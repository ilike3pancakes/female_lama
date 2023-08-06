
import subprocess


def candidate() -> str:
    """
    Returns a random american english dictionary word, capitalised.
    """
    command = """cat /usr/share/dict/american-english | shuf | grep -v "'s" | head -n 1"""
    result = subprocess.run(['/bin/bash', '-c', command], capture_output=True, text=True)

    return result.stdout.capitalize()


if __name__ == "__main__":
    print(candidate())
