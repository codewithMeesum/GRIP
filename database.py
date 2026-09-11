"""SQLite repository. Short-lived connections, transactions, image BLOBs."""
from contextlib import contextmanager
import json
import os
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from uuid import uuid4
from prompts import Analysis, Innovation, CATEGORIES, STATUSES
from utils import clean_text, utcnow


def db_path() -> Path:
    return Path(os.environ.get("GRIP_DB_PATH", str(Path(__file__).parent / "data" / "grip.db")))


@contextmanager
def connect():
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path, timeout=15)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys=ON")
    conn.execute("PRAGMA busy_timeout=15000")
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db() -> None:
    with connect() as conn:
        conn.execute("PRAGMA journal_mode=WAL")
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL, description TEXT NOT NULL,
            category TEXT NOT NULL, location TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'Reported',
            image BLOB, thumbnail BLOB, analysis TEXT NOT NULL,
            is_demo INTEGER NOT NULL DEFAULT 0,
            created_at TEXT NOT NULL, updated_at TEXT NOT NULL,
            submission_token TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS comments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            author TEXT NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL,
            submission_token TEXT UNIQUE NOT NULL
        );
        CREATE TABLE IF NOT EXISTS status_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            status TEXT NOT NULL, actor TEXT NOT NULL, note TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS votes (
            report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            session_id TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (report_id, session_id)
        );
        CREATE TABLE IF NOT EXISTS innovations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            report_id INTEGER NOT NULL REFERENCES reports(id) ON DELETE CASCADE,
            content TEXT NOT NULL, constraints_text TEXT NOT NULL,
            created_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS comments_report ON comments(report_id);
        CREATE INDEX IF NOT EXISTS events_report ON status_events(report_id);
        CREATE INDEX IF NOT EXISTS innovations_report ON innovations(report_id);
        CREATE INDEX IF NOT EXISTS reports_created ON reports(created_at DESC);
        """)


def validate_report(title: str, description: str, category: str, location: str) -> dict:
    if category not in CATEGORIES:
        raise ValueError("Choose an environmental category.")
    return {
        "title": clean_text(title, "Title", 8, 140),
        "description": clean_text(description, "Description", 30, 4000),
        "category": category,
        "location": clean_text(location, "Location", 3, 180),
    }


def validate_envelope(envelope: dict, schema) -> str:
    schema.model_validate(envelope["data"])
    if envelope.get("source") not in {"Gemini", "Local guidance"}:
        raise ValueError("Unknown analysis source")
    return json.dumps(envelope, ensure_ascii=False)


def create_report(report: dict, analysis: dict, image: bytes | None = None,
                  thumbnail: bytes | None = None, token: str | None = None) -> int:
    values = validate_report(**{k: report[k] for k in ("title", "description", "category", "location")})
    encoded = validate_envelope(analysis, Analysis)
    now = utcnow()
    token = token or str(uuid4())
    with connect() as conn:
        conn.execute("""INSERT INTO reports
            (title, description, category, location, image, thumbnail, analysis,
             created_at, updated_at, submission_token)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(submission_token) DO NOTHING""",
            (*values.values(), image, thumbnail, encoded, now, now, token))
        row = conn.execute("SELECT id FROM reports WHERE submission_token=?", (token,)).fetchone()
        report_id = row["id"]
        if not conn.execute("SELECT 1 FROM status_events WHERE report_id=?", (report_id,)).fetchone():
            conn.execute("""INSERT INTO status_events (report_id,status,actor,note,created_at)
                VALUES (?, 'Reported', 'Community member', 'Report submitted for community review.', ?)""",
                (report_id, now))
        return report_id


def list_reports(search: str = "", category: str = "All categories",
                 status: str = "All statuses", sort: str = "Newest",
                 include_demo: bool = True) -> list[dict]:
    # Deliberately omit full images from feed queries.
    query = """SELECT r.id,r.title,r.description,r.category,r.location,r.status,
        r.thumbnail,r.analysis,r.is_demo,r.created_at,r.updated_at,
        (SELECT COUNT(*) FROM comments c WHERE c.report_id=r.id) AS comment_count,
        (SELECT COUNT(*) FROM votes v WHERE v.report_id=r.id) AS vote_count
        FROM reports r WHERE 1=1"""
    args = []
    if search.strip():
        query += " AND (instr(lower(r.title),lower(?)) OR instr(lower(r.description),lower(?)) OR instr(lower(r.location),lower(?)))"
        args.extend([search.strip()] * 3)
    if category != "All categories":
        query += " AND r.category=?"
        args.append(category)
    if status != "All statuses":
        query += " AND r.status=?"
        args.append(status)
    if not include_demo:
        query += " AND r.is_demo=0"
    query += " ORDER BY " + ("vote_count DESC, " if sort == "Most supported" else "") + "r.created_at DESC, r.id DESC"
    with connect() as conn:
        return [dict(row) for row in conn.execute(query, args)]


def get_report(report_id: int) -> dict | None:
    with connect() as conn:
        row = conn.execute("SELECT * FROM reports WHERE id=?", (report_id,)).fetchone()
    if row is None:
        return None
    report = dict(row)
    report["analysis"] = json.loads(report["analysis"])
    return report


def save_analysis(report_id: int, analysis: dict) -> None:
    encoded = validate_envelope(analysis, Analysis)
    with connect() as conn:
        conn.execute("UPDATE reports SET analysis=?, updated_at=? WHERE id=?", (encoded, utcnow(), report_id))


def comments(report_id: int) -> list[dict]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM comments WHERE report_id=? ORDER BY created_at,id", (report_id,))]


def add_comment(report_id: int, author: str, body: str, token: str | None = None) -> None:
    author = clean_text(author, "Display name", 2, 60)
    body = clean_text(body, "Comment", 3, 1500)
    with connect() as conn:
        conn.execute("""INSERT INTO comments (report_id,author,body,created_at,submission_token)
            VALUES (?,?,?,?,?) ON CONFLICT(submission_token) DO NOTHING""",
            (report_id, author, body, utcnow(), token or str(uuid4())))


def history(report_id: int) -> list[dict]:
    with connect() as conn:
        return [dict(row) for row in conn.execute(
            "SELECT * FROM status_events WHERE report_id=? ORDER BY created_at,id", (report_id,))]


def advance_status(report_id: int, expected: str, actor: str, note: str) -> str:
    actor = clean_text(actor, "Display name", 2, 60)
    note = clean_text(note, "Evidence or progress note", 10, 1200)
    if expected not in STATUSES or expected == STATUSES[-1]:
        raise ValueError("This report has no next status.")
    next_status = STATUSES[STATUSES.index(expected) + 1]
    now = utcnow()
    with connect() as conn:
        result = conn.execute("UPDATE reports SET status=?,updated_at=? WHERE id=? AND status=?",
                              (next_status, now, report_id, expected))
        if result.rowcount != 1:
            raise ValueError("This report changed in another session. Refresh before updating it.")
        conn.execute("INSERT INTO status_events (report_id,status,actor,note,created_at) VALUES (?,?,?,?,?)",
                     (report_id, next_status, actor, note, now))
    return next_status


def supported_ids(session_id: str) -> set[int]:
    with connect() as conn:
        return {row[0] for row in conn.execute("SELECT report_id FROM votes WHERE session_id=?", (session_id,))}


def toggle_support(report_id: int, session_id: str) -> None:
    with connect() as conn:
        conn.execute("BEGIN IMMEDIATE")
        found = conn.execute("SELECT 1 FROM votes WHERE report_id=? AND session_id=?", (report_id, session_id)).fetchone()
        if found:
            conn.execute("DELETE FROM votes WHERE report_id=? AND session_id=?", (report_id, session_id))
        else:
            conn.execute("INSERT INTO votes VALUES (?,?,?)", (report_id, session_id, utcnow()))


def save_innovation(report_id: int, envelope: dict, constraints: str) -> None:
    encoded = validate_envelope(envelope, Innovation)
    with connect() as conn:
        conn.execute("INSERT INTO innovations (report_id,content,constraints_text,created_at) VALUES (?,?,?,?)",
                     (report_id, encoded, constraints, utcnow()))


def get_innovations(report_id: int) -> list[dict]:
    with connect() as conn:
        rows = conn.execute("SELECT * FROM innovations WHERE report_id=? ORDER BY id DESC", (report_id,)).fetchall()
    return [dict(row) | {"content": json.loads(row["content"])} for row in rows]


def dashboard_data(include_demo: bool = True) -> dict:
    where = "" if include_demo else "WHERE r.is_demo=0"
    with connect() as conn:
        counts = {}
        for table in ("comments", "votes", "innovations"):
            counts[table] = conn.execute(
                f"SELECT COUNT(*) FROM {table} x JOIN reports r ON r.id=x.report_id {where}"
            ).fetchone()[0]
        counts["activity"] = [dict(row) for row in conn.execute(f"""
            SELECT r.title,e.status,e.note,e.created_at FROM status_events e
            JOIN reports r ON r.id=e.report_id {where} ORDER BY e.created_at DESC,e.id DESC LIMIT 8
        """)]
    return counts


def backup_bytes() -> bytes:
    """Consistent online snapshot including rows currently in the WAL file."""
    with TemporaryDirectory(prefix="grip-backup-") as directory, connect() as source:
        snapshot = Path(directory) / "backup.db"
        target = sqlite3.connect(snapshot)
        try:
            source.backup(target)
            # A standalone file must not depend on an external WAL sidecar.
            target.execute("PRAGMA journal_mode=DELETE")
        finally:
            target.close()
        return snapshot.read_bytes()
