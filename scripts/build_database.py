"""Build the local SQLite database from synthetic FinSight PayOps CSV files."""

from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"
DATABASE_PATH = ROOT_DIR / "data" / "business_data.sqlite"

CSV_FILES = {
    "clients": RAW_DATA_DIR / "clients.csv",
    "providers": RAW_DATA_DIR / "providers.csv",
    "payments": RAW_DATA_DIR / "payments.csv",
}


def _read_csv(name: str) -> pd.DataFrame:
    """Read a required raw CSV file with a helpful error if it is missing."""
    path = CSV_FILES[name]
    if not path.exists():
        raise FileNotFoundError(
            f"Missing {path}. Run `python scripts/generate_synthetic_data.py` first."
        )
    return pd.read_csv(path)


def _create_schema(connection: sqlite3.Connection) -> None:
    """Create the clients, providers, and payments tables."""
    connection.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE clients (
            client_id TEXT PRIMARY KEY,
            client_name TEXT NOT NULL,
            client_type TEXT NOT NULL CHECK (client_type IN ('Individual', 'SME', 'Enterprise')),
            region TEXT NOT NULL CHECK (region IN ('North', 'Central', 'West', 'South', 'East')),
            signup_date TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive', 'Suspended')),
            risk_level TEXT NOT NULL CHECK (risk_level IN ('Low', 'Medium', 'High'))
        );

        CREATE TABLE providers (
            provider_id TEXT PRIMARY KEY,
            provider_name TEXT NOT NULL,
            channel TEXT NOT NULL CHECK (channel IN ('Card', 'Bank Transfer', 'Cash', 'Wallet', 'SPEI')),
            region TEXT NOT NULL CHECK (region IN ('North', 'Central', 'West', 'South', 'East')),
            active_since TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive'))
        );

        CREATE TABLE payments (
            payment_id TEXT PRIMARY KEY,
            client_id TEXT NOT NULL,
            provider_id TEXT NOT NULL,
            payment_date TEXT NOT NULL,
            amount REAL NOT NULL CHECK (amount >= 0),
            currency TEXT NOT NULL,
            status TEXT NOT NULL CHECK (status IN ('Successful', 'Failed', 'Pending', 'Reversed')),
            failure_reason TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY (client_id) REFERENCES clients (client_id),
            FOREIGN KEY (provider_id) REFERENCES providers (provider_id),
            CHECK ((status = 'Failed' AND failure_reason IS NOT NULL AND failure_reason != '') OR (status != 'Failed'))
        );

        CREATE INDEX idx_payments_client_id ON payments (client_id);
        CREATE INDEX idx_payments_provider_id ON payments (provider_id);
        CREATE INDEX idx_payments_payment_date ON payments (payment_date);
        CREATE INDEX idx_payments_status ON payments (status);
        """
    )


def build_database() -> None:
    """Replace the SQLite database with the generated synthetic dataset."""
    clients = _read_csv("clients")
    providers = _read_csv("providers")
    payments = _read_csv("payments")

    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DATABASE_PATH.exists():
        DATABASE_PATH.unlink()

    with sqlite3.connect(DATABASE_PATH) as connection:
        _create_schema(connection)
        clients.to_sql("clients", connection, if_exists="append", index=False)
        providers.to_sql("providers", connection, if_exists="append", index=False)
        payments.to_sql("payments", connection, if_exists="append", index=False)
        connection.execute("PRAGMA foreign_key_check")

    print(f"Created database -> {DATABASE_PATH}")
    print(f"Loaded clients: {len(clients):,}")
    print(f"Loaded providers: {len(providers):,}")
    print(f"Loaded payments: {len(payments):,}")


if __name__ == "__main__":
    build_database()
