from __future__ import annotations

from random import choice
from typing import List


# Internal game state
_word_list: List[str] | None = None
_current_word: str | None = None
_guessed_chars: List[str] = []
_wrong_guesses: int = 0
_word_display: List[str] = []


HANGMAN_STAGES = [
    """
    ┌─────
    │
    │
    │
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │
    │
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │    │
    │
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │   ┌│
    │
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │   ┌│┐
    │
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │   ┌│┐
    │   ┌┘
    │
    └─────
    """,
    """
    ┌─────
    │    O
    │   ┌│┐
    │   ┌┘┐
    │
    └─────
    """
]


def get_word() -> str | None:
    global _current_word
    return _current_word

def set_dictionary(dictionary: List[str]) -> None:
    global _word_list, _current_word, _guessed_chars, _wrong_guesses, _word_display
    _word_list = dictionary
    _initialize_game()


def _initialize_game():
    global _current_word, _guessed_chars, _wrong_guesses, _word_display
    _current_word = choice(_word_list)
    _guessed_chars = []
    _wrong_guesses = 0
    _word_display = ['_'] * len(_current_word)


def hangman(s: str) -> str | None:
    global _wrong_guesses, _guessed_chars, _word_display
    if not _word_list or not _current_word:
        raise ValueError("No dictionary set")

    if s in _guessed_chars:
        return None  # No update if the character was already guessed

    _guessed_chars.append(s)

    if s in _current_word:
        for idx, char in enumerate(_current_word):
            if char == s:
                _word_display[idx] = s
    else:
        _wrong_guesses += 1

    if _wrong_guesses >= 6:
        _initialize_game()
        return "loss"

    if "".join(_word_display) == _current_word:
        _initialize_game()
        return "win"

    return None


def _display_wrong_guesses() -> str:
    return " ".join(sorted(list(set(_guessed_chars) - set(_current_word))))


def get_state() -> str:
    return f"{_display_wrong_guesses()}\n{HANGMAN_STAGES[_wrong_guesses]}\n{' '.join(_word_display)}"


if __name__ == "__main__":
    # Win scenario
    set_dictionary(["apple"])
    print(get_state())
    hangman('a')
    print(get_state())
    hangman('p')
    print(get_state())
    hangman('l')
    print(get_state())
    res = hangman('e')
    print(res)

    # Lose scenario
    set_dictionary(["slap"])
    print(get_state())
    hangman('s')
    print(get_state())
    hangman('s')
    print(get_state())
    hangman('l')
    print(get_state())
    hangman('q')
    print(get_state())
    hangman('w')
    print(get_state())
    hangman('e')
    print(get_state())
    hangman('r')
    print(get_state())
    hangman('t')
    print(get_state())
    hangman('y')
    print(get_state())
    res = hangman('u')
    print(res)
