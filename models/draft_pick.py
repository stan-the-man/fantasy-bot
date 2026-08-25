import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS draft_picks (
    draft_id TEXT,
    pick_no INTEGER,
    player_id TEXT,
    picked_by TEXT,
    roster_id TEXT,
    round INTEGER,
    draft_slot INTEGER,
    is_keeper INTEGER,
    metadata TEXT,
    PRIMARY KEY (draft_id, pick_no)
)
"""


@dataclass
class DraftPick:
    draft_id: str
    pick_no: int
    player_id: str
    picked_by: str = None
    roster_id: str = None
    round: int = None
    draft_slot: int = None
    is_keeper: bool = None
    metadata: dict = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data):
        return cls(
            draft_id=data.get("draft_id"),
            pick_no=data.get("pick_no"),
            player_id=data.get("player_id"),
            picked_by=data.get("picked_by"),
            roster_id=data.get("roster_id"),
            round=data.get("round"),
            draft_slot=data.get("draft_slot"),
            is_keeper=data.get("is_keeper"),
            metadata=data.get("metadata") or {},
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO draft_picks (
                draft_id, pick_no, player_id, picked_by, roster_id,
                round, draft_slot, is_keeper, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(draft_id, pick_no) DO UPDATE SET
                player_id=excluded.player_id,
                picked_by=excluded.picked_by,
                roster_id=excluded.roster_id,
                round=excluded.round,
                draft_slot=excluded.draft_slot,
                is_keeper=excluded.is_keeper,
                metadata=excluded.metadata
            """,
            (
                self.draft_id,
                self.pick_no,
                self.player_id,
                self.picked_by,
                self.roster_id,
                self.round,
                self.draft_slot,
                None if self.is_keeper is None else int(self.is_keeper),
                json.dumps(self.metadata),
            ),
        )
        db.commit()


def import_draft_picks(db, draft_picks_json):
    db.execute(CREATE_TABLE_SQL)
    draft_picks = [DraftPick.from_dict(p) for p in draft_picks_json]
    for draft_pick in draft_picks:
        draft_pick.save(db)
    return draft_picks


def _row_to_draft_pick(row):
    data = dict(row)
    data["metadata"] = json.loads(data["metadata"] or "{}")
    if data["is_keeper"] is not None:
        data["is_keeper"] = bool(data["is_keeper"])
    return DraftPick.from_dict(data)


def get_draft_picks(db, draft_id):
    rows = db.execute(
        "SELECT * FROM draft_picks WHERE draft_id = ? ORDER BY pick_no", (draft_id,)
    ).fetchall()
    return [_row_to_draft_pick(row) for row in rows]
