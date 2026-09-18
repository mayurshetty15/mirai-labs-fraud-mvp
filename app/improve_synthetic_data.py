"""Create a more realistic synthetic version of the augmented transaction data."""

from pathlib import Path

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parent.parent
INPUT_PATH = PROJECT_ROOT / "data" / "creditcard_augmented.csv"
OUTPUT_PATH = PROJECT_ROOT / "data" / "creditcard_augmented_v2.csv"
RANDOM_SEED = 42

SUSPICIOUS_DOMAINS = ("tempmail.io", "quickmail-temp.io", "mailinator.com")
RING_RANGES = {
    "small": (2, 3),
    "medium": (5, 8),
    "large": (15, 20),
}


def _group_sizes(total: int, rng: np.random.Generator) -> list[int]:
    """Split a row count into random groups of three to eight rows."""
    if total == 0:
        return []
    if total < 3:
        return [total]

    group_count = max(1, min(total // 3, int(np.ceil(total / 5))))
    sizes = [3] * group_count
    remaining = total - sum(sizes)
    while remaining:
        candidates = [i for i, size in enumerate(sizes) if size < 8]
        index = int(rng.choice(candidates))
        increment = min(remaining, 8 - sizes[index])
        increment = min(increment, int(rng.integers(1, increment + 1)))
        sizes[index] += increment
        remaining -= increment
    rng.shuffle(sizes)
    return sizes


def _apply_fraud_patterns(data: pd.DataFrame, rng: np.random.Generator) -> tuple[dict[str, int], int, int]:
    fraud_indices = data.index[data["Class"].astype(int).eq(1)].to_numpy()
    ring_names = np.array(["small", "medium", "large"])
    assigned_rings = rng.choice(ring_names, size=len(fraud_indices))

    ring_devices: dict[str, list[str]] = {}
    for ring_name, (minimum, maximum) in RING_RANGES.items():
        device_count = int(rng.integers(minimum, maximum + 1))
        ring_devices[ring_name] = [
            f"dvc_{ring_name}_{number:02d}" for number in range(device_count)
        ]

    ring_counts = {ring_name: 0 for ring_name in ring_names}
    for row_index, ring_name in zip(fraud_indices, assigned_rings):
        ring_name = str(ring_name)
        ring_counts[ring_name] += 1
        data.at[row_index, "device_id"] = str(rng.choice(ring_devices[ring_name]))
        if ring_name in {"medium", "large"}:
            data.at[row_index, "recipient_email_domain"] = (
                SUSPICIOUS_DOMAINS[int(rng.integers(0, len(SUSPICIOUS_DOMAINS)))]
            )

    target_burst_rows = round(len(fraud_indices) * 0.30)
    burst_indices = rng.permutation(fraud_indices)[:target_burst_rows]
    burst_sizes = _group_sizes(target_burst_rows, rng)
    cursor = 0
    for burst_number, burst_size in enumerate(burst_sizes):
        burst_rows = burst_indices[cursor : cursor + burst_size]
        cursor += burst_size
        original_times = data.loc[burst_rows, "Time"].astype(float)
        start_time = int(original_times.min())
        window = int(rng.integers(60, 91))
        offsets = np.sort(rng.choice(window + 1, size=burst_size, replace=False))
        data.loc[burst_rows, "Time"] = start_time + offsets
        data.loc[burst_rows, "card_id"] = f"card_fraud_burst_{burst_number:03d}"

    return ring_counts, len(burst_indices), len(fraud_indices) - len(burst_indices)


def _apply_legitimate_card_reuse(data: pd.DataFrame, rng: np.random.Generator) -> int:
    legitimate_indices = data.index[data["Class"].astype(int).eq(0)].to_numpy()
    target_rows = round(len(legitimate_indices) * 0.10)
    selected_indices = rng.permutation(legitimate_indices)[:target_rows]
    group_sizes = []
    remaining = target_rows
    while remaining >= 3:
        group_size = int(rng.integers(3, 6))
        group_size = min(group_size, remaining)
        if remaining - group_size in {1, 2}:
            group_size -= 3 - (remaining - group_size)
        if group_size < 3:
            break
        group_sizes.append(group_size)
        remaining -= group_size

    rng.shuffle(group_sizes)
    cursor = 0
    for group_number, group_size in enumerate(group_sizes):
        group_rows = selected_indices[cursor : cursor + group_size]
        cursor += group_size
        data.loc[group_rows, "card_id"] = f"card_legit_reuse_{group_number:04d}"

    return len(group_sizes)


def main() -> None:
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Input dataset not found: {INPUT_PATH}")

    original = pd.read_csv(INPUT_PATH)
    data = original.copy()
    rng = np.random.default_rng(RANDOM_SEED)

    ring_counts, burst_count, non_burst_count = _apply_fraud_patterns(data, rng)
    legitimate_reuse_count = _apply_legitimate_card_reuse(data, rng)
    data.to_csv(OUTPUT_PATH, index=False)

    legitimate_counts = data.loc[data["Class"].eq(0), "card_id"].value_counts()
    repeated_legitimate_cards = int(legitimate_counts.between(3, 5).sum())

    print(f"Wrote {OUTPUT_PATH}")
    print("Fraud rows by ring size:")
    for ring_name in ("small", "medium", "large"):
        print(f"  {ring_name}: {ring_counts[ring_name]}")
    print(f"Fraud rows with burst timing: {burst_count}")
    print(f"Fraud rows without burst timing: {non_burst_count}")
    print(f"Legitimate reuse groups created: {legitimate_reuse_count}")
    print(
        "Legitimate card_ids repeating 3-5 times: "
        f"{repeated_legitimate_cards}"
    )
    print(
        f"Total rows: {len(data)} "
        f"({'matches original' if len(data) == len(original) else 'DOES NOT MATCH original'})"
    )


if __name__ == "__main__":
    main()