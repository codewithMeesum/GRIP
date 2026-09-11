import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path


DB_PATH = Path(
    os.getenv(
        "GRIP_DB_PATH",
        "grip.db",
    )
)


# =========================================================
# CONNECTION
# =========================================================
def connect():
    connection = sqlite3.connect(
        DB_PATH,
        check_same_thread=False,
    )

    connection.row_factory = sqlite3.Row

    return connection


# =========================================================
# INITIALIZE DATABASE
# =========================================================
def init_db():

    with connect() as con:

        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                category TEXT NOT NULL,
                location TEXT NOT NULL,
                description TEXT NOT NULL,
                image_bytes BLOB,
                image_mime TEXT,
                ai_analysis TEXT NOT NULL DEFAULT '{}',
                status TEXT NOT NULL DEFAULT 'Reported',
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id INTEGER NOT NULL,
                author TEXT NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(report_id)
                    REFERENCES reports(id)
            );
            """
        )

        # Compatibility with an older version of the database.
        columns = {
            row["name"]
            for row in con.execute(
                "PRAGMA table_info(reports)"
            ).fetchall()
        }

        if "image_bytes" not in columns:
            con.execute(
                "ALTER TABLE reports ADD COLUMN image_bytes BLOB"
            )

        if "image_mime" not in columns:
            con.execute(
                "ALTER TABLE reports ADD COLUMN image_mime TEXT"
            )

        if "ai_analysis" not in columns:
            con.execute(
                """
                ALTER TABLE reports
                ADD COLUMN ai_analysis TEXT
                NOT NULL DEFAULT '{}'
                """
            )


# =========================================================
# DEMO DATA
# =========================================================
def seed_demo_data():

    with connect() as con:

        count = con.execute(
            "SELECT COUNT(*) FROM reports"
        ).fetchone()[0]

        if count:
            return

        now = datetime.now().strftime(
            "%Y-%m-%d %H:%M"
        )

        samples = [

            (
                "Waste dumped beside a stream",
                "Waste",
                "Skardu, Gilgit-Baltistan",
                (
                    "Mixed household waste has accumulated "
                    "near a stream used by nearby communities."
                ),
                {
                    "category": "Waste",
                    "summary": (
                        "Solid waste accumulation has been "
                        "reported near a waterway."
                    ),
                    "priority": "High",
                    "possible_causes": [
                        "Improper disposal",
                        "Insufficient waste collection",
                    ],
                    "next_actions": [
                        "Verify the site and document the affected area",
                        "Refer to a suitable local waste-management organization",
                        "Record conditions before and after any intervention",
                    ],
                },
                "Verified",
            ),

            (
                "Blocked drainage channel after heavy rain",
                "Water",
                "Gilgit, Gilgit-Baltistan",
                (
                    "A drainage channel is blocked by debris, "
                    "increasing the risk of standing water and overflow."
                ),
                {
                    "category": "Water",
                    "summary": (
                        "A blocked channel may restrict "
                        "stormwater flow."
                    ),
                    "priority": "Medium",
                    "possible_causes": [
                        "Debris accumulation",
                        "Inadequate maintenance",
                    ],
                    "next_actions": [
                        "Inspect and document the blockage",
                        "Refer the issue to the appropriate local authority or maintenance team",
                        "Compare conditions before and after clearing",
                    ],
                },
                "Action Required",
            ),

            (
                "Open burning near a residential area",
                "Air",
                "Hunza, Gilgit-Baltistan",
                (
                    "Smoke from open burning was reported "
                    "close to a residential area."
                ),
                {
                    "category": "Air",
                    "summary": (
                        "Open burning is generating localized smoke."
                    ),
                    "priority": "High",
                    "possible_causes": [
                        "Waste burning",
                        "Limited disposal options",
                    ],
                    "next_actions": [
                        "Document timing and location",
                        "Discourage unsafe open burning",
                        "Refer the issue to an appropriate local organization",
                    ],
                },
                "Reported",
            ),
        ]

        for (
            title,
            category,
            location,
            description,
            ai,
            status,
        ) in samples:

            con.execute(
                """
                INSERT INTO reports(
                    title,
                    category,
                    location,
                    description,
                    image_bytes,
                    image_mime,
                    ai_analysis,
                    status,
                    created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    title,
                    category,
                    location,
                    description,
                    None,
                    None,
                    json.dumps(
                        ai,
                        ensure_ascii=False,
                    ),
                    status,
                    now,
                ),
            )


# =========================================================
# CREATE REPORT
# =========================================================
def create_report(
    title,
    category,
    location,
    description,
    image_bytes=None,
    mime_type=None,
    ai_analysis=None,
):

    with connect() as con:

        cursor = con.execute(
            """
            INSERT INTO reports(
                title,
                category,
                location,
                description,
                image_bytes,
                image_mime,
                ai_analysis,
                status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                title,
                category,
                location,
                description,
                image_bytes,
                mime_type,
                json.dumps(
                    ai_analysis or {},
                    ensure_ascii=False,
                ),
                "Reported",
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
            ),
        )

        return cursor.lastrowid


# =========================================================
# ROW CONVERTER
# =========================================================
def _row_to_dict(row):

    data = dict(row)

    try:
        data["ai_analysis"] = json.loads(
            data.get(
                "ai_analysis",
                "{}",
            )
            or "{}"
        )

    except (
        json.JSONDecodeError,
        TypeError,
    ):
        data["ai_analysis"] = {}

    return data


# =========================================================
# LIST REPORTS
# =========================================================
def list_reports():

    with connect() as con:

        rows = con.execute(
            """
            SELECT *
            FROM reports
            ORDER BY id DESC
            """
        ).fetchall()

    return [
        _row_to_dict(row)
        for row in rows
    ]


# =========================================================
# GET ONE REPORT
# =========================================================
def get_report(report_id):

    if report_id is None:
        return None

    with connect() as con:

        row = con.execute(
            """
            SELECT *
            FROM reports
            WHERE id = ?
            """,
            (report_id,),
        ).fetchone()

    if not row:
        return None

    return _row_to_dict(row)


# =========================================================
# UPDATE STATUS
# =========================================================
def update_status(
    report_id,
    status,
):

    with connect() as con:

        con.execute(
            """
            UPDATE reports
            SET status = ?
            WHERE id = ?
            """,
            (
                status,
                report_id,
            ),
        )


# =========================================================
# ADD COMMENT
# =========================================================
def add_comment(
    report_id,
    author,
    comment,
):

    with connect() as con:

        con.execute(
            """
            INSERT INTO comments(
                report_id,
                author,
                comment,
                created_at
            )
            VALUES (?, ?, ?, ?)
            """,
            (
                report_id,
                author,
                comment,
                datetime.now().strftime(
                    "%Y-%m-%d %H:%M"
                ),
            ),
        )


# =========================================================
# LIST COMMENTS
# =========================================================
def list_comments(report_id):

    with connect() as con:

        rows = con.execute(
            """
            SELECT *
            FROM comments
            WHERE report_id = ?
            ORDER BY id ASC
            """,
            (report_id,),
        ).fetchall()

    return [
        dict(row)
        for row in rows
    ]
