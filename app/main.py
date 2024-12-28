import sys
import os
import subprocess
import shlex

BUILTIN_COMMANDS = {"exit", "echo", "type", "pwd", "cd"}

def check_path(command_name):
    if os.path.isabs(command_name) and os.access(command_name, os.X_OK):
        return command_name

    paths = os.getenv("PATH", "").split(":")
    for path in paths:
        full_path = os.path.join(path, command_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            print(f"[DEBUG] Found path: {full_path}", file=sys.stderr)  # simple logs
            return full_path
    return None

def parse_command_and_args(raw_args):
    args = shlex.split(raw_args)
    print(f"[DEBUG] Parsed args: {args}", file=sys.stderr)  # simple logs, remove later
    command = args[0] if args else ""
    output_file, error_file = None, None
    append_stdout, append_stderr = False, False

    if ">>" in args:
        redirect_index = args.index(">>")
        output_file = args[redirect_index + 1]
        append_stdout = True
        args = args[:redirect_index] + args[redirect_index + 2:]

    elif ">" in args:
        redirect_index = args.index(">")
        output_file = args[redirect_index + 1]
        args = args[:redirect_index] + args[redirect_index + 2:]

    if "2>>" in args:
        redirect_index = args.index("2>>")
        error_file = args[redirect_index + 1]
        append_stderr = True
        args = args[:redirect_index] + args[redirect_index + 2:]

    elif "2>" in args:
        redirect_index = args.index("2>")
        error_file = args[redirect_index + 1]
        args = args[:redirect_index] + args[redirect_index + 2:]

    return command, args, output_file, error_file, append_stdout, append_stderr

def handle_command(command, args, output_file, error_file, append_stdout, append_stderr):
    if command == "exit":
        execute_exit(args)
    elif command == "echo":
        execute_echo(args, output_file, error_file, append_stdout, append_stderr)
    elif command == "pwd":
        execute_pwd(output_file, error_file, append_stdout, append_stderr)
    elif command == "cd":
        execute_cd(args)
    elif command == "type":
        execute_type(args, output_file, error_file)
    else:
        execute_external_program(command, args, output_file, error_file, append_stdout, append_stderr)

def execute_exit(args):
    status_code = int(args[0]) if args and args[0].isdigit() else 0
    sys.exit(status_code)

def execute_echo(args, output_file, error_file, append_stdout, append_stderr):
    output = " ".join(args) + "\n"
    write_output(output, output_file, append_stdout)

def execute_type(args, output_file, error_file):
    output = []
    for name in args:
        if name in BUILTIN_COMMANDS:
            output.append(f"{name} is a shell builtin\n")
        else:
            path = check_path(name)
            if path:
                output.append(f"{name} is {path}\n")
            else:
                output.append(f"{name}: not found\n")
    write_output("".join(output), output_file, False)

def execute_pwd(output_file, error_file, append_stdout, append_stderr):
    output = f"{os.getcwd()}\n"
    write_output(output, output_file, append_stdout)

def execute_cd(args):
    if not args:
        sys.stderr.write("cd: argument required\n")
        return
    directory = args[0]
    if directory.startswith("~"):
        directory = os.path.expanduser(directory)
    try:
        os.chdir(directory)
    except FileNotFoundError:
        sys.stderr.write(f"cd: {directory}: No such file or directory\n")
    except PermissionError:
        sys.stderr.write(f"cd: {directory}: Permission denied\n")

def execute_external_program(command, args, output_file, error_file, append_stdout, append_stderr):
    executable_path = check_path(command)
    print(f"[DEBUG] Executable path: {executable_path}", file=sys.stderr)  # Logs
    if executable_path:
        try:
            stdout_target = open(output_file, "a" if append_stdout else "w") if output_file else subprocess.PIPE
            stderr_target = open(error_file, "a" if append_stderr else "w") if error_file else subprocess.PIPE

            result = subprocess.run(
                [executable_path] + args,
                stdout=stdout_target,
                stderr=stderr_target,
                text=True
            )

            if not output_file:
                sys.stdout.write(result.stdout or "")
            if not error_file:
                sys.stderr.write(result.stderr or "")

        except FileNotFoundError:
            sys.stderr.write(f"{command}: command not found\n")
        except Exception as e:
            sys.stderr.write(f"Error executing {command}: {e}\n")
        finally:
            if output_file:
                stdout_target.close()
            if error_file:
                stderr_target.close()
    else:
        sys.stderr.write(f"{command}: command not found\n")

def write_output(output, output_file, append_mode):
    mode = "a" if append_mode else "w"
    if output_file:
        try:
            with open(output_file, mode) as f:
                f.write(output)
        except IOError as e:
            sys.stderr.write(f"Error writing to file {output_file}: {e}\n")
    else:
        sys.stdout.write(output)

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            raw_command = input().strip()
            if not raw_command:
                continue

            command, args, output_file, error_file, append_stdout, append_stderr = parse_command_and_args(raw_command)
            handle_command(command, args, output_file, error_file, append_stdout, append_stderr)

        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)

if __name__ == "__main__":
    main()
