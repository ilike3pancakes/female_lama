"""
Custom triggers
===============

Creating custom triggers
------------------------

when a user...

wettest trigger\n
(.*)

then...

create_trigger($1) -> Result<Trigger>


Evaluating custom triggers
--------------------------

when a user...

(.*)

then...

all_triggers.each do trigger.match($1) as result and then yield result


Example
-------

When a user...

Wettest trigger
sassy
word -> word word " 👏" concat word terminal if

then...

Aight ☝️

WHen a user...

sassy hello world foobar

then...

hello 👏 world 👏 foobar


Example
-------

When a user...

Wettest trigger
mock
char -> char lower char upper randbit 0 = if

then...

Aight ☝️

When a user...

mock dms open ladies

then...

dMs oPEN LaDieS


Example
-------

When a user...

Wettest trigger

sentence -> nothing "aight let's see that ass" sentence "lmao" contains if

then...

Aight ☝️

When a user...

Any sentence that contains "lmao"

then...

aight let's see that ass
"""
from __future__ import annotations

from dataclasses import dataclass
import re
import random
import logging
from typing import Callable, List, Union, Generator, Optional

from persistence import PersistenceMixin

logger = logging.getLogger()


@dataclass
class TriggerSpec:
    associated_jid: str
    trigger_spec: str
    prefix: str


@dataclass
class TriggerSpecs(PersistenceMixin):
    specs: List[TriggerSpec]

    def __post_init__(self):
        if self.specs and isinstance(self.specs[0], dict):
            self.specs = [TriggerSpec(**fields) for fields in self.specs]

    @staticmethod
    def default_ctor() -> "TriggerSpecs":
        print("Creating empty trigger_specs.yaml")
        return TriggerSpecs(specs=[])

    def insert(self, associated_jid: str, *, trigger: "Trigger"):
        logger.info("Inserting...")
        new_spec = TriggerSpec(associated_jid=associated_jid, trigger_spec=trigger.description, prefix=trigger.prefix)
        self.specs = [
            new_spec if spec.associated_jid == associated_jid and spec.prefix == trigger.prefix else spec
            for spec in self.specs
        ]

        logger.info("Checking existing specs")

        if not any(spec.associated_jid == associated_jid and spec.prefix == trigger.prefix for spec in self.specs):
            self.specs.append(new_spec)
        logger.info("Done inserting.")


def tokenize(description: str) -> List[str]:
    return description.split()

class Trigger:
    def __init__(self, description: str):
        self.description = description
        self.prefix = description.split('\n')[0].strip()
        self.operation: Optional[str] = None  # Could be "word", "char", "sentence"
        self.logic: Optional[Callable[[List[str | bool | None], str, bool], None]] = None  # The function to apply
        self.parse_description(description)

    def parse_description(self, description: str):
        description = "\n".join(description.split('\n')[1:])
        parts = description.split('->')
        if len(parts) != 2:
            raise ValueError('Invalid description')

        operation = parts[0].strip()
        if operation not in {"word", "char", "sentence"}:
            raise ValueError(f"operation should be word, char, or sentence, but was {operation}")

        assert operation in {"word", "char", "sentence"}

        self.operation = operation
        code = parts[1]

        # The code should define a Forth-like stack operation
        self.logic = self.compile_logic(code.strip())

    def compile_logic(self, code: str) -> Callable:
        tokens = re.findall(r'".+?"|\S+', code)

        def forth_logic(stack: List[str | bool | None], word: str, terminal: bool):
            for token in tokens:
                if token == "if":
                    condition = stack.pop()
                    false_value = stack.pop()
                    true_value = stack.pop()
                    stack.append(true_value if condition else false_value)
                elif token == "concat":
                    right = stack.pop()
                    left = stack.pop()
                    stack.append(str(left) + str(right))
                elif token == "word":
                    stack.append(word)
                elif token == "char":
                    stack.append(word)
                elif token == "sentence":
                    stack.append(word)
                elif token == "terminal":
                    stack.append(terminal)
                elif token == "contains":
                    needle = stack.pop()
                    haystack = stack.pop()
                    stack.append(str(needle) in str(haystack))
                elif token == "randbit":
                    stack.append(random.choice([True, False]))
                elif token == "upper":
                    to_change = stack.pop()
                    stack.append(str(to_change).upper())
                elif token == "lower":
                    to_change = stack.pop()
                    stack.append(str(to_change).lower())
                elif token == "nothing":
                    stack.append(None)
                elif len(token) > 1 and token[0] == '"' and token[-1] == '"':
                    # Quoted string literals
                    stack.append(token[1:-1])
                else:
                    stack.append(token)  # literals, etc.

        return forth_logic

    def match(self, input_str: str) -> Optional[str]:
        logger.info(f"Matching {input_str} against {self.prefix}")
        if not input_str.startswith(f"{self.prefix} "):
            return None
        logger.info("Input matched!")

        input_str = self.prefix.join(input_str.split(self.prefix)[1:]) if self.prefix else input_str

        if self.operation == "word":
            words = input_str.split()
            transformed_words = [self.transform_word(word, idx + 1 == len(words)) for idx, word in enumerate(words)]
            return ' '.join([str(word) for word in transformed_words if word])
        elif self.operation == "char":
            transformed_chars = [self.transform_char(c, idx + 1 == len(input_str)) for idx, c in enumerate(input_str)]
            return ''.join([str(char) for char in transformed_chars if char])
        elif self.operation == "sentence":
            sentences = input_str.splitlines()
            transformed_sentences = [
                self.transform_sentence(s, idx + 1 == len(sentences)) for idx, s in enumerate(sentences)
            ]
            return '\n'.join([str(sentence) for sentence in transformed_sentences if sentence])
        return None

    def transform_word(self, word: str, terminal: bool) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, word, terminal)
        return stack[-1]  # We assume the final result is at the top of the stack

    def transform_char(self, char: str, terminal: bool) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, char, terminal)
        return stack[-1]

    def transform_sentence(self, sentence: str, terminal: bool) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, sentence, terminal)
        return stack[-1]


class Result:
    def __init__(self, success: bool, value: Union[None, 'Trigger']):
        self.success = success
        self.value = value


def create_trigger(description: str) -> Result:
    try:
        new_trigger = Trigger(description)
        return Result(True, new_trigger)
    except Exception as e:
        print(f"Failed to create trigger: {e}")
        return Result(False, None)


def evaluate_all_triggers(input_str: str, all_triggers: List[Trigger]) -> Generator[str, None, None]:
    for trigger in all_triggers:
        result = trigger.match(input_str)
        if result:
            yield result


sassy_spec = """
sassy
word -> word word " 👏" concat terminal if
""".strip()

lmao_spec = """.

sentence -> "aight let's see that ass" nothing sentence "lmao" contains if
""".strip()[1:]

mock_spec = """
mock
char -> char lower char upper randbit if
""".strip()

angry_spec = """
angry
char -> char upper "!!    😠" concat char upper terminal if
""".strip()

if __name__ == "__main__":
    trigger1 = create_trigger(sassy_spec)
    assert trigger1.value, f"{trigger1.success} {trigger1.value}"

    trigger2 = create_trigger(lmao_spec)
    assert trigger2.value, f"{trigger2.success} {trigger2.value}"

    trigger3 = create_trigger(mock_spec)
    assert trigger3.value, f"{trigger3.success} {trigger3.value}"

    trigger4 = create_trigger(angry_spec)
    assert trigger4.value, f"{trigger4.success} {trigger4.value}"

    triggers = [trigger1.value, trigger2.value, trigger3.value, trigger4.value]

    for result in evaluate_all_triggers("sassy hello world foobar", triggers):
        print(result)
    for result in evaluate_all_triggers("haha lmao hello world foobar", triggers):
        print(result)
    for result in evaluate_all_triggers("mock hello world", triggers):
        print(result)
    for result in evaluate_all_triggers("an ignored input example", triggers):
        print(result)
    for result in evaluate_all_triggers("angry hello world", triggers):
        print(result)
