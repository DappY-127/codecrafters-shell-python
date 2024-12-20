import sys


BUILTIN_COMMANDS = {"exit", "echo", "type"}

def main():
    while True:
        try:
            sys.stdout.write("$ ")
            sys.stdout.flush()
            command = input().strip()

            if command.startswith('exit'):
                command, _, status_code = command.partition(" ")
                status_code = status_code.strip()
                if status_code.isdigit():
                    sys.exit(int(status_code))
                else:
                    print("exit: numeric argument required")
                    sys.exit(0)

            elif command.startswith('echo'):
                command, _, message = command.partition(" ")
                print(message)

            elif command.startswith('type'):
                command, _, command_name = command.partition(" ")
                if not command_name.strip():
                    print("type: argument required")
                    break

                for command_name in command_name.split():
                    if command_name in BUILTIN_COMMANDS:
                        print(f'{command_name} is a shell builtin')
                    else:
                        print(f'{command_name}: not found')

            else:
                print(f"{command}: command not found")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
