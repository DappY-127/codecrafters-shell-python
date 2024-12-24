import sys
import os
import subprocess
import shlex
import re


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
    return command, args[1:]

def handle_command(command, args):
    if command == "exit":
        execute_exit(args)
    elif command == "echo":
        execute_echo(args)
    elif command == "pwd":
        execute_pwd()
    elif command == "cd":
        execute_cd(args)
    elif command == "type":
        execute_type(args)
    else:
        execute_external_program(command, args)

def execute_exit(command):
    status_code = int(command[0]) if command and command[0].isdigit() else 0
    sys.exit(status_code)

def execute_type(command):
    if not command:
        sys.stdout.write("type: argument required\n")
        return

    for name in command:
        if name in BUILTIN_COMMANDS:
            sys.stdout.write(f"{name} is a shell builtin\n")
        else:
            path = check_path(name)
            if path:
                sys.stdout.write(f"{name} is {path}\n")
            else:
                sys.stdout.write(f"{name}: not found\n")

def execute_echo(command):
    sys.stdout.write(f"{' '.join(command)}\n")

def execute_external_program(command, args):
    executable_path = check_path(command)

    if executable_path:
        try:
            result = subprocess.run([executable_path, *args], capture_output=True, text=True)
            sys.stdout.write(result.stdout)
        except subprocess.CalledProcessError as e:
            sys.stdout.write(e.stderr)
    else:
        sys.stdout.write(f"{command}: command not found\n")

def execute_pwd():
    sys.stdout.write(f"{os.getcwd()}")

def execute_cd(command):
    command, _, directory = command.partition(" ")
    directory = directory.strip()
    if not directory:
        print(f"{command}: argument required")
        return
    
    if directory.startswith("~"):
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
            raw_command = input().strip()
            if not raw_command:
                continue

            command, args = parse_command_and_args(raw_command)
            handle_command(command, args)
            
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
