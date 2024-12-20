import sys
import os


BUILTIN_COMMANDS = {"exit", "echo", "type"}

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

            else:
                print(f"{command}: command not found")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
