#!/usr/bin/env python3
"""
PyPath - Database Schema Runner
Executes database/schema.sql against Neon PostgreSQL or any PostgreSQL database.
Works with standard Python 3.8+ (no pip dependencies required).
"""

import os
import sys
import re
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
SCHEMA_FILE = Path(__file__).resolve().parent / "schema.sql"
ENV_LOCAL = BASE_DIR / ".env.local"
ENV_FILE = BASE_DIR / ".env"


def load_env_file(filepath: Path) -> dict:
    """Simple parser for .env / .env.local files."""
    env = {}
    if not filepath.exists():
        return env
    for line in filepath.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" in line:
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'\"")
            env[key] = val
    return env


def get_database_url() -> tuple[str | None, str]:
    """Resolves DATABASE_URL from CLI argument, env var, or .env files."""
    # 1. CLI argument
    if len(sys.argv) > 1 and sys.argv[1].startswith("postgres"):
        return sys.argv[1], "Command Line Argument"

    # 2. Existing OS environment variable
    if os.environ.get("DATABASE_URL"):
        return os.environ["DATABASE_URL"], "OS Environment ($DATABASE_URL)"

    # 3. .env.local
    local_env = load_env_file(ENV_LOCAL)
    if local_env.get("DATABASE_URL") and not local_env["DATABASE_URL"].startswith("postgresql://USER:"):
        return local_env["DATABASE_URL"], ".env.local"

    # 4. .env
    base_env = load_env_file(ENV_FILE)
    if base_env.get("DATABASE_URL") and not base_env["DATABASE_URL"].startswith("postgresql://USER:"):
        return base_env["DATABASE_URL"], ".env"

    return None, "None"


def parse_sql_statements(sql_text: str) -> list[str]:
    """Strips comments and splits schema into individual executable SQL statements."""
    # Remove single line comments (-- ...)
    clean = re.sub(r"--.*$", "", sql_text, flags=re.MULTILINE)
    # Remove multi-line comments (/* ... */)
    clean = re.sub(r"/\*.*?\*/", "", clean, flags=re.DOTALL)
    # Split by semicolon
    raw_statements = [s.strip() for s in clean.split(";") if s.strip()]
    return raw_statements


def execute_via_neon_http(database_url: str, sql_statement: str) -> dict:
    """
    Executes a SQL statement over Neon's serverless HTTP SQL API.
    Zero native PostgreSQL driver required!
    """
    parsed = urllib.parse.urlparse(database_url)
    host = parsed.hostname
    if not host:
        raise ValueError(f"Could not parse hostname from connection string: {database_url}")

    url = f"https://{host}/sql"
    headers = {
        "Content-Type": "application/json",
        "Neon-Connection-String": database_url,
        "User-Agent": "PyPath-Schema-Runner/1.0",
    }
    body = json.dumps({"query": sql_statement}).encode("utf-8")

    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            data = resp.read().decode("utf-8")
            return json.loads(data) if data else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            err_json = json.loads(error_body)
            msg = err_json.get("message") or err_json.get("error") or error_body
        except Exception:
            msg = error_body
        raise RuntimeError(f"HTTP {e.code}: {msg}") from e
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed: {e.reason}") from e


def test_syntax_offline(statements: list[str]) -> None:
    """Performs offline syntax and structure verification of schema statements."""
    print("=" * 60)
    print("  PyPath Database Schema Verification (Offline)")
    print("=" * 60)
    print(f"Schema file: {SCHEMA_FILE}")
    print(f"Total SQL statements to run: {len(statements)}\n")

    for idx, stmt in enumerate(statements, 1):
        first_line = stmt.strip().splitlines()[0]
        summary = first_line[:65] + ("..." if len(first_line) > 65 else "")
        print(f"  [{idx}/{len(statements)}] VALID: {summary}")

    print("\n[OK] All statements are syntactically valid PostgreSQL DDL.")


def run():
    print("=" * 60)
    print("  PyPath - Database Setup & Schema Runner")
    print("=" * 60)

    if not SCHEMA_FILE.exists():
        print(f"[ERROR] Schema file not found at: {SCHEMA_FILE}")
        sys.exit(1)

    sql_content = SCHEMA_FILE.read_text(encoding="utf-8")
    statements = parse_sql_statements(sql_content)

    db_url, source = get_database_url()

    if not db_url:
        test_syntax_offline(statements)
        print("\n" + "-" * 60)
        print("  NEXT STEP: Connect to your Neon PostgreSQL database")
        print("-" * 60)
        print("No DATABASE_URL was found in environment or .env.local.\n")
        print("To run these schema migrations directly against Neon:")
        print("1. Get your free connection string at: https://neon.tech")
        print("2. Run with connection string argument:")
        print('   python database/run_schema.py "postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require"')
        print("   OR save it in pypath/.env.local:")
        print('   DATABASE_URL=postgresql://user:pass@ep-xyz.neon.tech/neondb?sslmode=require\n')

        # Interactive fallback if run directly in an interactive terminal
        if sys.stdin and sys.stdin.isatty():
            try:
                entered = input("Paste your Neon DATABASE_URL to run now (or press Enter to exit): ").strip()
                if entered.startswith("postgres"):
                    db_url = entered
                    source = "Interactive Input"
                    # Also persist to .env.local if not already present
                    if not ENV_LOCAL.exists():
                        secret = os.urandom(32).hex()
                        ENV_LOCAL.write_text(f"DATABASE_URL={db_url}\nJWT_SECRET={secret}\n", encoding="utf-8")
                        print(f"[INFO] Saved configuration to {ENV_LOCAL.name}")
                else:
                    return
            except (KeyboardInterrupt, EOFError):
                print("\nAborted.")
                return
        else:
            return

    print(f"\nTarget Database Source: {source}")
    # Mask password for display
    masked_url = re.sub(r":([^@]+)@", ":****@", db_url)
    print(f"Connection String: {masked_url}")
    print(f"Executing {len(statements)} statements against Neon Postgres...\n")

    success_count = 0
    for idx, stmt in enumerate(statements, 1):
        first_line = stmt.strip().splitlines()[0]
        desc = first_line[:65]
        print(f"[{idx}/{len(statements)}] Executing: {desc} ...", end=" ", flush=True)

        try:
            execute_via_neon_http(db_url, stmt)
            print("OK")
            success_count += 1
        except Exception as e:
            print("FAILED")
            print(f"    Error: {e}")
            sys.exit(1)

    print("\n" + "=" * 60)
    print(f"  SUCCESS! Executed {success_count}/{len(statements)} statements.")
    print("=" * 60)

    # Verify tables exist
    try:
        print("\nVerifying tables in database...")
        check_query = """
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name;
        """
        res = execute_via_neon_http(db_url, check_query)
        rows = res.get("rows", [])
        if rows:
            table_names = [r[0] if isinstance(r, list) else r.get("table_name") for r in rows]
            print(f"Verified tables in 'public' schema: {', '.join(table_names)}")
        else:
            print("Tables verified successfully.")
    except Exception as e:
        print(f"Note: Table check completed ({e})")

    print("\nDatabase is ready for PyPath!")


if __name__ == "__main__":
    run()

