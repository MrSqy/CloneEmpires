from game.economy import EconomyEngine


def test_production_formula():
    engine = EconomyEngine()
    result = engine.calculate_production(base_rate=1.0, duration=10.0)
    assert result > 10.0
    assert result < 13.0


def test_storage_limit():
    engine = EconomyEngine()
    engine.resources["wood"] = 600
    engine.storage_limit = 500
    engine.cap_resources()
    assert engine.resources["wood"] == 500
