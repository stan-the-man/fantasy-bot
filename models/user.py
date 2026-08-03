import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    username TEXT,
    display_name TEXT,
    avatar TEXT,
    metadata TEXT,
    is_owner INTEGER
)
"""


@dataclass
class User:
    user_id: str
    username: str
    display_name: str
    avatar: str
    metadata: dict = field(default_factory=dict)
    is_owner: bool = False

    @classmethod
    def from_dict(cls, data):
        return cls(
            user_id=data.get("user_id"),
            username=data.get("username"),
            display_name=data.get("display_name"),
            avatar=data.get("avatar"),
            metadata=data.get("metadata") or {},
            is_owner=data.get("is_owner", False),
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO users (user_id, username, display_name, avatar, metadata, is_owner)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                username=excluded.username,
                display_name=excluded.display_name,
                avatar=excluded.avatar,
                metadata=excluded.metadata,
                is_owner=excluded.is_owner
            """,
            (
                self.user_id,
                self.username,
                self.display_name,
                self.avatar,
                json.dumps(self.metadata),
                int(self.is_owner),
            ),
        )
        db.commit()

    def team_name(self):
        return self.metadata.get('team_name') or self.display_name


def import_users(db, users_json):
    db.execute(CREATE_TABLE_SQL)
    users = [User.from_dict(u) for u in users_json]
    for user in users:
        user.save(db)
    return users


def get_user(db, user_id):
    row = db.execute(
        "SELECT * FROM users WHERE user_id = ?", (user_id,)
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["metadata"] = json.loads(data["metadata"] or "{}")
    data["is_owner"] = bool(data["is_owner"])
    return User.from_dict(data)
