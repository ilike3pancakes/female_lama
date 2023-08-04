from __future__ import annotations
from dataclasses import dataclass
from typing import Generator, Optional# , Protocol


class ForthOp(): # Protocol
    def apply(self, vals: list[ForthVal]) -> None:
        ...


class ForthAdd(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        b = vals.pop().val
        a = vals.pop().val
        assert a
        assert b
        vals.append(ForthVal(val=a + b))


class ForthNeg(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        a = vals.pop().val
        assert a
        vals.append(ForthVal(val=-a))


class ForthSub(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        ForthNeg().apply(vals)
        ForthAdd().apply(vals)


class ForthMult(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        b = vals.pop().val
        a = vals.pop().val
        assert a
        assert b
        vals.append(ForthVal(val=a * b))


class ForthInverse(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        a = vals.pop().val
        assert a
        vals.append(ForthVal(val=1 / a))


class ForthDiv(ForthOp):
    def apply(self, vals: list[ForthVal]) -> None:
        ForthInverse().apply(vals)
        ForthMult().apply(vals)


@dataclass
class ForthVal(ForthOp):
    val: Optional[float] = None
    op: Optional[ForthOp] = None

    def apply(self, vals: list[ForthVal]) -> None:
        if self.val:
            vals.append(self)
            return

        assert self.op
        self.op.apply(vals)


def parse(token: str) -> ForthOp:
    ops: dict[str, ForthOp | None] = {
        "+": ForthAdd(),
        "/": ForthDiv(),
        "*": ForthMult(),
        "-": ForthSub(),
    }

    return ops.get(token, None) or ForthVal(val=float(token))


def forth(tokens: Generator[ForthVal, None, None]) -> float:
    stack: list[ForthVal] = []
    for token in tokens:
        token.apply(stack)

    assert stack[0].val
    return stack[0].val

def calculate(input: str) -> str:
    """
    Accepts a pre-trimmed maths query in the form of forth over floats.

    3 3 + -> 6.0
    3 + -> Error("Not enough values on the stack to +")
    """
    tokens = (parse(token) for token in filter(lambda x: x, input.strip().split(' ')))
    return f"😮‍💨☝️🖩 {forth(tokens)}"


if __name__ == "__main__":
    print(calculate("300 2.2 /"))
