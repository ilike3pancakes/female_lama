
from dataclasses import asdict
import typing
from typing import Callable
import yaml


class PersistenceMixin:
    def write(self, where: str) -> None:
        with open(where, "w") as f:
            f.write(yaml.dump(asdict(self)))

    @classmethod
    def read(cls, where: str, *, default_ctor: Callable[[], typing.Any]) -> typing.Any:
        try:
            with open(where) as f:
                return cls(**yaml.load(f.read(), Loader=yaml.Loader))
        except FileNotFoundError:
            return default_ctor()
