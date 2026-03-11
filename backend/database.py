import sqlite3
from pathlib import Path
from hashlib import sha256

DB_PATH = Path(__file__).parent / "data" / "kanban.db"

DEFAULT_COLUMNS = ["Backlog", "Discovery", "In Progress", "Review", "Done"]


def hash_password(password: str) -> str:
    return sha256(password.encode()).hexdigest()


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
                password TEXT NOT NULL,
                display_name TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE TABLE IF NOT EXISTS boards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL REFERENCES users(id),
                name TEXT NOT NULL DEFAULT 'My Board',
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_boards_user_id ON boards(user_id);
            CREATE TABLE IF NOT EXISTS columns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                board_id INTEGER NOT NULL REFERENCES boards(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                position INTEGER NOT NULL
            );
            CREATE INDEX IF NOT EXISTS idx_columns_board_id ON columns(board_id);
            CREATE TABLE IF NOT EXISTS cards (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                column_id INTEGER NOT NULL REFERENCES columns(id) ON DELETE CASCADE,
                title TEXT NOT NULL,
                details TEXT NOT NULL DEFAULT '',
                label TEXT NOT NULL DEFAULT '',
                due_date TEXT,
                position INTEGER NOT NULL,
                created_at TEXT NOT NULL DEFAULT (datetime('now'))
            );
            CREATE INDEX IF NOT EXISTS idx_cards_column_id ON cards(column_id);
        """
        )
    finally:
        conn.close()


# --- User management ---

def create_user(username: str, password: str, display_name: str = "") -> int | None:
    conn = get_conn()
    try:
        existing = conn.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
        if existing:
            return None
        cur = conn.execute(
            "INSERT INTO users (username, password, display_name) VALUES (?, ?, ?)",
            (username, hash_password(password), display_name or username),
        )
        user_id = cur.lastrowid
        conn.commit()
        return user_id
    finally:
        conn.close()


def verify_user(username: str, password: str) -> int | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, password FROM users WHERE username = ?", (username,)
        ).fetchone()
        if not row:
            return None
        if row["password"] != hash_password(password):
            return None
        return row["id"]
    finally:
        conn.close()


def ensure_user(username: str, password: str) -> int:
    """Legacy helper: get or create user (used for seeding)."""
    uid = verify_user(username, password)
    if uid:
        return uid
    new_id = create_user(username, password)
    if new_id:
        return new_id
    # Race: user was just created, try verify again
    return verify_user(username, password) or 0


def get_user_by_id(user_id: int) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id, username, display_name, created_at FROM users WHERE id = ?",
            (user_id,),
        ).fetchone()
        if not row:
            return None
        return dict(row)
    finally:
        conn.close()


def update_user_profile(user_id: int, display_name: str | None = None) -> bool:
    conn = get_conn()
    try:
        if display_name is not None:
            conn.execute("UPDATE users SET display_name = ? WHERE id = ?", (display_name, user_id))
            conn.commit()
        return True
    finally:
        conn.close()


def change_password(user_id: int, old_password: str, new_password: str) -> bool:
    conn = get_conn()
    try:
        row = conn.execute("SELECT password FROM users WHERE id = ?", (user_id,)).fetchone()
        if not row or row["password"] != hash_password(old_password):
            return False
        conn.execute("UPDATE users SET password = ? WHERE id = ?", (hash_password(new_password), user_id))
        conn.commit()
        return True
    finally:
        conn.close()


# --- Board management ---

def create_board(user_id: int, name: str = "My Board") -> int:
    conn = get_conn()
    try:
        cur = conn.execute("INSERT INTO boards (user_id, name) VALUES (?, ?)", (user_id, name))
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


def list_boards(user_id: int) -> list[dict]:
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT id, name, created_at FROM boards WHERE user_id = ? ORDER BY created_at",
            (user_id,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def rename_board(board_id: int, name: str, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?", (board_id, user_id)
        ).fetchone()
        if not row:
            return False
        conn.execute("UPDATE boards SET name = ? WHERE id = ?", (name, board_id))
        conn.commit()
        return True
    finally:
        conn.close()


def delete_board(board_id: int, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?", (board_id, user_id)
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM boards WHERE id = ?", (board_id,))
        conn.commit()
        return True
    finally:
        conn.close()


def ensure_board(user_id: int) -> int:
    """Legacy helper: get first board or create default."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT id FROM boards WHERE user_id = ?", (user_id,)).fetchone()
        if row:
            return row["id"]
    finally:
        conn.close()
    return create_board(user_id)


def get_board(board_id: int, user_id: int) -> dict | None:
    conn = get_conn()
    try:
        board_row = conn.execute(
            "SELECT id, name FROM boards WHERE id = ? AND user_id = ?", (board_id, user_id)
        ).fetchone()
        if not board_row:
            return None

        rows = conn.execute(
            """
            SELECT
                co.id AS column_id,
                co.title AS column_title,
                co.position AS column_position,
                ca.id AS card_id,
                ca.title AS card_title,
                ca.details AS card_details,
                ca.label AS card_label,
                ca.due_date AS card_due_date,
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
                        "label": row["card_label"],
                        "due_date": row["card_due_date"],
                    }
                )

        return {"id": board_id, "name": board_row["name"], "columns": columns}
    finally:
        conn.close()


def get_default_board(user_id: int) -> dict:
    """Get first board for user, creating one if needed. Legacy compat."""
    board_id = ensure_board(user_id)
    result = get_board(board_id, user_id)
    return result or {"id": board_id, "name": "My Board", "columns": []}


# --- Column management ---

def add_column(board_id: int, title: str, user_id: int) -> dict | None:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT id FROM boards WHERE id = ? AND user_id = ?", (board_id, user_id)
        ).fetchone()
        if not row:
            return None
        max_pos = conn.execute(
            "SELECT COALESCE(MAX(position), -1) as mp FROM columns WHERE board_id = ?",
            (board_id,),
        ).fetchone()["mp"]
        cur = conn.execute(
            "INSERT INTO columns (board_id, title, position) VALUES (?, ?, ?)",
            (board_id, title, max_pos + 1),
        )
        conn.commit()
        return {"id": cur.lastrowid, "title": title, "position": max_pos + 1, "cards": []}
    finally:
        conn.close()


def delete_column(column_id: int, user_id: int) -> bool:
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT c.id, c.board_id, c.position FROM columns c JOIN boards b ON c.board_id = b.id WHERE c.id = ? AND b.user_id = ?",
            (column_id, user_id),
        ).fetchone()
        if not row:
            return False
        conn.execute("DELETE FROM columns WHERE id = ?", (column_id,))
        conn.execute(
            "UPDATE columns SET position = position - 1 WHERE board_id = ? AND position > ?",
            (row["board_id"], row["position"]),
        )
        conn.commit()
        return True
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


# --- Card management ---

def create_card(column_id: int, title: str, details: str, user_id: int, label: str = "", due_date: str | None = None) -> dict | None:
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
            "INSERT INTO cards (column_id, title, details, label, due_date, position) VALUES (?, ?, ?, ?, ?, ?)",
            (column_id, title, details, label, due_date, max_pos + 1),
        )
        card_id = cur.lastrowid
        conn.commit()
        return {"id": card_id, "title": title, "details": details, "label": label, "due_date": due_date}
    finally:
        conn.close()


def update_card(card_id: int, title: str | None, details: str | None, user_id: int, label: str | None = None, due_date: str | None = "UNSET") -> bool:
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
        if label is not None:
            conn.execute("UPDATE cards SET label = ? WHERE id = ?", (label, card_id))
        if due_date != "UNSET":
            conn.execute("UPDATE cards SET due_date = ? WHERE id = ?", (due_date, card_id))
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


def search_cards(user_id: int, query: str, board_id: int | None = None) -> list[dict]:
    conn = get_conn()
    try:
        sql = """
            SELECT ca.id, ca.title, ca.details, ca.label, ca.due_date,
                   co.title AS column_title, b.name AS board_name, b.id AS board_id
            FROM cards ca
            JOIN columns co ON ca.column_id = co.id
            JOIN boards b ON co.board_id = b.id
            WHERE b.user_id = ? AND (ca.title LIKE ? OR ca.details LIKE ?)
        """
        params: list = [user_id, f"%{query}%", f"%{query}%"]
        if board_id is not None:
            sql += " AND b.id = ?"
            params.append(board_id)
        sql += " ORDER BY ca.title LIMIT 50"
        rows = conn.execute(sql, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()
