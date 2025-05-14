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

dictionary_mappings = {
    "standard": "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ",
    "italic": "𝘢𝘣𝘤𝘥𝘦𝘧𝘨𝘩𝘪𝘫𝘬𝘭𝘮𝘯𝘰𝘱𝘲𝘳𝘴𝘵𝘶𝘷𝘸𝘹𝘺𝘻𝘈𝘉𝘊𝘋𝘌𝘍𝘎𝘏𝘐𝘑𝘒𝘓𝘔𝘕𝘖𝘗𝘘𝘙𝘚𝘛𝘜𝘝𝘞𝘟𝘠𝘡",
    "script": "𝒶𝒷𝒸𝒹𝑒𝒻𝑔𝒽𝒾𝒿𝓀𝓁𝓂𝓃𝑜𝓅𝓆𝓇𝓈𝓉𝓊𝓋𝓌𝓍𝓎𝓏𝒜𝐵𝒞𝒟𝐸𝐹𝒢𝐻𝐼𝒥𝒦𝐿𝑀𝒩𝒪𝒫𝒬𝑅𝒮𝒯𝒰𝒱𝒲𝒳𝒴𝒵",
    "cursive": "𝓪𝓫𝓬𝓭𝓮𝓯𝓰𝓱𝓲𝓳𝓴𝓵𝓶𝓷𝓸𝓹𝓺𝓻𝓼𝓽𝓾𝓿𝔀𝔁𝔂𝔃𝓐𝓑𝓒𝓓𝓔𝓕𝓖𝓗𝓘𝓙𝓚𝓛𝓜𝓝𝓞𝓟𝓠𝓡𝓢𝓣𝓤𝓥𝓦𝓧𝓨𝓩",
    "gothic": "𝔞𝔟𝔠𝔡𝔢𝔣𝔤𝔥𝔦𝔧𝔨𝔩𝔪𝔫𝔬𝔭𝔮𝔯𝔰𝔱𝔲𝔳𝔴𝔵𝔶𝔷𝔄𝔅ℭ𝔇𝔈𝔉𝔊ℌℑ𝔍𝔎𝔏𝔐𝔑𝔒𝔓𝔔ℜ𝔖𝔗𝔘𝔙𝔚𝔛𝔜ℨ",
    "gothicbold": "𝖆𝖇𝖈𝖉𝖊𝖋𝖌𝖍𝖎𝖏𝖐𝖑𝖒𝖓𝖔𝖕𝖖𝖗𝖘𝖙𝖚𝖛𝖜𝖝𝖞𝖟𝕬𝕭𝕮𝕯𝕰𝕱𝕲𝕳𝕴𝕵𝕶𝕷𝕸𝕹𝕺𝕻𝕼𝕽𝕾𝕿𝖀𝖁𝖂𝖃𝖄𝖅",
    "bb": "𝕒𝕓𝕔𝕕𝕖𝕗𝕘𝕙𝕚𝕛𝕜𝕝𝕞𝕟𝕠𝕡𝕢𝕣𝕤𝕥𝕦𝕧𝕨𝕩𝕪𝕫𝔸𝔹ℂ𝔻𝔼𝔽𝔾ℍ𝕀𝕁𝕂𝕃𝕄ℕ𝕆ℙℚℝ𝕊𝕋𝕌𝕍𝕎𝕏𝕐ℤ",
    "mono": "ａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺ",
    "blocks": "🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉🄰🄱🄲🄳🄴🄵🄶🄷🄸🄹🄺🄻🄼🄽🄾🄿🅀🅁🅂🅃🅄🅅🅆🅇🅈🅉",
}


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
        self.logic: Optional[Callable[[List[str | bool | None], str, bool, list[str], str], None]] = None  # The function to apply
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

        def forth_logic(stack: List[str | bool | None], word: str, terminal: bool, group_peers: list[str], self_: str):
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
                elif token == "fuckode":
                    fuck = stack.pop()
                    if len(fuck) > 2:
                        bogus = '\u200b\u200f'
                        fuckoded = f"{fuck[0]}{bogus}{fuck[1:]}"
                        stack.append(fuckoded)
                    else:
                        stack.append(fuck)
                elif token == "startswith":
                    needle = stack.pop()
                    haystack = stack.pop()
                    stack.append(str(haystack).startswith(str(needle)))
                elif token == "contains":
                    needle = stack.pop()
                    haystack = stack.pop()
                    stack.append(str(needle) in str(haystack))
                elif token == "randbit":
                    stack.append(random.choice([True, False]))
                elif token == "someone":
                    stack.append(random.choice(group_peers or ["No one"]))
                elif token == "self":
                    stack.append(self_)
                elif token == "upper":
                    to_change = stack.pop()
                    stack.append(str(to_change).upper())
                elif token == "lower":
                    to_change = stack.pop()
                    stack.append(str(to_change).lower())
                elif token == "nothing":
                    stack.append(None)
                elif token == "[]":
                    stack.append([])
                elif token == "++":
                    head = stack.pop()
                    tail = stack.pop()
                    tail.append(head)
                    stack.append(tail)
                elif token == "shuffle":
                    list_ = stack.pop()
                    random.shuffle(list_)
                    stack.append(list_)
                elif token == "head":
                    list_ = stack.pop()
                    stack.append(list_[-1])
                elif token == "break":
                    stack.append("\n")
                elif len(token) > 1 and token[0] == '"' and token[-1] == '"':
                    # Quoted string literals
                    stack.append(token[1:-1])
                elif token in dictionary_mappings.keys():
                    source = str(stack.pop())
                    dictionary = dictionary_mappings[token]

                    def index_of(source: str, char: str) -> int | None:
                        try:
                            return source.index(char)
                        except ValueError:
                            return None

                    indices = [index_of(dictionary_mappings["standard"], ch) for ch in source]
                    result = "".join([dictionary[index] if index else source[index] for index in indices])
                    stack.append(result)
                else:
                    stack.append(token)  # literals, etc.

        return forth_logic

    def match(self, input_str: str, group_peers: list[str], self_: str) -> Optional[str]:
        # Exact match: trigger the exact match
        # Starts with: trigger all that start with it
        # Empty prefix: match all input
        exact_match = input_str == self.prefix
        starts_with = input_str.startswith(f"{self.prefix} ")
        empty_prefix = self.prefix == ""
        if not (exact_match or starts_with or empty_prefix):
            return None

        if starts_with:
            input_str = self.prefix.join(input_str.split(self.prefix)[1:])
        elif exact_match:
            input_str = f"{input_str} "

        if self.operation == "word":
            words = input_str.split()
            transformed_words = [self.transform_word(word, idx + 1 == len(words), group_peers, self_) for idx, word in enumerate(words)]
            return ' '.join([str(word) for word in transformed_words if word])
        elif self.operation == "char":
            transformed_chars = [self.transform_char(c, idx + 1 == len(input_str), group_peers, self_) for idx, c in enumerate(input_str)]
            return ''.join([str(char) for char in transformed_chars if char])
        elif self.operation == "sentence":
            sentences = input_str.splitlines()
            transformed_sentences = [
                self.transform_sentence(s, idx + 1 == len(sentences), group_peers, self_) for idx, s in enumerate(sentences)
            ]
            return '\n'.join([str(sentence) for sentence in transformed_sentences if sentence])
        return None

    def transform_word(self, word: str, terminal: bool, group_peers: list[str], self_: str) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, word, terminal, group_peers, self_)
        return stack[-1]  # We assume the final result is at the top of the stack

    def transform_char(self, char: str, terminal: bool, group_peers: list[str], self_: str) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, char, terminal, group_peers, self_)
        return stack[-1]

    def transform_sentence(self, sentence: str, terminal: bool, group_peers: list[str], self_: str) -> str | bool | None:
        stack: list[str | bool | None] = []
        assert self.logic
        self.logic(stack, sentence, terminal, group_peers, self_)
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


def evaluate_all_triggers(input_str: str, all_triggers: list[Trigger], group_peers: list[str], self_: str) -> Generator[str, None, None]:
    for trigger in all_triggers:
        result = trigger.match(input_str, group_peers, self_)
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

fuckode_spec = """
fuckode
word -> word fuckode
""".strip()

woah_spec = """
woah
sentence -> "woah heh"
""".strip()

aww_spec = """.

sentence -> "awwwwwwwwwwwwwww" nothing sentence "aww" startswith if
""".strip()[1:]

mash_spec = """.

sentence -> self " and " concat someone concat " " concat [] "happy" ++ "sad" ++ shuffle head concat nothing sentence "mash" startswith if
""".strip()[1:]

if __name__ == "__main__":
    trigger1 = create_trigger(sassy_spec)
    assert trigger1.value, f"{trigger1.success} {trigger1.value}"

    trigger2 = create_trigger(lmao_spec)
    assert trigger2.value, f"{trigger2.success} {trigger2.value}"

    trigger3 = create_trigger(mock_spec)
    assert trigger3.value, f"{trigger3.success} {trigger3.value}"

    trigger4 = create_trigger(angry_spec)
    assert trigger4.value, f"{trigger4.success} {trigger4.value}"

    trigger_fuckode = create_trigger(fuckode_spec)
    assert trigger_fuckode.value, f"{trigger_fuckode.success} {trigger_fuckode.value}"

    trigger5 = create_trigger(woah_spec)
    assert trigger5.value, f"{trigger5.success} {trigger5.value}"

    trigger6 = create_trigger(aww_spec)
    assert trigger6.value, f"{trigger6.success} {trigger6.value}"

    trigger7 = create_trigger(mash_spec)
    assert trigger7.value, f"{trigger7.success} {trigger7.value}"

    triggers = [
        trigger1.value,
        trigger2.value,
        trigger3.value,
        trigger4.value,
        trigger_fuckode.value,
        trigger5.value,
        trigger6.value,
        trigger7.value,
    ]

    group_peers = ["foobar", "qwerty"]

    inputs = [
        "sassy hello world foobar",
        "haha lmao hello world foobar",
        "mock hello world",
        "an ignored input example",
        "angry hello world",
        "fuckode fuck",
        "woah",
        "aww ? aww",
        "mash",
    ]

    for input_ in inputs:
        for result in evaluate_all_triggers(input_, triggers, group_peers, "B-lake"):
            print(result)
