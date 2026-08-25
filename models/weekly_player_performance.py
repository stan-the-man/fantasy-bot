import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS weekly_player_performances (
    player_id TEXT,
    week INTEGER,
    season TEXT,
    season_type TEXT,
    status TEXT,
    date TEXT,
    category TEXT,
    last_modified INTEGER,
    sport TEXT,
    team TEXT,
    opponent TEXT,
    is_away_team INTEGER,
    game_id TEXT,
    week_shard TEXT,
    company TEXT,
    updated_at INTEGER,
    stats TEXT,
    PRIMARY KEY (player_id, week, season)
)
"""


@dataclass
class WeeklyPlayerPerformance:
    player_id: str
    week: int
    season: str
    season_type: str = None
    status: str = None
    date: str = None
    category: str = None
    last_modified: int = None
    sport: str = None
    team: str = None
    opponent: str = None
    is_away_team: bool = None
    game_id: str = None
    week_shard: str = None
    company: str = None
    updated_at: int = None
    stats: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        return cls(
            player_id=data.get("player_id"),
            week=data.get("week"),
            season=data.get("season"),
            season_type=data.get("season_type"),
            status=data.get("status"),
            date=data.get("date"),
            category=data.get("category"),
            last_modified=data.get("last_modified"),
            sport=data.get("sport"),
            team=data.get("team"),
            opponent=data.get("opponent"),
            is_away_team=data.get("is_away_team"),
            game_id=data.get("game_id"),
            week_shard=data.get("week_shard"),
            company=data.get("company"),
            updated_at=data.get("updated_at"),
            stats=data.get("stats") or {},
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO weekly_player_performances (
                player_id, week, season, season_type, status, date, category,
                last_modified, sport, team, opponent, is_away_team, game_id,
                week_shard, company, updated_at, stats
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id, week, season) DO UPDATE SET
                season_type=excluded.season_type,
                status=excluded.status,
                date=excluded.date,
                category=excluded.category,
                last_modified=excluded.last_modified,
                sport=excluded.sport,
                team=excluded.team,
                opponent=excluded.opponent,
                is_away_team=excluded.is_away_team,
                game_id=excluded.game_id,
                week_shard=excluded.week_shard,
                company=excluded.company,
                updated_at=excluded.updated_at,
                stats=excluded.stats
            """,
            (
                self.player_id,
                self.week,
                self.season,
                self.season_type,
                self.status,
                self.date,
                self.category,
                self.last_modified,
                self.sport,
                self.team,
                self.opponent,
                None if self.is_away_team is None else int(self.is_away_team),
                self.game_id,
                self.week_shard,
                self.company,
                self.updated_at,
                json.dumps(self.stats),
            ),
        )
        db.commit()


def import_weekly_player_performance(db, performance_json):
    db.execute(CREATE_TABLE_SQL)
    performance = WeeklyPlayerPerformance.from_dict(performance_json)
    performance.save(db)
    return performance


def _row_to_performance(row):
    data = dict(row)
    data["stats"] = json.loads(data["stats"] or "{}")
    if data["is_away_team"] is not None:
        data["is_away_team"] = bool(data["is_away_team"])
    return WeeklyPlayerPerformance.from_dict(data)


def get_weekly_player_performance(db, player_id, week, season):
    row = db.execute(
        "SELECT * FROM weekly_player_performances WHERE player_id = ? AND week = ? AND season = ?",
        (player_id, week, season),
    ).fetchone()
    if row is None:
        return None
    return _row_to_performance(row)


def get_performances_for_players(db, player_ids, week, season):
    if not player_ids:
        return {}
    placeholders = ','.join('?' for _ in player_ids)
    rows = db.execute(
        f"SELECT * FROM weekly_player_performances WHERE week = ? AND season = ? AND player_id IN ({placeholders})",
        (week, season, *player_ids),
    ).fetchall()
    return {row['player_id']: _row_to_performance(row) for row in rows}
