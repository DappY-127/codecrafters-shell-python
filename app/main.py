import sys


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

            if command:
                print(f"{command}: command not found")
        except (KeyboardInterrupt, EOFError):
            print("\nExiting...")
            sys.exit(0)


if __name__ == "__main__":
    main()
