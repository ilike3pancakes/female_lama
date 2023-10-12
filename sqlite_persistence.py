from __future__ import annotations

from dataclasses import fields, dataclass, field, is_dataclass
from typing import Type, Optional
import sqlite3

class SqlitePersistenceMixin:
    @classmethod
    def _get_dataclass_fields(cls: Type['SqlitePersistenceMixin']):
        assert is_dataclass(cls)
        return fields(cls)

    @classmethod
    def _get_table_name(cls) -> str:
        return cls.__name__

    @classmethod
    def _create_table_if_not_exists(cls: Type['SqlitePersistenceMixin'], conn: sqlite3.Connection) -> None:
        table_name = cls._get_table_name()
        columns = ", ".join(
            [
                f"{field.name} {field.metadata['db_type']}"
                f"{' NOT NULL' if not field.metadata.get('nullable', True) else ''}"
                for field in cls._get_dataclass_fields()
            ]
        )
        indexes = "; ".join(
            [
                f"CREATE INDEX IF NOT EXISTS idx_{table_name}_{field.name} ON {table_name}({field.name})"
                for field in cls._get_dataclass_fields() if field.metadata.get('index')
            ]
        )

        conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({columns})")
        if indexes:
            conn.executescript(indexes)

    def save(self, conn: sqlite3.Connection) -> None:
        self._create_table_if_not_exists(conn)
        columns = ", ".join([field.name for field in self._get_dataclass_fields()])
        placeholders = ", ".join(["?" for _ in self._get_dataclass_fields()])
        values = tuple([getattr(self, field.name) for field in self._get_dataclass_fields()])

        conn.execute(f"INSERT OR REPLACE INTO {self._get_table_name()} ({columns}) VALUES ({placeholders})", values)

    @classmethod
    def load(
        cls: Type['SqlitePersistenceMixin'], conn: sqlite3.Connection, **query
    ) -> Optional['SqlitePersistenceMixin']:
        cls._create_table_if_not_exists(conn)

        where_clause = " AND ".join([f"{key} = ?" for key in query])
        values = tuple(query.values())

        row = conn.execute(f"SELECT * FROM {cls._get_table_name()} WHERE {where_clause}", values).fetchone()

        if row:
            return cls(**dict(zip([field.name for field in cls._get_dataclass_fields()], row)))
        return None

    @classmethod
    def load_all(
        cls: Type['SqlitePersistenceMixin'], conn: sqlite3.Connection, **query
    ) -> list['SqlitePersistenceMixin']:
        cls._create_table_if_not_exists(conn)

        where_clause = " AND ".join([f"{key} = ?" for key in query])
        values = tuple(query.values())

        rows = conn.execute(
            f"SELECT * FROM {cls._get_table_name()} {'WHERE' if where_clause else ''} {where_clause}", values
        ).fetchall()

        # Creating instances for all fetched rows and returning them as a list
        return [cls(**dict(zip([field.name for field in cls._get_dataclass_fields()], row))) for row in rows]



if __name__ == '__main__':
    @dataclass
    class MyData(SqlitePersistenceMixin):
        id: int = field(metadata={'db_type': 'INTEGER PRIMARY KEY', 'index': True, 'nullable': False})
        name: str = field(metadata={'db_type': 'TEXT', 'index': True, 'nullable': False})
        test: str = field(metadata={'db_type': 'TEXT', 'index': True, 'nullable': False})
        age: int | None = field(default=None, metadata={'db_type': 'INTEGER', 'nullable': True})

    conn = sqlite3.connect("test.db")

    data = MyData(id=1, name="John", age=55, test="a")
    data.save(conn)

    data = MyData(id=2, name="John", test="b")
    data.save(conn)

    loaded_data = MyData.load(conn, id=1)
    print(loaded_data)

    loaded_data = MyData.load(conn, id=2)
    print(loaded_data)

    # Valid with id = None but fails mypy, id gets auto-incremented; but test=None is invalid, fails at insert time.
    data = MyData(id=3, name="X", test="c")
    data.save(conn)

    loaded_data = MyData.load(conn, name="X")
    print(loaded_data)

    loaded_data2 = MyData.load_all(conn, name="John")
    print(loaded_data2)
