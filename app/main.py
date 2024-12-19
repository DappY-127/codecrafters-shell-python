import sys

command_history = []

def main():
    while True:
        sys.stdout.write("$ ")
        command = input()
        command_history.append(command)
        print(f"{command}: command not found\n")


if __name__ == "__main__":
    main()
