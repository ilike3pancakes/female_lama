
from dataclasses import asdict
from pathlib import Path
import typing
from typing import Callable
import yaml
import logging

logger = logging.getLogger()


class PersistenceMixin:
    def write(self, where: str) -> None:
        path = Path(where)
        with open(path, "w") as f:
            # https://github.com/python/mypy/issues/14941
            f.write(yaml.dump(asdict(self)))  # type: ignore
            logger.info(f"Wrote to {path.absolute}")

    @classmethod
    def read(cls, where: str, *, default_ctor: Callable[[], typing.Any]) -> typing.Any:
        try:
            with open(where) as f:
                return cls(**yaml.load(f.read(), Loader=yaml.Loader))
        except FileNotFoundError:
            return default_ctor()
