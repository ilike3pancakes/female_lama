
from sh import bash


def candidate() -> str:
    """
    Returns a random american english dictionary word, capitalised.
    """

    return bash("-c", """cat /usr/share/dict/american-english | shuf | grep -v "'s" | head -n 1""").capitalize()


if __name__ == "__main__":
    print(candidate())
