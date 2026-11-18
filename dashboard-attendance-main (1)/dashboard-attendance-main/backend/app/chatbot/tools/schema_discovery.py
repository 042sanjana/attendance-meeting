
from app.chatbot.tools.sql_executor import (
    get_connection,
    MODULE_TABLES,
)


def get_module_schema(module: str) -> str:
    if module not in MODULE_TABLES:
        raise ValueError(f"Unknown module: {module}")

    allowed_tables = MODULE_TABLES[module]
    conn = get_connection(module)

    try:
        output = []

        for table in allowed_tables:
            exists = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = ?
                """,
                (table,)
            ).fetchone()

            if not exists:
                continue

            columns = conn.execute(
                f'PRAGMA table_info("{table}")'
            ).fetchall()

            column_text = ", ".join(
                f"{row['name']} ({row['type']})"
                for row in columns
            )

            output.append(
                f"TABLE {table}: {column_text}"
            )

        return "\n".join(output) or (
            f"No recognized tables found for {module}."
        )

    finally:
        conn.close()
