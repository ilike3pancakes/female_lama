from dataclasses import fields, dataclass, field
from typing import Type, Optional
import sqlite3

class SQLitePersistenceMixin:
    
    @classmethod
    def _get_table_name(cls) -> str:
        return cls.__name__

    @classmethod
    def _create_table_if_not_exists(cls, conn: sqlite3.Connection) -> None:
        columns = ", ".join([f"{field.name} {field.metadata['db_type']}" for field in fields(cls)])
        indexes = "; ".join([f"CREATE INDEX IF NOT EXISTS idx_{cls._get_table_name()}_{field.name} ON {cls._get_table_name()}({field.name})"
                             for field in fields(cls) if field.metadata.get('index')])

        conn.execute(f"CREATE TABLE IF NOT EXISTS {cls._get_table_name()} ({columns})")
        if indexes:
            conn.executescript(indexes)

    def save(self, conn: sqlite3.Connection) -> None:
        self._create_table_if_not_exists(conn)
        columns = ", ".join([field.name for field in fields(self)])
        placeholders = ", ".join(["?" for _ in fields(self)])
        values = tuple([getattr(self, field.name) for field in fields(self)])

        conn.execute(f"INSERT OR REPLACE INTO {self._get_table_name()} ({columns}) VALUES ({placeholders})", values)

    @classmethod
    def load(cls: Type['SQLitePersistenceMixin'], conn: sqlite3.Connection, **query) -> Optional['SQLitePersistenceMixin']:
        cls._create_table_if_not_exists(conn)
        
        where_clause = " AND ".join([f"{key} = ?" for key in query])
        values = tuple(query.values())

        row = conn.execute(f"SELECT * FROM {cls._get_table_name()} WHERE {where_clause}", values).fetchone()

        if row:
            return cls(**dict(zip([field.name for field in fields(cls)], row)))
        return None


@dataclass
class MyData(SQLitePersistenceMixin):
    id: int = field(metadata={'db_type': 'INTEGER PRIMARY KEY', 'index': True})
    name: str = field(metadata={'db_type': 'TEXT', 'index': True})
    age: int = field(metadata={'db_type': 'INTEGER'})

conn = sqlite3.connect("test.db")

data = MyData(id=1, name="John", age=55)
data.save(conn)

loaded_data = MyData.load(conn, id=1)
print(loaded_data)
