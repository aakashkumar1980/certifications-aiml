"""
SQLite Database Module for Campaign Performance Analysis.

Provides three core capabilities:

1. **Initialization** — Loads CSV files from the ``database/data/`` directory into
   a SQLite database, creating one table per file.
2. **Schema Introspection** — Returns a human-readable schema string
   including column types and sample rows for LLM context injection.
3. **Safe Query Execution** — Runs SELECT-only queries with a regex-based
   guard that blocks any destructive SQL (DROP, DELETE, UPDATE, etc.).

The database file is stored at ``database/campaign.db`` relative to the
project root. All paths are resolved via ``config.settings.Settings``.

Example Usage::

    from database.campaign_db import CampaignDatabase
    db = CampaignDatabase()
    db.initialize()
    print(db.get_schema())
    results = db.execute_query("SELECT * FROM campaigns LIMIT 5")
"""

import os
import re
import sys
import sqlite3

import pandas as pd

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.settings import Settings

# Pre-compiled regex for blocking destructive SQL keywords
_DESTRUCTIVE_PATTERN = re.compile(
    r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE)\b",
    re.IGNORECASE,
)


class CampaignDatabase:
    """
    Manages the SQLite database lifecycle for campaign data.

    Encapsulates database initialization (CSV-to-SQL loading), schema
    discovery, and read-only query execution with built-in safety guards.

    Attributes:
        db_path (str): Absolute path to the SQLite database file.
        data_dir (str): Directory containing source CSV files.

    Example::

        db = CampaignDatabase()
        db.initialize()
        schema = db.get_schema()
        rows = db.execute_query("SELECT campaign_id, status FROM campaigns")
    """

    # Mapping of table names to their source CSV filenames
    CSV_TABLE_MAP = {
        "campaigns": "campaigns.csv",
        "enrollments": "enrollments.csv",
        "redemptions": "redemptions.csv",
        "campaign_performance": "campaign_performance.csv",
    }

    def __init__(self, db_path=None, data_dir=None):
        """
        Initialize the database manager.

        Args:
            db_path (str, optional): Path to the SQLite database file.
                Defaults to ``Settings.DB_PATH``.
            data_dir (str, optional): Path to the CSV data directory.
                Defaults to ``Settings.DATA_DIR``.
        """
        self.db_path = db_path or Settings.DB_PATH
        self.data_dir = data_dir or Settings.DATA_DIR

    def _connect(self):
        """
        Create a new SQLite connection to the database.

        Returns:
            sqlite3.Connection: A fresh database connection.
        """
        return sqlite3.connect(self.db_path)

    def initialize(self):
        """
        Load all CSV files into SQLite tables.

        Reads each CSV listed in ``CSV_TABLE_MAP`` from the data directory
        and writes it into the database using ``pandas.DataFrame.to_sql``
        with ``if_exists='replace'`` so the method is idempotent.

        Missing CSV files are logged as warnings but do not raise errors,
        allowing partial initialization during development.

        Returns:
            None
        """
        conn = self._connect()
        try:
            for table_name, csv_file in self.CSV_TABLE_MAP.items():
                csv_path = os.path.join(self.data_dir, csv_file)
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df.to_sql(table_name, conn, if_exists="replace", index=False)
                    print(f"  Loaded {len(df)} rows into '{table_name}' table")
                else:
                    print(f"  Warning: {csv_path} not found, skipping '{table_name}'")
        finally:
            conn.close()

    def get_schema(self):
        """
        Return the full database schema as a formatted string.

        For each table, includes the column names and types (from
        ``PRAGMA table_info``) plus one sample row for context.
        This output is designed to be injected into LLM prompts so
        the model can generate accurate SQL.

        Returns:
            str: Multi-line string describing every table, its columns,
                and a sample data row.

        Example Output::

            Table: campaigns
              campaign_id (TEXT)
              campaign_name (TEXT)
              ...
              Sample: {'campaign_id': 'CMP-001', ...}
        """
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
        tables = cursor.fetchall()

        schema_parts = []
        for (table_name,) in tables:
            # Get column definitions
            cursor.execute(f"PRAGMA table_info({table_name});")
            columns = cursor.fetchall()
            col_descriptions = [f"  {col[1]} ({col[2]})" for col in columns]
            schema_parts.append(f"Table: {table_name}\n" + "\n".join(col_descriptions))

            # Add a sample row for LLM context
            cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
            rows = cursor.fetchall()
            if rows:
                col_names = [col[1] for col in columns]
                schema_parts.append(f"  Sample: {dict(zip(col_names, rows[0]))}")

        conn.close()
        return "\n\n".join(schema_parts)

    def execute_query(self, sql):
        """
        Execute a SQL query with safety validation.

        Only SELECT statements are permitted. Any query containing
        destructive keywords (DROP, DELETE, UPDATE, INSERT, ALTER,
        TRUNCATE, CREATE, REPLACE) is rejected before execution.

        Args:
            sql (str): The SQL query string to execute. Must be a
                SELECT statement.

        Returns:
            list[dict] | str: On success, a list of dictionaries where
                each dict represents a row with column-name keys.
                On failure or empty results, returns a descriptive
                error/info string.

        Example::

            results = db.execute_query("SELECT COUNT(*) as cnt FROM campaigns")
            # [{'cnt': 5}]

            results = db.execute_query("DROP TABLE campaigns")
            # "Error: Only SELECT queries are allowed. Destructive operations are blocked."
        """
        # Safety guard — reject destructive operations
        if _DESTRUCTIVE_PATTERN.search(sql):
            return "Error: Only SELECT queries are allowed. Destructive operations are blocked."

        try:
            conn = self._connect()
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(sql)
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                return "Query returned no results."

            return [dict(row) for row in rows]

        except sqlite3.Error as e:
            return f"SQL Error: {str(e)}"
        except Exception as e:
            return f"Error executing query: {str(e)}"


# --- Module-Level Convenience Functions ---
# These allow simple imports: from database.campaign_db import get_schema, execute_query

_default_db = CampaignDatabase()


def init_database():
    """Initialize the database using default settings. See ``CampaignDatabase.initialize``."""
    _default_db.initialize()


def get_schema():
    """Return the database schema string. See ``CampaignDatabase.get_schema``."""
    return _default_db.get_schema()


def execute_query(sql):
    """Execute a safe SELECT query. See ``CampaignDatabase.execute_query``."""
    return _default_db.execute_query(sql)


# --- Script Entry Point ---
if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("\nDatabase schema:")
    print(get_schema())
