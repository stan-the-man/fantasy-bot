import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS rosters (
    roster_id INTEGER PRIMARY KEY,
    league_id TEXT,
    owner_id TEXT,
    players TEXT,
    starters TEXT,
    reserve TEXT,
    taxi TEXT,
    co_owners TEXT,
    keepers TEXT,
    player_map TEXT,
    metadata TEXT,
    settings TEXT
)
"""


@dataclass
class Roster:
    roster_id: int
    league_id: str
    owner_id: str
    players: list = field(default_factory=list)
    starters: list = field(default_factory=list)
    reserve: list = field(default_factory=list)
    taxi: list = field(default_factory=list)
    co_owners: list = field(default_factory=list)
    keepers: list = field(default_factory=list)
    player_map: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    settings: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        return cls(
            roster_id=data.get("roster_id"),
            league_id=data.get("league_id"),
            owner_id=data.get("owner_id"),
            players=data.get("players") or [],
            starters=data.get("starters") or [],
            reserve=data.get("reserve") or [],
            taxi=data.get("taxi") or [],
            co_owners=data.get("co_owners") or [],
            keepers=data.get("keepers") or [],
            player_map=data.get("player_map") or {},
            metadata=data.get("metadata") or {},
            settings=data.get("settings") or {},
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO rosters (
                roster_id, league_id, owner_id, players, starters, reserve,
                taxi, co_owners, keepers, player_map, metadata, settings
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(roster_id) DO UPDATE SET
                league_id=excluded.league_id,
                owner_id=excluded.owner_id,
                players=excluded.players,
                starters=excluded.starters,
                reserve=excluded.reserve,
                taxi=excluded.taxi,
                co_owners=excluded.co_owners,
                keepers=excluded.keepers,
                player_map=excluded.player_map,
                metadata=excluded.metadata,
                settings=excluded.settings
            """,
            (
                self.roster_id,
                self.league_id,
                self.owner_id,
                json.dumps(self.players),
                json.dumps(self.starters),
                json.dumps(self.reserve),
                json.dumps(self.taxi),
                json.dumps(self.co_owners),
                json.dumps(self.keepers),
                json.dumps(self.player_map),
                json.dumps(self.metadata),
                json.dumps(self.settings),
            ),
        )
        db.commit()


def import_rosters(db, rosters_json):
    db.execute(CREATE_TABLE_SQL)
    rosters = [Roster.from_dict(r) for r in rosters_json]
    for roster in rosters:
        roster.save(db)
    return rosters


def _row_to_roster(row):
    data = dict(row)
    for key in ("players", "starters", "reserve", "taxi", "co_owners", "keepers"):
        data[key] = json.loads(data[key] or "[]")
    for key in ("player_map", "metadata", "settings"):
        data[key] = json.loads(data[key] or "{}")
    return Roster.from_dict(data)


def get_roster(db, roster_id):
    row = db.execute(
        "SELECT * FROM rosters WHERE roster_id = ?", (roster_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_roster(row)


def get_rosters(db):
    rows = db.execute("SELECT * FROM rosters").fetchall()
    return [_row_to_roster(row) for row in rows]
