import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS matchups (
    roster_id INTEGER,
    week INTEGER,
    matchup_id INTEGER,
    starters TEXT,
    players TEXT,
    points REAL,
    custom_points REAL,
    PRIMARY KEY (roster_id, week)
)
"""


@dataclass
class Matchup:
    roster_id: int
    week: int
    matchup_id: int
    starters: list = field(default_factory=list)
    players: list = field(default_factory=list)
    points: float = None
    custom_points: float = None

    @classmethod
    def from_dict(cls, data, week):
        return cls(
            roster_id=data.get("roster_id"),
            week=week,
            matchup_id=data.get("matchup_id"),
            starters=data.get("starters") or [],
            players=data.get("players") or [],
            points=data.get("points"),
            custom_points=data.get("custom_points"),
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO matchups (roster_id, week, matchup_id, starters, players, points, custom_points)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(roster_id, week) DO UPDATE SET
                matchup_id=excluded.matchup_id,
                starters=excluded.starters,
                players=excluded.players,
                points=excluded.points,
                custom_points=excluded.custom_points
            """,
            (
                self.roster_id,
                self.week,
                self.matchup_id,
                json.dumps(self.starters),
                json.dumps(self.players),
                self.points,
                self.custom_points,
            ),
        )
        db.commit()


def import_matchups(db, matchups_json, week):
    db.execute(CREATE_TABLE_SQL)
    matchups = [Matchup.from_dict(m, week) for m in matchups_json]
    for matchup in matchups:
        matchup.save(db)
    return matchups


def _row_to_matchup(row):
    data = dict(row)
    data["starters"] = json.loads(data["starters"] or "[]")
    data["players"] = json.loads(data["players"] or "[]")
    return Matchup.from_dict(data, data["week"])


def get_all_matchups_except_roster_for_week(db, roster_id, week):
    rows = db.execute(
        "SELECT * FROM matchups WHERE roster_id != ? AND week = ?", (roster_id, week,)
    ).fetchall()
    return [_row_to_matchup(row) for row in rows]


def get_matchup(db, roster_id, week):
    row = db.execute(
        "SELECT * FROM matchups WHERE roster_id = ? AND week = ?", (roster_id, week,)
    ).fetchone()
    return _row_to_matchup(row)


def get_matchups_for_roster(db, roster_id):
    rows = db.execute(
        "SELECT * FROM matchups WHERE roster_id = ?", (roster_id,)
    ).fetchall()
    return [_row_to_matchup(row) for row in rows]


def get_opponents(db, week, matchup_id, exclude_roster_id):
    rows = db.execute(
        "SELECT * FROM matchups WHERE week = ? AND matchup_id = ? AND roster_id != ?",
        (week, matchup_id, exclude_roster_id),
    ).fetchall()
    return [_row_to_matchup(row) for row in rows]


def get_top_scoring_matchup(db, week):
    row = db.execute(
        "SELECT * FROM matchups WHERE week = ? ORDER BY points DESC LIMIT 1",
        (week,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_matchup(row)

def get_lowest_scoring_matchup(db, week):
    row = db.execute(
        "SELECT * FROM matchups WHERE week = ? ORDER BY points ASC LIMIT 1",
        (week,),
    ).fetchone()
    if row is None:
        return None
    return _row_to_matchup(row)

def get_closest_scoring_matchup(db, week):
    row = db.execute(
        """
        SELECT a.roster_id AS roster_a_id, b.roster_id AS roster_b_id,
               a.points AS points_a, b.points AS points_b
        FROM matchups a
        JOIN matchups b ON a.week = b.week
            AND a.matchup_id = b.matchup_id
            AND a.roster_id < b.roster_id
        WHERE a.week = ?
        ORDER BY ABS(a.points - b.points) ASC
        LIMIT 1
        """,
        (week,),
    ).fetchone()
    if row is None:
        return None
    return dict(row)
