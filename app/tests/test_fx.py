from datetime import date, timedelta
from decimal import Decimal
from app.services import fx_service


def test_get_rate_same_currency():
    assert fx_service.get_rate(None, "EGP", "EGP") == Decimal("1.0")


def test_convert_same_currency():
    result = fx_service.convert_amount(None, Decimal("100"), "EGP", "EGP")
    assert result["amount"] == 100.0
    assert result["rate"] == 1.0


def test_add_and_get_rate(db_session):
    from app.models.fx_rate import FxRate
    db = db_session
    today = date.today()
    fx_service.add_rate(db, today, "USD", "EGP", 49.25, "test")
    rate = fx_service.get_rate(db, "USD", "EGP", today)
    assert rate is not None
    assert float(rate) == 49.25


def test_convert_usd_to_egp(db_session):
    fx_service.add_rate(db_session, date.today(), "USD", "EGP", 49.25, "test")
    result = fx_service.convert_amount(db_session, Decimal("100"), "USD", "EGP")
    assert result["amount"] == 4925.0
    assert result["rate"] == 49.25


def test_convert_egp_to_usd_via_inversion(db_session):
    fx_service.add_rate(db_session, date.today(), "USD", "EGP", 49.25, "test")
    result = fx_service.convert_amount(db_session, Decimal("4925"), "EGP", "USD")
    assert result["amount"] == 100.0


def test_latest_rates(db_session):
    fx_service.add_rate(db_session, date.today(), "USD", "EGP", 49.25, "test")
    fx_service.add_rate(db_session, date.today(), "EUR", "EGP", 52.80, "test")
    rates = fx_service.get_latest_rates(db_session)
    rate_map = {r["currency"]: r["rate_to_base"] for r in rates}
    assert rate_map.get("USD") == 49.25
    assert rate_map.get("EUR") == 52.80


def test_historical_rates(db_session):
    fx_service.add_rate(db_session, date.today() - timedelta(days=30), "USD", "EGP", 48.50, "test")
    fx_service.add_rate(db_session, date.today(), "USD", "EGP", 49.25, "test")
    hist = fx_service.get_historical_rates(db_session, "USD", months=3)
    assert len(hist) == 2
    assert hist[-1]["rate"] == 49.25


def test_seed_default_rates(db_session):
    fx_service.seed_default_rates(db_session)
    usd = fx_service.get_rate(db_session, "USD", "EGP")
    eur = fx_service.get_rate(db_session, "EUR", "EGP")
    assert usd is not None
    assert eur is not None
