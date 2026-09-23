import pytest

from saas_intelligence.cloud import identifier


@pytest.mark.parametrize("bad", ["x; DROP TABLE y", "raw..events", "x--", "account space", "x/y"])
def test_reject_identifier_injection(bad):
    with pytest.raises(ValueError):
        identifier(bad)


def test_allow_qualified_identifier():
    assert identifier("saas_analytics.raw.saas_landing") == "SAAS_ANALYTICS.RAW.SAAS_LANDING"
