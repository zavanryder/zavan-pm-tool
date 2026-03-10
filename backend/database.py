import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "kanban.db"

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def get_conn() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL DEFAULT 'My Board'
            );
            CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL REFERENCES boards(id),
                title TEXT NOT NULL,
                position INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL REFERENCES columns(id),
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                position INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
        """
        )
    finally:
        conn.close()


def ensure_user(username: str, password: str) -> int:
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username, password),
        )
        user_id = cur.lastrowid
        conn.commit()
        return user_id
    finally:
        conn.close()


def ensure_board(user_id: int) -> int:
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return row["id"]
        cur = conn.execute("INSERT INTO boards (user_id, name) VALUES (?, 'My Board')", (user_id,))
        board_id = cur.lastrowid
        for i, title in enumerate(DEFAULT_COLUMNS):
            conn.execute(
                "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
                (board_id, title, i),
            )
        conn.commit()
        return board_id
    finally:
        conn.close()


def get_board(user_id: int) -> dict:
    board_id = ensure_board(user_id)
    conn = get_conn()
    try:
        rows = conn.execute(
            """
            SELECT
                co.id AS column_id,
                co.title AS column_title,
                co.position AS column_position,
                ca.id AS card_id,
                ca.title AS card_title,
                ca.details AS card_details,
                ca.position AS card_position
            FROM columns co
            LEFT JOIN cards ca ON ca.column_id = co.id
            WHERE co.board_id = ?
            ORDER BY co.position, ca.position
            """,
            (board_id,),
        ).fetchall()

        columns: list[dict] = []
        by_column_id: dict[int, dict] = {}
        for row in rows:
            column_id = row["column_id"]
            if column_id not in by_column_id:
                col = {
                    "id": column_id,
                    "title": row["column_title"],
                    "position": row["column_position"],
                    "cards": [],
                }
                by_column_id[column_id] = col
                columns.append(col)

            if row["card_id"] is not None:
                by_column_id[column_id]["cards"].append(
                    {
                        "id": row["card_id"],
                        "title": row["card_title"],
                        "details": row["card_details"],
                    }
                )

        return {"id": board_id, "columns": columns}
    finally:
        conn.close()


def rename_column(column_id: int, title: str, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
            (column_id, user_id),
        ).fetchone()
        if not row:
            return False
        conn.execute("UPDATE columns SET title = ? WHERE id = ?", (title, column_id))
        conn.commit()
        return True
    finally:
        conn.close()


def create_card(column_id: int, title: str, details: str, user_id: int) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT c.id FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
            (column_id, user_id),
        ).fetchone()
        if not row:
            return None
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) as mp FROM cards WHERE column_id = ?",
            (column_id,),
        ).fetchone()["mp"]
        cur = conn.execute(
            "INSERT INTO cards (column_id, title, details, position) VALUES (?, ?, ?, ?)",
            (column_id, title, details, max_pos + 1),
        )
        card_id = cur.lastrowid
        conn.commit()
        return {"id": card_id, "title": title, "details": details}
    finally:
        conn.close()


def update_card(card_id: int, title: str | None, details: str | None, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT ca.id FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
            (card_id, user_id),
        ).fetchone()
        if not row:
            return False
        if title is not None:
            conn.execute("UPDATE cards SET title = ? WHERE id = ?", (title, card_id))
        if details is not None:
            conn.execute("UPDATE cards SET details = ? WHERE id = ?", (details, card_id))
        conn.commit()
        return True
    finally:
        conn.close()


def delete_card(card_id: int, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT ca.id, ca.column_id, ca.position FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
            (card_id, user_id),
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM cards WHERE id = ?", (card_id,))
        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (row["column_id"], row["position"]),
        )
        conn.commit()
        return True
    finally:
        conn.close()


def move_card(card_id: int, target_column_id: int, position: int, user_id: int) -> bool:
    if position < 0:
        raise ValueError("Position must be >= 0")

    conn = get_conn()
    try:
        card = conn.execute(
            "SELECT ca.id, ca.column_id, ca.position FROM cards ca JOIN columns co ON ca.column_id = co.id JOIN boards b ON co.board_id = b.id WHERE ca.id = ? AND b.user_id = ?",
            (card_id, user_id),
        ).fetchone()
        if not card:
            return False

        target_col = conn.execute(
            "SELECT co.id FROM columns co JOIN boards b ON co.board_id = b.id WHERE co.id = ? AND b.user_id = ?",
            (target_column_id, user_id),
        ).fetchone()
        if not target_col:
            return False

        old_col_id = card["column_id"]
        old_pos = card["position"]

        target_count = conn.execute(
            "SELECT COUNT(*) AS c FROM cards WHERE column_id = ?",
            (target_column_id,),
        ).fetchone()["c"]

        if target_column_id == old_col_id:
            target_count -= 1

        normalized_pos = min(position, target_count)

        conn.execute(
            "UPDATE cards SET position = position - 1 WHERE column_id = ? AND position > ?",
            (old_col_id, old_pos),
        )

        conn.execute(
            "UPDATE cards SET position = position + 1 WHERE column_id = ? AND position >= ?",
            (target_column_id, normalized_pos),
        )
        conn.execute(
            "UPDATE cards SET column_id = ?, position = ? WHERE id = ?",
            (target_column_id, normalized_pos, card_id),
        )
        conn.commit()
        return True
    finally:
        conn.close()
