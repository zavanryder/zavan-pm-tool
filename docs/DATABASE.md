# Database Design

SQLite database stored at `data/kanban.db`. Created automatically on first startup if it doesn't exist.

## Tables

### users
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| username | TEXT | NOT NULL, UNIQUE |
| password_hash | TEXT | NOT NULL |

Stores user accounts. For the MVP, a single user ("user") is seeded on startup. The password_hash column stores plain text for the MVP but the schema supports hashing for future.

### boards
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| user_id | INTEGER | NOT NULL, FK -> users(id) |
| name | TEXT | NOT NULL, DEFAULT 'My Board' |

One board per user for the MVP. The schema supports multiple boards per user for future.

### columns
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| board_id | INTEGER | NOT NULL, FK -> boards(id) |
| title | TEXT | NOT NULL |
| position | INTEGER | NOT NULL |

Five columns seeded per board: Backlog (0), Discovery (1), In Progress (2), Review (3), Done (4). Position determines display order.

### cards
| Column | Type | Constraints |
|--------|------|-------------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT |
| column_id | INTEGER | NOT NULL, FK -> columns(id) |
| title | TEXT | NOT NULL |
| details | TEXT | NOT NULL, DEFAULT '' |
| position | INTEGER | NOT NULL |

Cards belong to a column. Position determines order within the column. Moving a card changes its column_id and position.

## Indexes

- `idx_boards_user_id` on boards(user_id)
- `idx_columns_board_id` on columns(board_id)
- `idx_cards_column_id` on cards(column_id)

## Migration approach

Tables are created with `CREATE TABLE IF NOT EXISTS` on application startup. No migration framework needed for the MVP.

## Seeding

On first login, if the user has no board:
1. Create a board for the user
2. Create 5 default columns (Backlog, Discovery, In Progress, Review, Done)
