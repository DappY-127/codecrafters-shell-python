import sys
import os
import subprocess
import shlex

BUILTIN_COMMANDS = {"exit", "echo", "type", "pwd", "cd"}

def check_path(command_name):
    """Check if the command exists in the PATH."""
    for path in os.environ.get("PATH", "").split(":"):
        full_path = os.path.join(path, command_name)
        if os.path.exists(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def parse_command_and_args(raw_args):
    """Parse command into arguments and handle redirection operators."""
    args = []
    current_arg = []
    in_single_quote = False
    in_double_quote = False
    redirect_out = None
    redirect_err = None
    append_out = False
    append_err = False
    i = 0
    while i < len(raw_args):
        char = raw_args[i]
        # Handle redirection logic outside quotes
        if not in_single_quote and not in_double_quote:
            if char == ">" and i + 1 < len(raw_args) and raw_args[i + 1] == ">":
                append_out = True
                i += 2
                while i < len(raw_args) and raw_args[i].isspace():
                    i += 1
                redirect_out = raw_args[i:].strip()
                break
            elif char == ">" or (char == "1" and i + 1 < len(raw_args) and raw_args[i + 1] == ">"):
                i += 1
                while i < len(raw_args) and raw_args[i].isspace():
                    i += 1
                redirect_out = raw_args[i:].strip()
                break
            elif char == "2" and i + 1 < len(raw_args) and raw_args[i + 1] == ">":
                append_err = True
                i += 2
                while i < len(raw_args) and raw_args[i].isspace():
                    i += 1
                redirect_err = raw_args[i:].strip()
                break

        if char == "'":
            in_single_quote = not in_single_quote
        elif char == '"':
            in_double_quote = not in_double_quote
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

def handle_command(command, args, output_file, error_file, append_stdout, append_stderr):
    """Handle different types of commands."""
    if command == "exit":
        execute_exit(args)
    elif command == "echo":
        execute_echo(args, output_file, append_stdout)
    elif command == "pwd":
        execute_pwd(output_file, append_stdout)
    elif command == "cd":
        execute_cd(args)
    elif command == "type":
        execute_type(args, output_file, append_stdout)
    else:
        execute_external_program(command, args, output_file, error_file, append_stdout, append_stderr)

def execute_exit(args):
    """Handle the 'exit' command."""
    sys.exit(0)

def execute_echo(args, output_file, append_stdout):
    """Handle the 'echo' command."""
    output = " ".join(args) + "\n"
    write_output(output, output_file, append_stdout)

def execute_pwd(output_file, append_stdout):
    """Handle the 'pwd' command."""
    output = os.getcwd() + "\n"
    write_output(output, output_file, append_stdout)

def execute_cd(args):
    """Handle the 'cd' command."""
    if len(args) != 1:
        sys.stderr.write("cd: expected 1 argument\n")
        return
    try:
        os.chdir(args[0])
    except FileNotFoundError:
        sys.stderr.write(f"cd: {args[0]}: No such file or directory\n")
    except PermissionError:
        sys.stderr.write(f"cd: {args[0]}: Permission denied\n")

def execute_type(args, output_file, append_stdout):
    """Handle the 'type' command."""
    if len(args) > 1:
        cmd_path = check_path(args[1])
        if cmd_path:
            output = f"{args[1]} is {cmd_path}\n"
            write_output(output, output_file, append_stdout)
        else:
            sys.stderr.write(f"{args[1]}: command not found\n")

def execute_external_program(command, args, output_file, error_file, append_stdout, append_stderr):
    """Execute an external program."""
    cmd_path = check_path(command)
    if cmd_path:
        try:
            result = subprocess.run([cmd_path] + args, 
                                    stdout=output_file if not append_stdout else sys.stdout, 
                                    stderr=error_file if not append_stderr else sys.stderr, 
                                    text=True)
            if result.returncode != 0:
                sys.stderr.write(f"{command}: error executing command\n")
        except FileNotFoundError:
            sys.stderr.write(f"{command}: command not found\n")
        except PermissionError:
            sys.stderr.write(f"{command}: Permission denied\n")
    else:
        sys.stderr.write(f"{command}: command not found\n")

def write_output(output, output_file, append_mode):
    """Write output to the specified file or stdout."""
    mode = "a" if append_mode else "w"
    try:
        with open(output_file, mode) as f:
            f.write(output)
    except FileNotFoundError:
        sys.stderr.write(f"Error opening file {output_file}\n")

def main():
    """Main loop to accept and execute commands."""
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        try:
            raw_command = input()
        except EOFError:
            break

        # Parse the command and arguments
        args, redirect_out, redirect_err, append_out, append_err = parse_command_and_args(raw_command)

        if not args:
            continue
        
        command = args[0]
        output_file = redirect_out if redirect_out else None
        error_file = redirect_err if redirect_err else None
        
        handle_command(command, args[1:], output_file, error_file, append_out, append_err)

if __name__ == "__main__":
    main()
