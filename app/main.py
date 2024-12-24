import sys
import os
import subprocess
import shlex


BUILTIN_COMMANDS = {"exit", "echo", "type", "pwd", "cd"}

def check_path(command_name):
    paths = os.getenv("PATH", "").split(":")
    for path in paths:
        full_path = os.path.join(path, command_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def parse_command_and_args(raw_args):
    args = shlex.split(raw_args)
    command = args[0] if args else ""
    redirect_stdout = None
    redirect_stderr = None

    if ">" in args or "1>" in args or "2>" in args:
        i = 0
        while i < len(args):
            if args[i] in {">", "1>"}:
                if i + 1 < len(args):
                    redirect_stdout = args[i + 1]
                    del args[i:i + 2]
                else:
                    break
            elif args[i] == "2>":
                if i + 1 < len(args):
                    redirect_stderr = args[i + 1]
                    del args[i:i + 2]
                else:
                    break
            else:
                i += 1

    return command, args[1:], redirect_stdout, redirect_stderr

def handle_command(command, args, redirect_stdout, redirect_stderr):
    if command == "exit":
        execute_exit(args)
    elif command == "echo":
        execute_echo(args, redirect_stdout, redirect_stderr)
    elif command == "pwd":
        execute_pwd(redirect_stdout, redirect_stderr)
    elif command == "cd":
        execute_cd(args)
    elif command == "type":
        execute_type(args, redirect_stdout, redirect_stderr)
    else:
        execute_external_program(command, args, redirect_stdout, redirect_stderr)

def write_output(output, redirect_stdout, redirect_stderr):
    if redirect_stdout:
        try:
            with open(redirect_stdout, "a") as file:
                file.write(output)
        except IOError as e:
            sys.stdout.write(f"Error writing to file {redirect_stdout}: {e}\n")
    elif redirect_stderr:
        try:
            with open(redirect_stderr, "a") as file:
                file.write(output)
        except IOError as e:
            sys.stdout.write(f"Error writing to file {redirect_stderr}: {e}\n")
    else:
        sys.stdout.write(output)

def execute_exit(command):
    status_code = int(command[0]) if command and command[0].isdigit() else 0
    sys.exit(status_code)

def execute_type(command, redirect_stdout=None, redirect_stderr=None):
    output = []
    if not command:
        output.append("type: argument required\n")
    else:
        for name in command:
            if name in BUILTIN_COMMANDS:
                output.append(f"{name} is a shell builtin\n")
            else:
                path = check_path(name)
                if path:
                    output.append(f"{name} is {path}\n")
                else:
                    output.append(f"{name}: not found\n")

    write_output("".join(output), redirect_stdout, redirect_stderr)

def execute_echo(command, redirect_stdout=None, redirect_stderr=None):
    sys.stdout.write(f"{' '.join(command)}\n", redirect_stdout, redirect_stderr)

def execute_external_program(command, args, redirect_stdout, redirect_stderr):
    executable_path = check_path(command)

    if executable_path:
        try:
            with subprocess.Popen(
                [executable_path, *args],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            ) as proc:
                stdout, stderr = proc.communicate()
                write_output(stdout, redirect_stdout, None)
                write_output(stderr, None, redirect_stderr)
        except FileNotFoundError:
            sys.stdout.write(f"{command}: command not found\n")
        except subprocess.CalledProcessError as e:
            write_output("", None, redirect_stderr)
    else:
        sys.stdout.write(f"{command}: command not found\n")

def execute_pwd(redirect_stdout=None, redirect_stderr=None):
    sys.stdout.write(f"{os.getcwd()}\n", redirect_stdout, redirect_stderr)

def execute_cd(args):
    if not args:
        sys.stdout.write("cd: argument required\n")
        return

    directory = args[0]
    if directory.startswith("~"):
        directory = os.path.expanduser(directory)

    try:
        os.chdir(directory)
    except FileNotFoundError:
        sys.stdout.write(f"cd: {directory}: No such file or directory\n")
    except PermissionError:
        sys.stdout.write(f"cd: {directory}: Permission denied\n")

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            raw_command = input().strip()
            if not raw_command:
                continue

            command, args, redirect_stdout, redirect_stderr = parse_command_and_args(raw_command)
            handle_command(command, args, redirect_stdout, redirect_stderr)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
