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
        columns = ", ".join([f"{field.name} {field.metadata['db_type']}" for field in cls._get_dataclass_fields()])
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


@dataclass
class MyData(SqlitePersistenceMixin):
    id: int = field(metadata={'db_type': 'INTEGER PRIMARY KEY', 'index': True})
    name: str = field(metadata={'db_type': 'TEXT', 'index': True})
    age: int = field(metadata={'db_type': 'INTEGER'})

conn = sqlite3.connect("test.db")

data = MyData(id=1, name="John", age=55)
data.save(conn)

loaded_data = MyData.load(conn, id=1)
print(loaded_data)
