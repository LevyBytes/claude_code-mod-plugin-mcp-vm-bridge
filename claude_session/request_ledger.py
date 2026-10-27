"""Private relay-owned request journal; completed entries do not consume active capacity."""
import json
import sqlite3
from os import PathLike


class RequestLedger:
    def __init__(self, path: str | PathLike[str] = ':memory:'):
        self.db = sqlite3.connect(str(path), check_same_thread=False)
        self.db.execute('CREATE TABLE IF NOT EXISTS requests '
                        '(binding TEXT, id TEXT, state TEXT, body TEXT, PRIMARY KEY(binding, id))')
        self.db.execute('CREATE INDEX IF NOT EXISTS requests_pending ON requests(binding, state)')
        self.db.commit()

    def get(self, binding, rid):
        row = self.db.execute('SELECT body FROM requests WHERE binding=? AND id=?', (binding, rid)).fetchone()
        return None if row is None else json.loads(row[0])

    def put(self, binding, rid, row):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO requests VALUES (?, ?, ?, ?)',
                            (binding, rid, row['state'], json.dumps(row)))

    def pending(self, binding):
        rows = self.db.execute("SELECT body FROM requests WHERE binding=? AND state IN "
                               "('queued','dispatched','unknown')", (binding,))
        return [json.loads(row[0]) for row in rows]

    def close(self):
        self.db.close()
