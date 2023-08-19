
from typing import List, Optional
from dataclasses import dataclass, fields  # TODO I don't think I'm using fields correctly

from persistence import PersistenceMixin

@dataclass
class UserPoints:
    jid: str
    displayname: Optional[str]
    points: int


@dataclass
class Points(PersistenceMixin):
    users: List[UserPoints]

    def __post_init__(self):
        if self.users and isinstance(self.users[0], dict):
            self.users = [UserPoints(**fields) for fields in self.users]


    @staticmethod
    def default_ctor() -> "Points":
        print("Creating empty points.yaml")
        return Points(users=[])


def atomic_incr(user_jid: str, displayname: Optional[str]) -> int:
    """
    Increase the user's points by 1 and return the result.

    Data is persisted.
    """
    points: Points = Points.read("points.yaml", default_ctor=Points.default_ctor)

    points_mapping = {user.jid: user.points for user in points.users}
    new_points = points_mapping.get(user_jid, 0) + 1

    points.users = [
        UserPoints(jid=user_jid, displayname=displayname, points=new_points) if user.jid == user_jid else user
        for user in points.users
    ]

    if not any(user.jid == user_jid for user in points.users):
        points.users.append(UserPoints(jid=user_jid, displayname=displayname, points=new_points))

    points.write("points.yaml")

    return new_points

if __name__ == "__main__":
    print(atomic_incr("testjid", None))
