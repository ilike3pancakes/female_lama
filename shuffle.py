
import subprocess


def candidate() -> str:
    """
    Returns a random american english dictionary word, capitalised.
    """
    command = """cat /usr/share/dict/american-english | shuf | grep -v "'s" | head -n 1"""
    result = subprocess.run(['/bin/bash', '-c', command], capture_output=True, text=True)

    word = result.stdout.capitalize()

    print(f"Returning {word}")

    return word


if __name__ == "__main__":
    print(candidate())
