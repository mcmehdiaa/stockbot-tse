from datetime import UTC, datetime

from stockbot.ingestion.tse import normalize_tsetmc_payload


def test_normalizes_supported_envelope_and_keeps_raw_payload() -> None:
    observed_at = datetime(2026, 9, 2, tzinfo=UTC)
    payload = {"instrumentList": [{"lVal18AFC": "فولاد", "price": 1234}, {"price": 99}]}

    snapshots = normalize_tsetmc_payload(payload, observed_at=observed_at)

    assert len(snapshots) == 1
    assert snapshots[0].symbol == "فولاد"
    assert snapshots[0].raw["price"] == 1234
