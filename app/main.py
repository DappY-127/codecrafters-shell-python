import sys
import os
import subprocess


def find_cmd_path(cmd):
    PATH = os.environ.get("PATH")
    paths = PATH.split(":")
    cmd_path = None
    for path in paths:
        full_path = os.path.join(path, cmd)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def change_dir(path):
    if path == "~":
        path = os.environ.get("HOME")
    try:
        os.chdir(path)
    except FileNotFoundError:
        print(f"cd: {path}: No such file or directory")

def parse_command(command):
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
                char == "2" and i + 1 < len(command) and command[i + 1] in [">", ">"]
            )
            is_stdout = char == ">" or (
                char == "1" and i + 1 < len(command) and command[i + 1] in [">", ">"]
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
                    if (
                        command[i].isspace()
                        and not in_single_quote
                        and not in_double_quote
                    ):
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

        if (
            char == "\\"
            and not in_single_quote
            and not in_double_quote
            and i + 1 < len(command)
        ):
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

def main():
    builtin_commands = ["echo", "exit", "type", "pwd", "cd"]
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command = input()
            args, redirect_out, redirect_err, append_out, append_err = parse_command(
                command
            )

            if not args:
                continue

            # Get original stdout/stderr
            old_stdout = sys.stdout
            old_stderr = sys.stderr
            output_file = None
            error_file = None
            try:
                if redirect_out:
                    try:
                        os.makedirs(os.path.dirname(redirect_out), exist_ok=True)
                        output_file = open(redirect_out, "a" if append_out else "w")
                        sys.stdout = output_file
                    except OSError as e:
                        print(f"Error opening {redirect_out}", file=old_stderr)
                        continue
                if redirect_err:
                    try:
                        os.makedirs(os.path.dirname(redirect_err), exist_ok=True)
                        error_file = open(redirect_err, "a" if append_err else "w")
                        sys.stderr = error_file
                    except OSError as e:
                        print(f"Error opening {redirect_err}", file=old_stderr)
                        continue

                # Command execution
                if args[0] == "exit":
                    if len(args) > 1 and args[1] == "0":
                        break
                    else:
                        print("exit: missing or invalid argument", file=old_stderr)
                elif args[0] == "echo":
                    message = " ".join(args[1:]) if len(args) > 1 else ""
                    print(message, file=sys.stdout if not redirect_err else old_stdout)
                elif args[0] == "type":
                    cmd_path = find_cmd_path(args[1]) if len(args) > 1 else None
                    if len(args) > 1:
                        if args[1] in builtin_commands:
                            print(
                                f"{args[1]} is a shell builtin",
                                file=sys.stdout if not redirect_err else old_stdout,
                            )
                        elif cmd_path:
                            print(
                                f"{args[1]} is {cmd_path}",
                                file=sys.stdout if not redirect_err else old_stdout,
                            )
                        else:
                            print(f"{args[1]}: not found", file=sys.stderr)
                    else:
                        print("type: missing argument", file=sys.stderr)
                elif args[0] == "cd":
                    if len(args) > 1:
                        change_dir(args[1])

                elif args[0] == "pwd":
                    print(
                        os.getcwd(), file=sys.stdout if not redirect_err else old_stdout

                    )

                elif args[0] == "cat":
                    if len(args) > 1:
                        try:
                            for i, file_path in enumerate(args[1:]):
                                try:
                                    with open(file_path, "r") as file:
                                        content = file.read()
                                        # Write content without adding extra newlines
                                        sys.stdout.write(content)
                                except FileNotFoundError:
                                    print(
                                        f"cat: {file_path}: No such file or directory",
                                        file=sys.stderr,
                                    )
                        except Exception as e:
                            print(f"cat: error: {e}", file=sys.stderr)
                    else:
                        print("cat: missing operand", file=sys.stderr)
                else:
                    cmd_path = find_cmd_path(args[0])
                    if cmd_path:
                        try:
                            result = subprocess.run(
                                [cmd_path] + args[1:],
                                text=True,
                                stdout=sys.stdout if not redirect_err else old_stdout,
                                stderr=sys.stderr,
                            )

                        except FileNotFoundError:
                            print(f"{args[0]}: command not found", file=sys.stderr)

                        except PermissionError:
                            print(f"{args[0]}: Permission denied", file=sys.stderr)
                    else:
                        print(f"{args[0]}: command not found", file=sys.stderr)
            finally:
                # Restore stdout/stderr and close files
                if redirect_out:
                    sys.stdout = old_stdout
                    if output_file:
                        output_file.close()
                if redirect_err:
                    sys.stderr = old_stderr
                    if error_file:
                        error_file.close()
        except EOFError:
            break

        except KeyboardInterrupt:
            print()
            continue

if __name__ == "__main__":
    main()