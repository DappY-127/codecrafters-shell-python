import sys
import os
import subprocess


BUILTIN_COMMANDS = {"exit", "echo", "type", "pwd", "cd"}

def check_path(command_name):
    paths = os.getenv("PATH", "").split(":")
    for path in paths:
        full_path = os.path.join(path, command_name)
        if os.path.isfile(full_path) and os.access(full_path, os.X_OK):
            return full_path
    return None

def execute_exit(command):
    command, _, status_code = command.partition(" ")
    status_code = status_code.strip()
    if status_code.isdigit():
        sys.exit(int(status_code))
    else:
        print("exit: numeric argument required")
        sys.exit(1)

def execute_type(command):
    command, _, command_name = command.partition(" ")
    if not command_name.strip():
        print("type: argument required")
        return

    for name in command_name.split():
        if name in BUILTIN_COMMANDS:
            print(f'{name} is a shell builtin')
        else:
            execution_path = check_path(name)
            if execution_path:
                print(f'{name} is {execution_path}')
            else:
                print(f'{name}: not found')

def execute_echo(command):
    command, _, message = command.partition(" ")
    print(message)

def execute_external_program(command):
    args = command.split()
    program = args[0]
    executable_path = check_path(program)

    if executable_path:
        try:
            result = subprocess.run(args, check=True, text=True, capture_output=True)
            print(result.stdout, end='')
        except subprocess.CalledProcessError as e:
            print(e.stderr, end='')
    
    else:
        print(f"{program}: command not found")

def execute_pwd():
    working_directory = os.getcwd()
    print(working_directory)

def execute_cd(command):
    command, _, directory = command.partition(" ")
    directory = directory.strip()
    if not directory:
        print(f"{command}: argument required")
        return
    
    if directory.startwith("~"):
        home_dir = os.getenv("HOME")
        if not home_dir:
            print(f"{command}: HOME environment variable is not set")
            return
        directory = directory.replace("~", home_dir, 1)

    if os.path.isabs(directory):
        new_path = directory
    else:
        new_path = os.path.join(os.getcwd(), directory)

    if os.path.isdir(directory):
        try:
            os.chdir(directory)
        except PermissionError:
            print(f"{command}: {directory}: Permission denied")
    else:
        print(f'{command}: {directory}: No such file or directory')

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command = input().strip()

            if command.startswith('exit'):
                execute_exit(command=command)

            elif command.startswith('echo'):
                execute_echo(command=command)

            elif command.startswith('type'):
                execute_type(command=command)

            elif command.startswith('pwd'):
                execute_pwd()

            elif command.startswith('cd'):
                execute_cd(command=command)

            else:
                execute_external_program(command=command)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
