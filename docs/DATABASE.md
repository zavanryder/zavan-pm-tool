# Database Design

SQLite database stored at `data/kanban.db`. Created automatically on first startup if it doesn't exist.

## Tables

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL, UNIQUE |
| password | TEXT | NOT NULL (sha256 hash) |
| display_name | TEXT | NOT NULL, DEFAULT '' |
| created_at | TEXT | NOT NULL, DEFAULT datetime('now') |

Stores user accounts. Passwords are sha256-hashed. A default user ("user"/"password") is seeded on startup. Users can self-register.

### boards
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, FK -> users(id) |
| name | TEXT | NOT NULL, DEFAULT 'My Board' |
| created_at | TEXT | NOT NULL, DEFAULT datetime('now') |

Multiple boards per user. Users can create, rename, and delete boards.

### columns
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| board_id | INTEGER | NOT NULL, FK -> boards(id) ON DELETE CASCADE |
| title | TEXT | NOT NULL |
| position | INTEGER | NOT NULL |

Five default columns seeded per new board. Users can add and delete columns dynamically. Deleting a board cascades to its columns and cards.

### cards
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| column_id | INTEGER | NOT NULL, FK -> columns(id) ON DELETE CASCADE |
| title | TEXT | NOT NULL |
| details | TEXT | NOT NULL, DEFAULT '' |
| label | TEXT | NOT NULL, DEFAULT '' |
| due_date | TEXT | nullable |
| position | INTEGER | NOT NULL |
| created_at | TEXT | NOT NULL, DEFAULT datetime('now') |

Cards belong to a column. Label is a tag string (bug, feature, improvement, task, docs). Due date is ISO date string or null.

## Indexes

- `idx_boards_user_id` on boards(user_id)
- `idx_columns_board_id` on columns(board_id)
- `idx_cards_column_id` on cards(column_id)

## Migration approach

Tables are created with `CREATE TABLE IF NOT EXISTS` on application startup.

## Seeding

On startup, ensures default user ("user"/"password") exists. When a user creates their first board, 5 default columns are seeded (Backlog, Discovery, In Progress, Review, Done).
