import json
from dataclasses import dataclass, field

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS transactions (
    transaction_id TEXT PRIMARY KEY,
    type TEXT,
    status TEXT,
    status_updated INTEGER,
    created INTEGER,
    leg INTEGER,
    creator TEXT,
    settings TEXT,
    metadata TEXT,
    roster_ids TEXT,
    consenter_ids TEXT,
    drops TEXT,
    adds TEXT,
    draft_picks TEXT,
    waiver_budget TEXT
)
"""


@dataclass
class Transaction:
    transaction_id: str
    type: str = None
    status: str = None
    status_updated: int = None
    created: int = None
    leg: int = None
    creator: str = None
    settings: dict = field(default_factory=dict)
    metadata: dict = field(default_factory=dict)
    roster_ids: list = field(default_factory=list)
    consenter_ids: list = field(default_factory=list)
    drops: dict = field(default_factory=dict)
    adds: dict = field(default_factory=dict)
    draft_picks: list = field(default_factory=list)
    waiver_budget: list = field(default_factory=list)

    @classmethod
    def from_dict(cls, data):
        return cls(
            transaction_id=data.get("transaction_id"),
            type=data.get("type"),
            status=data.get("status"),
            status_updated=data.get("status_updated"),
            created=data.get("created"),
            leg=data.get("leg"),
            creator=data.get("creator"),
            settings=data.get("settings") or {},
            metadata=data.get("metadata") or {},
            roster_ids=data.get("roster_ids") or [],
            consenter_ids=data.get("consenter_ids") or [],
            drops=data.get("drops") or {},
            adds=data.get("adds") or {},
            draft_picks=data.get("draft_picks") or [],
            waiver_budget=data.get("waiver_budget") or [],
        )

    def save(self, db):
        db.execute(CREATE_TABLE_SQL)
        db.execute(
            """
            INSERT INTO transactions (
                transaction_id, type, status, status_updated, created, leg, creator,
                settings, metadata, roster_ids, consenter_ids, drops, adds,
                draft_picks, waiver_budget
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(transaction_id) DO UPDATE SET
                type=excluded.type,
                status=excluded.status,
                status_updated=excluded.status_updated,
                created=excluded.created,
                leg=excluded.leg,
                creator=excluded.creator,
                settings=excluded.settings,
                metadata=excluded.metadata,
                roster_ids=excluded.roster_ids,
                consenter_ids=excluded.consenter_ids,
                drops=excluded.drops,
                adds=excluded.adds,
                draft_picks=excluded.draft_picks,
                waiver_budget=excluded.waiver_budget
            """,
            (
                self.transaction_id,
                self.type,
                self.status,
                self.status_updated,
                self.created,
                self.leg,
                self.creator,
                json.dumps(self.settings),
                json.dumps(self.metadata),
                json.dumps(self.roster_ids),
                json.dumps(self.consenter_ids),
                json.dumps(self.drops),
                json.dumps(self.adds),
                json.dumps(self.draft_picks),
                json.dumps(self.waiver_budget),
            ),
        )
        db.commit()


def import_transactions(db, transactions_json):
    db.execute(CREATE_TABLE_SQL)
    transactions = [Transaction.from_dict(t) for t in transactions_json]
    for transaction in transactions:
        transaction.save(db)
    return transactions


def _row_to_transaction(row):
    data = dict(row)
    for key in ("settings", "metadata", "drops", "adds"):
        data[key] = json.loads(data[key] or "{}")
    for key in ("roster_ids", "consenter_ids", "draft_picks", "waiver_budget"):
        data[key] = json.loads(data[key] or "[]")
    return Transaction.from_dict(data)


def get_transaction(db, transaction_id):
    row = db.execute(
        "SELECT * FROM transactions WHERE transaction_id = ?", (transaction_id,)
    ).fetchone()
    if row is None:
        return None
    return _row_to_transaction(row)


def get_transactions(db):
    rows = db.execute("SELECT * FROM transactions").fetchall()
    return [_row_to_transaction(row) for row in rows]


def get_all_transactions(db):
    row = db.execute(
        "SELECT COUNT(*) FROM transactions WHERE type IN ('waiver', 'free_agent')"
    ).fetchone()
    return row[0]


def get_waiver_transactions(db, roster_id):
    rows = db.execute(
        """
        SELECT * FROM transactions
        WHERE type IN ('waiver', 'free_agent')
        AND EXISTS (
            SELECT 1 FROM json_each(roster_ids) WHERE value = ?
        )
        """,
        (roster_id,),
    ).fetchall()
    return [_row_to_transaction(row) for row in rows]
