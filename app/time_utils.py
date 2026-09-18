"""Shared display conversion for dataset-relative transaction timestamps."""

from datetime import datetime, timedelta, timezone

# Stored transaction times remain dataset-relative seconds. This anchor is only
# for analyst-facing display and must not be used for model or query logic.
DATASET_EPOCH = datetime(2026, 9, 1, tzinfo=timezone.utc)


def dataset_datetime(time_value: float) -> datetime:
    """Convert dataset-relative seconds to an anchored UTC datetime."""
    return DATASET_EPOCH + timedelta(seconds=max(0.0, float(time_value)))


def format_dataset_date(time_value: float) -> str:
    """Format a dataset-relative timestamp as DD/MM/YYYY."""
    return dataset_datetime(time_value).strftime("%d/%m/%Y")


def format_dataset_time(time_value: float) -> str:
    """Format a dataset-relative timestamp as HH:MM:SS."""
    return dataset_datetime(time_value).strftime("%H:%M:%S")


def format_dataset_datetime_fields(time_value: float) -> dict[str, str]:
    """Return separate bank-style date and time display fields."""
    value = dataset_datetime(time_value)
    return {
        "date": value.strftime("%d/%m/%Y"),
        "time": value.strftime("%H:%M:%S"),
    }
