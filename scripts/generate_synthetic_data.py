"""Generate reproducible synthetic payment operations data for FinSight PayOps.

The generated CSV files are fictional and intended only for local demos,
analytics experiments, and assistant development. They do not contain private
or real client data.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd

ROOT_DIR = Path(__file__).resolve().parents[1]
RAW_DATA_DIR = ROOT_DIR / "data" / "raw"

RANDOM_SEED = 42
REFERENCE_DATE = date(2026, 4, 1)
MONTHS_BACK = 24
CLIENT_COUNT = 500
PROVIDER_COUNT = 20
PAYMENT_COUNT = 10_000

CLIENT_TYPES = ["Individual", "SME", "Enterprise"]
REGIONS = ["North", "Central", "West", "South", "East"]
CLIENT_STATUSES = ["Active", "Inactive", "Suspended"]
RISK_LEVELS = ["Low", "Medium", "High"]
CHANNELS = ["Card", "Bank Transfer", "Cash", "Wallet", "SPEI"]
PROVIDER_STATUSES = ["Active", "Inactive"]
PAYMENT_STATUSES = ["Successful", "Failed", "Pending", "Reversed"]
CURRENCIES = ["MXN", "USD"]
FAILURE_REASONS = [
    "Insufficient funds",
    "Provider timeout",
    "Invalid account details",
    "Risk rule declined",
    "Network error",
    "Expired authorization",
]

CLIENT_TYPE_WEIGHTS = [0.60, 0.30, 0.10]
CLIENT_STATUS_WEIGHTS = [0.82, 0.13, 0.05]
RISK_WEIGHTS_BY_CLIENT_TYPE = {
    "Individual": [0.60, 0.30, 0.10],
    "SME": [0.50, 0.35, 0.15],
    "Enterprise": [0.45, 0.40, 0.15],
}
PAYMENT_WEIGHTS_BY_CLIENT_TYPE = {
    "Individual": 1.0,
    "SME": 4.0,
    "Enterprise": 12.0,
}
AMOUNT_LOGNORMAL_BY_CLIENT_TYPE = {
    "Individual": (5.35, 0.75),
    "SME": (7.05, 0.70),
    "Enterprise": (8.75, 0.65),
}
STATUS_WEIGHTS_BY_RISK = {
    "Low": [0.925, 0.040, 0.025, 0.010],
    "Medium": [0.885, 0.070, 0.030, 0.015],
    "High": [0.815, 0.120, 0.040, 0.025],
}


def _random_dates(rng: np.random.Generator, start: date, end: date, count: int) -> list[date]:
    """Return random dates between start and end, inclusive."""
    day_span = (end - start).days
    offsets = rng.integers(0, day_span + 1, size=count)
    return [start + timedelta(days=int(offset)) for offset in offsets]


def generate_clients(rng: np.random.Generator) -> pd.DataFrame:
    """Generate synthetic client records."""
    signup_start = REFERENCE_DATE - timedelta(days=5 * 365)
    client_types = rng.choice(CLIENT_TYPES, size=CLIENT_COUNT, p=CLIENT_TYPE_WEIGHTS)
    risk_levels = [
        rng.choice(RISK_LEVELS, p=RISK_WEIGHTS_BY_CLIENT_TYPE[client_type])
        for client_type in client_types
    ]

    clients = pd.DataFrame(
        {
            "client_id": [f"C{idx:04d}" for idx in range(1, CLIENT_COUNT + 1)],
            "client_name": [f"FinSight Demo Client {idx:04d}" for idx in range(1, CLIENT_COUNT + 1)],
            "client_type": client_types,
            "region": rng.choice(REGIONS, size=CLIENT_COUNT, p=[0.20, 0.28, 0.16, 0.18, 0.18]),
            "signup_date": _random_dates(rng, signup_start, REFERENCE_DATE - timedelta(days=30), CLIENT_COUNT),
            "status": rng.choice(CLIENT_STATUSES, size=CLIENT_COUNT, p=CLIENT_STATUS_WEIGHTS),
            "risk_level": risk_levels,
        }
    )
    return clients.sort_values("client_id").reset_index(drop=True)


def generate_providers(rng: np.random.Generator) -> pd.DataFrame:
    """Generate synthetic payment provider records."""
    provider_names = [
        "Aurora Card Network",
        "BridgeBank Transfer",
        "Centavo Cash Rail",
        "Delta Wallet Services",
        "Eagle SPEI Gateway",
        "Faro Card Processing",
        "Granite Bank Link",
        "Helio Cash Connect",
        "Ion Wallet Hub",
        "Jade SPEI Direct",
        "Kinetic Card Acquirer",
        "Laguna Bank Transfer",
        "Metro Cash Services",
        "Nimbus Wallet Network",
        "Orion SPEI Switch",
        "Pioneer Card Gateway",
        "Quanta Bank Rail",
        "Riviera Cash Ops",
        "Sol Wallet Pay",
        "Terra SPEI Processor",
    ]
    active_start = REFERENCE_DATE - timedelta(days=7 * 365)
    channels = [CHANNELS[(idx - 1) % len(CHANNELS)] for idx in range(1, PROVIDER_COUNT + 1)]

    providers = pd.DataFrame(
        {
            "provider_id": [f"P{idx:03d}" for idx in range(1, PROVIDER_COUNT + 1)],
            "provider_name": provider_names,
            "channel": channels,
            "region": rng.choice(REGIONS, size=PROVIDER_COUNT, p=[0.18, 0.30, 0.17, 0.17, 0.18]),
            "active_since": _random_dates(rng, active_start, REFERENCE_DATE - timedelta(days=180), PROVIDER_COUNT),
            "status": rng.choice(PROVIDER_STATUSES, size=PROVIDER_COUNT, p=[0.90, 0.10]),
        }
    )
    return providers.sort_values("provider_id").reset_index(drop=True)


def _seasonal_payment_dates(rng: np.random.Generator, count: int) -> list[date]:
    """Generate payment dates with heavier activity in seasonal months."""
    start = REFERENCE_DATE - timedelta(days=730)
    all_dates = pd.date_range(start=start, end=REFERENCE_DATE, freq="D")
    month_weights = {
        1: 0.95,
        2: 0.90,
        3: 1.00,
        4: 1.05,
        5: 1.00,
        6: 1.05,
        7: 1.10,
        8: 1.05,
        9: 1.00,
        10: 1.10,
        11: 1.45,
        12: 1.60,
    }
    weekday_weights = np.where(all_dates.dayofweek < 5, 1.0, 0.70)
    weights = np.array([month_weights[d.month] for d in all_dates]) * weekday_weights
    weights = weights / weights.sum()
    sampled = rng.choice(all_dates.to_numpy(), size=count, replace=True, p=weights)
    return [pd.Timestamp(value).date() for value in sampled]


def _payment_amount(rng: np.random.Generator, client_type: str) -> float:
    """Generate a realistic payment amount by client type."""
    mean, sigma = AMOUNT_LOGNORMAL_BY_CLIENT_TYPE[client_type]
    amount = rng.lognormal(mean=mean, sigma=sigma)
    if client_type == "Individual":
        amount = np.clip(amount, 60, 12_000)
    elif client_type == "SME":
        amount = np.clip(amount, 250, 85_000)
    else:
        amount = np.clip(amount, 1_500, 650_000)
    return round(float(amount), 2)


def generate_payments(
    rng: np.random.Generator, clients: pd.DataFrame, providers: pd.DataFrame
) -> pd.DataFrame:
    """Generate synthetic payment records linked to clients and providers."""
    active_clients = clients[clients["status"] == "Active"].copy()
    inactive_clients = clients[clients["status"] != "Active"].copy()
    client_pool = pd.concat([active_clients, inactive_clients], ignore_index=True)
    client_weights = client_pool["client_type"].map(PAYMENT_WEIGHTS_BY_CLIENT_TYPE).to_numpy(dtype=float)
    client_weights *= np.where(client_pool["status"].eq("Active"), 1.0, 0.15)
    client_weights = client_weights / client_weights.sum()

    provider_weights = np.where(providers["status"].eq("Active"), 1.0, 0.10).astype(float)
    provider_weights = provider_weights / provider_weights.sum()

    selected_client_idx = rng.choice(client_pool.index.to_numpy(), size=PAYMENT_COUNT, p=client_weights)
    selected_provider_idx = rng.choice(providers.index.to_numpy(), size=PAYMENT_COUNT, p=provider_weights)
    payment_dates = _seasonal_payment_dates(rng, PAYMENT_COUNT)

    rows = []
    for idx, (client_idx, provider_idx, payment_date) in enumerate(
        zip(selected_client_idx, selected_provider_idx, payment_dates), start=1
    ):
        client = client_pool.loc[client_idx]
        provider = providers.loc[provider_idx]
        status_weights = STATUS_WEIGHTS_BY_RISK[client["risk_level"]]
        status = rng.choice(PAYMENT_STATUSES, p=status_weights)
        amount = _payment_amount(rng, client["client_type"])
        currency = rng.choice(CURRENCIES, p=[0.88, 0.12])
        failure_reason = rng.choice(FAILURE_REASONS) if status == "Failed" else ""
        created_hour = int(rng.integers(0, 24))
        created_minute = int(rng.integers(0, 60))
        created_second = int(rng.integers(0, 60))
        created_at = datetime.combine(payment_date, datetime.min.time()).replace(
            hour=created_hour, minute=created_minute, second=created_second
        )

        rows.append(
            {
                "payment_id": f"PMT{idx:06d}",
                "client_id": client["client_id"],
                "provider_id": provider["provider_id"],
                "payment_date": payment_date.isoformat(),
                "amount": amount,
                "currency": currency,
                "status": status,
                "failure_reason": failure_reason,
                "created_at": created_at.isoformat(timespec="seconds"),
            }
        )

    return pd.DataFrame(rows).sort_values("payment_id").reset_index(drop=True)


def generate_all() -> None:
    """Generate all Phase 2 raw CSV files."""
    rng = np.random.default_rng(RANDOM_SEED)
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    clients = generate_clients(rng)
    providers = generate_providers(rng)
    payments = generate_payments(rng, clients, providers)

    clients.to_csv(RAW_DATA_DIR / "clients.csv", index=False)
    providers.to_csv(RAW_DATA_DIR / "providers.csv", index=False)
    payments.to_csv(RAW_DATA_DIR / "payments.csv", index=False)

    print(f"Generated {len(clients):,} clients -> {RAW_DATA_DIR / 'clients.csv'}")
    print(f"Generated {len(providers):,} providers -> {RAW_DATA_DIR / 'providers.csv'}")
    print(f"Generated {len(payments):,} payments -> {RAW_DATA_DIR / 'payments.csv'}")


if __name__ == "__main__":
    generate_all()
