import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS leagues (
    league_id TEXT PRIMARY KEY,
    name TEXT,
    status TEXT,
    sport TEXT,
    season TEXT,
    season_type TEXT,
    total_rosters INTEGER,
    settings TEXT,
    scoring_settings TEXT,
    roster_positions TEXT,
    previous_league_id TEXT,
    draft_id TEXT,
    avatar TEXT
)
"""


@dataclass
class League:
    league_id: str
    name: str
    status: str
    sport: str
    season: str
    season_type: str
    total_rosters: int
    settings: dict = field(default_factory=dict)
    scoring_settings: dict = field(default_factory=dict)
    roster_positions: list = field(default_factory=list)
    previous_league_id: str = None
    draft_id: str = None
    avatar: str = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            league_id=data.get("league_id"),
            name=data.get("name"),
            status=data.get("status"),
            sport=data.get("sport"),
            season=data.get("season"),
            season_type=data.get("season_type"),
            total_rosters=data.get("total_rosters"),
            settings=data.get("settings") or {},
            scoring_settings=data.get("scoring_settings") or {},
            roster_positions=data.get("roster_positions") or [],
            previous_league_id=data.get("previous_league_id"),
            draft_id=data.get("draft_id"),
            avatar=data.get("avatar"),
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO leagues (
                league_id, name, status, sport, season, season_type, total_rosters,
                settings, scoring_settings, roster_positions, previous_league_id,
                draft_id, avatar
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(league_id) DO UPDATE SET
                name=excluded.name,
                status=excluded.status,
                sport=excluded.sport,
                season=excluded.season,
                season_type=excluded.season_type,
                total_rosters=excluded.total_rosters,
                settings=excluded.settings,
                scoring_settings=excluded.scoring_settings,
                roster_positions=excluded.roster_positions,
                previous_league_id=excluded.previous_league_id,
                draft_id=excluded.draft_id,
                avatar=excluded.avatar
            """,
            (
                self.league_id,
                self.name,
                self.status,
                self.sport,
                self.season,
                self.season_type,
                self.total_rosters,
                json.dumps(self.settings),
                json.dumps(self.scoring_settings),
                json.dumps(self.roster_positions),
                self.previous_league_id,
                self.draft_id,
                self.avatar,
            ),
        )
        db.commit()


def import_league(db, league_json):
    db.execute(CREATE_TABLE_SQL)
    league = League.from_dict(league_json)
    league.save(db)
    return league


def _row_to_league(row):
    data = dict(row)
    data["settings"] = json.loads(data["settings"] or "{}")
    data["scoring_settings"] = json.loads(data["scoring_settings"] or "{}")
    data["roster_positions"] = json.loads(data["roster_positions"] or "[]")
    return League.from_dict(data)


def get_league(db, league_id):
    row = db.execute(
        "SELECT * FROM leagues WHERE league_id = ?", (league_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_league(row)
