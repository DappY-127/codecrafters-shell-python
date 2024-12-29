import sys
import os
import subprocess

def find_cmd_path(cmd):
    """Find the full path of a command in the system's PATH."""
    PATH = os.environ.get("PATH")
    paths = PATH.split(":")
    for path in paths:
        full_path = os.path.join(path, cmd)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def change_dir(path):
    """Change the current working directory."""
    if path == "~":
        path = os.environ.get("HOME")
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")

def parse_command(command):
    """Parse a command string into arguments and redirection information."""
    args = []
    current_arg = []
    in_single_quote = False
    in_double_quote = False
    redirect_out = None
    redirect_err = None
    append_out = False
    append_err = False
    i = 0
    while i < len(command):
        char = command[i]
        if not in_single_quote and not in_double_quote:
            is_stderr = (
                char == "2" and i + 1 < len(command) and command[i + 1] in [">", ">>"]
            )
            is_stdout = char == ">" or (
                char == "1" and i + 1 < len(command) and command[i + 1] in [">", ">>"]
            )
            if is_stderr or is_stdout:
                if current_arg:
                    args.append("".join(current_arg))
                    current_arg = []
                if char in ["1", "2"]:
                    i += 1
                is_append = (
                    i + 1 < len(command) and command[i] == ">" and command[i + 1] == ">"
                )
                if is_append:
                    i += 2
                    if is_stderr:
                        append_err = True
                    else:
                        append_out = True
                else:
                    i += 1
                while i < len(command) and command[i].isspace():
                    i += 1
                while i < len(command):
                    if command[i].isspace() and not in_single_quote and not in_double_quote:
                        break
                    if command[i] == '"' and not in_single_quote:
                        in_double_quote = not in_double_quote
                    elif command[i] == "'" and not in_double_quote:
                        in_single_quote = not in_single_quote
                    else:
                        current_arg.append(command[i])
                    i += 1
                if is_stderr:
                    redirect_err = "".join(current_arg)
                else:
                    redirect_out = "".join(current_arg)
                current_arg = []
                continue
        if char == "\\" and not in_single_quote and not in_double_quote and i + 1 < len(command):
            next_char = command[i + 1]
            current_arg.append(next_char)
            i += 2
            continue
        if char == "'":
            if not in_double_quote:
                in_single_quote = not in_single_quote
            else:
                current_arg.append(char)
        elif char == '"':
            if not in_single_quote:
                in_double_quote = not in_double_quote
            else:
                current_arg.append(char)
        elif char == "\\" and in_double_quote and i + 1 < len(command):
            next_char = command[i + 1]
            if next_char in ['"', "\\", "$", "\n"]:
                current_arg.append(next_char)
                i += 1
            else:
                current_arg.append(char)
        elif char.isspace() and not in_single_quote and not in_double_quote:
            if current_arg:
                args.append("".join(current_arg))
                current_arg = []
        else:
            current_arg.append(char)
        i += 1
    if current_arg:
        args.append("".join(current_arg))
    return args, redirect_out, redirect_err, append_out, append_err

def execute_builtin_command(args, builtin_commands):
    """Handle execution of built-in commands."""
    if args[0] == "exit":
        if len(args) > 1 and args[1] == "0":
            return True
        else:
            print("exit: missing or invalid argument", file=sys.stderr)

    elif args[0] == "echo":
        message = " ".join(args[1:]) if len(args) > 1 else ""
        print(message)

    elif args[0] == "type":
        cmd_path = find_cmd_path(args[1]) if len(args) > 1 else None
        if len(args) > 1:
            if args[1] in builtin_commands:
                print(f"{args[1]} is a shell builtin")
            elif cmd_path:
                print(f"{args[1]} is {cmd_path}")
            else:
                print(f"{args[1]}: not found", file=sys.stderr)
        else:
            print("type: missing argument", file=sys.stderr)

    elif args[0] == "cd":
        if len(args) > 1:
            change_dir(args[1])

    elif args[0] == "pwd":
        print(os.getcwd())

    elif args[0] == "cat":
        if len(args) > 1:
            for file_path in args[1:]:
                try:
                    with open(file_path, "r") as file:
                        sys.stdout.write(file.read())
                except FileNotFoundError:
                    print(f"cat: {file_path}: No such file or directory", file=sys.stderr)
        else:
            print("cat: missing operand", file=sys.stderr)

    return False

def execute_external_command(args):
    """Execute an external command."""
    cmd_path = find_cmd_path(args[0])
    if cmd_path:
        try:
            subprocess.run([cmd_path] + args[1:], text=True)
        except FileNotFoundError:
            print(f"{args[0]}: command not found", file=sys.stderr)
        except PermissionError:
            print(f"{args[0]}: Permission denied", file=sys.stderr)
    else:
        print(f"{args[0]}: command not found", file=sys.stderr)

def setup_redirection(redirect_out, redirect_err, append_out, append_err):
    """Set up redirection for stdout and stderr."""
    old_stdout, old_stderr = sys.stdout, sys.stderr
    output_file, error_file = None, None

    try:
        if redirect_out:
            mode = "a" if append_out else "w"
            output_file = open(redirect_out, mode)
            sys.stdout = output_file
        if redirect_err:
            mode = "a" if append_err else "w"
            error_file = open(redirect_err, mode)
            sys.stderr = error_file
    except OSError as e:
        print(f"Error opening file for redirection: {e}", file=old_stderr)
        cleanup_redirection(old_stdout, old_stderr, output_file, error_file)

    return old_stdout, old_stderr, output_file, error_file

def cleanup_redirection(old_stdout, old_stderr, output_file, error_file):
    """Restore stdout and stderr and close any open files."""
    sys.stdout = old_stdout
    sys.stderr = old_stderr
    if output_file:
        output_file.close()
    if error_file:
        error_file.close()

def main():
    builtin_commands = ["echo", "exit", "type", "pwd", "cd"]

    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command = input()

            args, redirect_out, redirect_err, append_out, append_err = parse_command(command)
            if not args:
                continue

            old_stdout, old_stderr, output_file, error_file = setup_redirection(
                redirect_out, redirect_err, append_out, append_err
            )

            try:
                if args[0] in builtin_commands:
                    exit_shell = execute_builtin_command(args, builtin_commands)
                    if exit_shell:
                        break
                else:
                    execute_external_command(args)
            finally:
                cleanup_redirection(old_stdout, old_stderr, output_file, error_file)

        except EOFError:
            break
        except KeyboardInterrupt:
            print()
            continue

if __name__ == "__main__":
    main()
