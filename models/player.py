import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS players (
    player_id TEXT PRIMARY KEY,
    first_name TEXT,
    last_name TEXT,
    search_first_name TEXT,
    search_last_name TEXT,
    search_full_name TEXT,
    hashtag TEXT,
    status TEXT,
    sport TEXT,
    team TEXT,
    position TEXT,
    fantasy_positions TEXT,
    number INTEGER,
    depth_chart_position INTEGER,
    depth_chart_order INTEGER,
    height TEXT,
    weight TEXT,
    age INTEGER,
    college TEXT,
    birth_country TEXT,
    years_exp INTEGER,
    injury_status TEXT,
    injury_start_date TEXT,
    practice_participation TEXT,
    search_rank INTEGER,
    fantasy_data_id INTEGER,
    sportradar_id TEXT,
    stats_id TEXT,
    espn_id TEXT,
    rotowire_id TEXT,
    rotoworld_id TEXT,
    yahoo_id TEXT
)
"""


@dataclass
class Player:
    player_id: str
    first_name: str = None
    last_name: str = None
    search_first_name: str = None
    search_last_name: str = None
    search_full_name: str = None
    hashtag: str = None
    status: str = None
    sport: str = None
    team: str = None
    position: str = None
    fantasy_positions: list = field(default_factory=list)
    number: int = None
    depth_chart_position: int = None
    depth_chart_order: int = None
    height: str = None
    weight: str = None
    age: int = None
    college: str = None
    birth_country: str = None
    years_exp: int = None
    injury_status: str = None
    injury_start_date: str = None
    practice_participation: str = None
    search_rank: int = None
    fantasy_data_id: int = None
    sportradar_id: str = None
    stats_id: str = None
    espn_id: str = None
    rotowire_id: str = None
    rotoworld_id: str = None
    yahoo_id: str = None

    @classmethod
    def from_dict(cls, data):
        return cls(
            player_id=data.get("player_id"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            search_first_name=data.get("search_first_name"),
            search_last_name=data.get("search_last_name"),
            search_full_name=data.get("search_full_name"),
            hashtag=data.get("hashtag"),
            status=data.get("status"),
            sport=data.get("sport"),
            team=data.get("team"),
            position=data.get("position"),
            fantasy_positions=data.get("fantasy_positions") or [],
            number=data.get("number"),
            depth_chart_position=data.get("depth_chart_position"),
            depth_chart_order=data.get("depth_chart_order"),
            height=data.get("height"),
            weight=data.get("weight"),
            age=data.get("age"),
            college=data.get("college"),
            birth_country=data.get("birth_country"),
            years_exp=data.get("years_exp"),
            injury_status=data.get("injury_status"),
            injury_start_date=data.get("injury_start_date"),
            practice_participation=data.get("practice_participation"),
            search_rank=data.get("search_rank"),
            fantasy_data_id=data.get("fantasy_data_id"),
            sportradar_id=data.get("sportradar_id"),
            stats_id=data.get("stats_id"),
            espn_id=data.get("espn_id"),
            rotowire_id=data.get("rotowire_id"),
            rotoworld_id=data.get("rotoworld_id"),
            yahoo_id=data.get("yahoo_id"),
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO players (
                player_id, first_name, last_name, search_first_name, search_last_name,
                search_full_name, hashtag, status, sport, team, position, fantasy_positions,
                number, depth_chart_position, depth_chart_order, height, weight, age,
                college, birth_country, years_exp, injury_status, injury_start_date,
                practice_participation, search_rank, fantasy_data_id, sportradar_id,
                stats_id, espn_id, rotowire_id, rotoworld_id, yahoo_id
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(player_id) DO UPDATE SET
                first_name=excluded.first_name,
                last_name=excluded.last_name,
                search_first_name=excluded.search_first_name,
                search_last_name=excluded.search_last_name,
                search_full_name=excluded.search_full_name,
                hashtag=excluded.hashtag,
                status=excluded.status,
                sport=excluded.sport,
                team=excluded.team,
                position=excluded.position,
                fantasy_positions=excluded.fantasy_positions,
                number=excluded.number,
                depth_chart_position=excluded.depth_chart_position,
                depth_chart_order=excluded.depth_chart_order,
                height=excluded.height,
                weight=excluded.weight,
                age=excluded.age,
                college=excluded.college,
                birth_country=excluded.birth_country,
                years_exp=excluded.years_exp,
                injury_status=excluded.injury_status,
                injury_start_date=excluded.injury_start_date,
                practice_participation=excluded.practice_participation,
                search_rank=excluded.search_rank,
                fantasy_data_id=excluded.fantasy_data_id,
                sportradar_id=excluded.sportradar_id,
                stats_id=excluded.stats_id,
                espn_id=excluded.espn_id,
                rotowire_id=excluded.rotowire_id,
                rotoworld_id=excluded.rotoworld_id,
                yahoo_id=excluded.yahoo_id
            """,
            (
                self.player_id,
                self.first_name,
                self.last_name,
                self.search_first_name,
                self.search_last_name,
                self.search_full_name,
                self.hashtag,
                self.status,
                self.sport,
                self.team,
                self.position,
                json.dumps(self.fantasy_positions),
                self.number,
                self.depth_chart_position,
                self.depth_chart_order,
                self.height,
                self.weight,
                self.age,
                self.college,
                self.birth_country,
                self.years_exp,
                self.injury_status,
                self.injury_start_date,
                self.practice_participation,
                self.search_rank,
                self.fantasy_data_id,
                self.sportradar_id,
                self.stats_id,
                self.espn_id,
                self.rotowire_id,
                self.rotoworld_id,
                self.yahoo_id,
            ),
        )
        db.commit()


def import_players(db, players_json):
    db.execute(CREATE_TABLE_SQL)
    players = [Player.from_dict(p) for p in players_json.values()]
    for player in players:
        player.save(db)
    return players


def get_player(db, player_id):
    row = db.execute(
        "SELECT * FROM players WHERE player_id = ?", (player_id,)
    ).fetchone()
    if row is None:
        return None
    data = dict(row)
    data["fantasy_positions"] = json.loads(data["fantasy_positions"] or "[]")
    return Player.from_dict(data)
