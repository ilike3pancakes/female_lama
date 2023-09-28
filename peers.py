from __future__ import annotations

from dataclasses import dataclass, fields
from typing import List

from persistence import PersistenceMixin


@dataclass
class Peer:
    jid: str
    display_name: str | None
    group_jid: str | None


@dataclass
class Peers(PersistenceMixin):
    entries: List[Peer]

    def __post_init__(self):
        if self.entries and isinstance(self.entries[0], dict):
            self.entries = [Peer(**fields) for fields in self.entries]

    @staticmethod
    def default_ctor() -> "Peers":
        print("Creating empty peers.yaml")
        return Peers(entries=[])

    @staticmethod
    def get(jid: str) -> str | None:
        peers: Peers = Peers.read("peers.yaml", default_ctor=Peers.default_ctor)
        matching_peers = [entry for entry in peers.entries if entry.jid == jid]
        if matching_peers:
            return matching_peers[0].display_name

        return None

    @staticmethod
    def jids() -> list[str]:
        peers: Peers = Peers.read("peers.yaml", default_ctor=Peers.default_ctor)
        return [entry.jid for entry in peers.entries]

    def insert(self, jid: str, *, display_name: str | None = None, group_jid: str | None = None):
        self.entries = [
            Peer(jid=jid, display_name=display_name or user.display_name, group_jid=group_jid or user.group_jid)
            if user.jid == jid else user
            for user in self.entries
        ]

        if not any(user.jid == jid for user in self.entries):
            self.entries.append(Peer(jid=jid, display_name=display_name, group_jid=group_jid))


if __name__ == "__main__":
    peers: Peers = Peers.read("peers.test.yaml", default_ctor=Peers.default_ctor)
    peers.insert("abc123_", display_name="Test User")
    peers.write("peers.test.yaml")

    peers2: Peers = Peers.read("peers.test.yaml", default_ctor=Peers.default_ctor)
    print(peers2)
