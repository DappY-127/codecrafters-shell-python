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
            return full_path
    return None

def parse_command_and_args(raw_args):
    args = shlex.split(raw_args)
    command = args[0] if args else ""
    output_file, error_file = None, None
    append_stdout, append_stderr = False, False

    processed_args = []
    skip_next = False

    for i, arg in enumerate(args):
        if skip_next:
            skip_next = False
            continue

        if arg in {"1>>", ">>"}:
            if i + 1 < len(args):
                output_file = args[i + 1]
                append_stdout = True
                skip_next = True
        elif arg in {"1>", ">"}:
            if i + 1 < len(args):
                output_file = args[i + 1]
                skip_next = True
        elif arg == "2>>":
            if i + 1 < len(args):
                error_file = args[i + 1]
                append_stderr = True
                skip_next = True
        elif arg == "2>":
            if i + 1 < len(args):
                error_file = args[i + 1]
                skip_next = True
        else:
            processed_args.append(arg)

    return processed_args[0] if processed_args else "", processed_args[1:], output_file, error_file, append_stdout, append_stderr

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
    if executable_path:
        try:
            stdout_target = open(output_file, "a" if append_stdout else "w") if output_file else None
            stderr_target = open(error_file, "a" if append_stderr else "w") if error_file else None

            process = subprocess.Popen(
                [executable_path] + args,
                stdout=stdout_target if output_file else subprocess.PIPE,
                stderr=stderr_target if error_file else subprocess.PIPE,
                text=True
            )

            stdout_data, stderr_data = process.communicate()

            if stdout_data:
                if stdout_target: 
                    stdout_target.write(stdout_data)
                else:  
                    sys.stdout.write(stdout_data)

            if stderr_data:
                if stderr_target:  
                    stderr_target.write(stderr_data)
                else:  
                    sys.stderr.write(stderr_data)

        except FileNotFoundError:
            sys.stderr.write(f"{command}: command not found\n")
        except Exception as e:
            sys.stderr.write(f"Error executing {command}: {e}\n")
        finally:
            if stdout_target:
                stdout_target.close()
            if stderr_target:
                stderr_target.close()

    else:
        sys.stderr.write(f"{command}: command not found\n")

def write_output(output, output_file, append_mode):
    mode = "a" if append_mode else "w"
    
    if output_file:
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir)
            except Exception as e:
                sys.stderr.write(f"Error creating directory {output_dir}: {e}\n")
                return  # Stop further processing if directory cannot be created

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
