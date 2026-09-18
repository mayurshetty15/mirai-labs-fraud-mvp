"""Unit tests for the structured historical investigation tools."""

from datetime import datetime, timezone
from unittest.mock import Mock, patch

from app import tools


AS_OF = datetime.fromtimestamp(1000, timezone.utc)


class FakeCursor:
    def __init__(self, rows, columns):
        self.rows = rows
        self.description = [(column,) for column in columns]

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def execute(self, *_args):
        return None

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.rows[0] if self.rows else None


class FakeConnection:
    def __init__(self, rows, columns):
        self.cursor_value = FakeCursor(rows, columns)

    def cursor(self):
        return self.cursor_value

    def close(self):
        return None


def test_get_transaction_rejects_future_data_and_masks_pii():
    future = {"card_id": "card-123456", "device_id": "device-9999", "time": 1001}
    with patch.object(tools, "get_transaction_by_card_id", return_value=future):
        result = tools.get_transaction("card-123456", AS_OF)
    assert result["transaction"] is None

    historical = {**future, "time": 999, "purchaser_email_domain": "buyer.example"}
    with patch.object(tools, "get_transaction_by_card_id", return_value=historical):
        result = tools.get_transaction("card-123456", AS_OF)
    assert result["transaction"]["card_id"].endswith("3456")
    assert result["transaction"]["purchaser_email_domain"] == "***.example"


def test_get_transaction_empty_result_is_clean():
    with patch.object(tools, "get_transaction_by_card_id", return_value=None):
        assert tools.get_transaction("missing", AS_OF)["transaction"] is None


def test_get_card_history_excludes_future_and_out_of_window_rows():
    rows = [
        {"transaction_id": 1, "time": 999, "amount": 2},
        {"transaction_id": 2, "time": 1000, "amount": 3},
        {"transaction_id": 3, "time": -3000, "amount": 4},
    ]
    with patch.object(tools, "lookup_card_history", return_value=rows):
        result = tools.get_card_history("card-1", AS_OF, window_hours=1)
    assert [row["transaction_id"] for row in result["history"]] == [1]


def test_get_card_history_empty_result_is_clean():
    with patch.object(tools, "lookup_card_history", return_value=[]):
        assert tools.get_card_history("missing", AS_OF)["history"] == []


def test_get_device_history_filters_at_database_cutoff():
    columns = ["transaction_id", "card_id", "device_id", "time", "amount", "decision", "class_label"]
    rows = [
        (1, "card-a", "device-x", 999, 5, "review", 1),
        (2, "card-future", "device-x", 1001, 9, "review", 0),
    ]
    with patch.object(tools, "get_postgres_connection", return_value=FakeConnection(rows, columns)):
        result = tools.get_device_history("device-x", AS_OF)
    assert len(result["transactions"]) == 1
    assert result["distinct_card_count"] == 1


def test_get_device_history_empty_result_is_clean():
    columns = ["transaction_id", "card_id", "device_id", "time", "amount", "decision", "class_label"]
    with patch.object(tools, "get_postgres_connection", return_value=FakeConnection([], columns)):
        result = tools.get_device_history("unknown", AS_OF)
    assert result["transactions"] == []
    assert result["distinct_card_count"] == 0


def test_get_email_domain_profile_empty_result_is_clean():
    connection = FakeConnection([(0, None)], ["transaction_count", "fraud_rate"])
    with patch.object(tools, "get_postgres_connection", return_value=connection):
        result = tools.get_email_domain_profile("unknown.example", AS_OF)
    assert result["transaction_count"] == 0
    assert result["fraud_rate"] is None


def test_get_velocity_is_read_only_and_uses_as_of_cutoff():
    client = Mock()
    client.zcount.return_value = 2
    with patch.object(tools, "get_redis_client", return_value=client):
        result = tools.get_velocity("card-1", "device-1", AS_OF)
    assert result["count"] == 2
    client.zadd.assert_not_called()
    client.zremrangebyscore.assert_not_called()


def test_get_velocity_empty_result_is_clean():
    with patch.object(tools, "get_redis_client", return_value=None):
        result = tools.get_velocity("missing", "unknown", AS_OF)
    assert result["available"] is False
    assert result["count"] == 0


def test_get_similar_transactions_empty_result_is_clean():
    columns = ["transaction_id", "card_id", "device_id", "time", "amount", "v_features", "class_label"]
    with patch.object(tools, "get_postgres_connection", return_value=FakeConnection([], columns)):
        result = tools.get_similar_transactions({"Time": 1, "Amount": 2}, AS_OF)
    assert result["transactions"] == []


def test_get_model_explanation_empty_result_is_clean():
    with patch.object(tools, "get_transaction_by_card_id", return_value=None):
        result = tools.get_model_explanation("missing")
    assert result["explanations"] == []


def test_get_model_explanation_returns_shap_output():
    row = {"time": 1, "amount": 2, "v_features": {f"V{i}": 0 for i in range(1, 29)}}
    with patch.object(tools, "get_transaction_by_card_id", return_value=row), patch.object(
        tools, "joblib"
    ) as joblib_module, patch.object(
        tools, "explain_prediction", return_value=["Amount: contributed +0.20 to fraud score"]
    ):
        joblib_module.load.return_value = object()
        result = tools.get_model_explanation("card-1")
    assert result["explanations"][0]["feature"] == "Amount"
