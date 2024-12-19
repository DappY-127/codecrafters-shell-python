import sys

command_history = []

def main():
    while True:
        sys.stdout.write("$ ")
        sys.stdout.flush()
        command = input()
        command_history.append(command)

        if not command.strip():
            continue
        
        print(f"{command}: command not found\n")


if __name__ == "__main__":
    main()
