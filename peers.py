from __future__ import annotations

from dataclasses import dataclass, fields, field
import sqlite3
from typing import List

from sqlite_persistence import SqlitePersistenceMixin


@dataclass
class Peer(SqlitePersistenceMixin):
    jid: str = field(metadata={'db_type': 'TEXT PRIMARY KEY', 'index': True, 'nullable': False})
    display_name: str | None = field(default=None, metadata={'db_type': 'TEXT', 'index': True, 'nullable': True})
    group_jid: str | None = field(default=None, metadata={'db_type': 'TEXT', 'index': True, 'nullable': True})


class Peers:
    @staticmethod
    def get(jid: str, *, conn: sqlite3.Connection) -> str | None:
        """Gets the display name for the peer with the given jid."""

        maybe_peer: SqlitePersistenceMixin | None = Peer.load(conn, jid=jid)
        if maybe_peer:
            assert isinstance(maybe_peer, Peer)
            return maybe_peer.display_name

        return None

    @staticmethod
    def get_all_in_group_jid(group_jid: str, *, conn: sqlite3.Connection) -> list[Peer]:
        return Peer.load_all(conn=conn, group_jid=group_jid)  # type: ignore

    @staticmethod
    def get_all(*, conn: sqlite3.Connection) -> list[Peer]:
        return Peer.load_all(conn=conn)  # type: ignore

    @staticmethod
    def all_jids(*, conn: sqlite3.Connection) -> list[str]:
        """Gets all the recorded peer jids"""
        peers: list[Peer] = Peer.load_all(conn)  # type: ignore
        return [entry.jid for entry in peers]

    @staticmethod
    def insert(*, conn: sqlite3.Connection, jid: str, display_name: str | None = None, group_jid: str | None = None):
        maybe_peer: SqlitePersistenceMixin | None = Peer.load(conn, jid=jid)
        if maybe_peer:
            assert isinstance(maybe_peer, Peer)
            if not display_name:
               display_name = maybe_peer.display_name

            if not group_jid:
                group_jid = maybe_peer.group_jid

        Peer(jid=jid, display_name=display_name, group_jid=group_jid).save(conn)


if __name__ == "__main__":
    conn = sqlite3.connect("peers_test.db")

    Peers.insert(conn=conn, jid="abc123_", display_name="Test User")

    peer = Peers.get("abc123_", conn=conn)
    print(peer)

    Peers.insert(conn=conn, jid="foobar_")

    print(Peers.all_jids(conn=conn))

    # Group test
    Peers.insert(conn=conn, jid="a_", display_name="Test User", group_jid="q")
    Peers.insert(conn=conn, jid="b_", display_name="Test User 2", group_jid="q")
    Peers.insert(conn=conn, jid="c_", group_jid="q")

    print(Peers.get_all_in_group_jid(group_jid="q", conn=conn))

    # Overwrite test
    Peers.insert(conn=conn, jid="overwrite")
    print(Peers.get("overwrite", conn=conn))
    Peers.insert(conn=conn, jid="overwrite", display_name="Overwritten!")
    print(Peers.get("overwrite", conn=conn))

    conn2 = sqlite3.connect("prod.db")
    # print(Peer.load_all(conn=conn2))
