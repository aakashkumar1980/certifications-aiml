"""
SQLite Database Module for Campaign AI Assistant
Loads CSV data into SQLite, provides schema introspection and safe query execution.
"""

import os
import re
import sqlite3
import pandas as pd

# Database file lives in this directory
DB_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(DB_DIR, "campaign.db")
DATA_DIR = os.path.join(os.path.dirname(DB_DIR), "data")


def init_database():
    """Load all CSV files from data/ into SQLite tables. Recreates tables each run."""
    conn = sqlite3.connect(DB_PATH)

    csv_files = {
        "campaigns": "campaigns.csv",
        "enrollments": "enrollments.csv",
        "redemptions": "redemptions.csv",
        "campaign_performance": "campaign_performance.csv",
    }

    for table_name, csv_file in csv_files.items():
        csv_path = os.path.join(DATA_DIR, csv_file)
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            df.to_sql(table_name, conn, if_exists="replace", index=False)
            print(f"Loaded {len(df)} rows into '{table_name}' table")
        else:
            print(f"Warning: {csv_path} not found, skipping '{table_name}'")

    conn.close()


def get_schema():
    """Return the full database schema as a human-readable string."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
    tables = cursor.fetchall()

    schema_parts = []
    for (table_name,) in tables:
        cursor.execute(f"PRAGMA table_info({table_name});")
        columns = cursor.fetchall()
        col_descriptions = [f"  {col[1]} ({col[2]})" for col in columns]
        schema_parts.append(f"Table: {table_name}\n" + "\n".join(col_descriptions))

        # Add sample row for context
        cursor.execute(f"SELECT * FROM {table_name} LIMIT 2;")
        rows = cursor.fetchall()
        if rows:
            col_names = [col[1] for col in columns]
            schema_parts.append(f"  Sample: {dict(zip(col_names, rows[0]))}")

    conn.close()
    return "\n\n".join(schema_parts)


def execute_query(sql):
    """
    Execute a SELECT query against the database.
    Blocks destructive operations (DROP, DELETE, UPDATE, INSERT, ALTER).
    Returns results as a list of dicts, or an error message string.
    """
    # Safety check — block destructive SQL
    dangerous_keywords = r"\b(DROP|DELETE|UPDATE|INSERT|ALTER|TRUNCATE|CREATE|REPLACE)\b"
    if re.search(dangerous_keywords, sql, re.IGNORECASE):
        return "Error: Only SELECT queries are allowed. Destructive operations are blocked."

    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(sql)
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            return "Query returned no results."

        # Convert to list of dicts for readable output
        results = [dict(row) for row in rows]
        return results

    except sqlite3.Error as e:
        return f"SQL Error: {str(e)}"
    except Exception as e:
        return f"Error executing query: {str(e)}"


if __name__ == "__main__":
    print("Initializing database...")
    init_database()
    print("\nDatabase schema:")
    print(get_schema())
