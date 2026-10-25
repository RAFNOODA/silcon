import random

from gpu_tycoon.data import ARCHITECTURES, PROCESS_NODES, MEMORIES
from gpu_tycoon.economy import (
    create_new_game, design_product, advance_month, set_price, set_production,
    save_game, load_game, invest_research, money,
)


def test_new_company_starts_in_1998_with_starting_cash():
    state = create_new_game("  Byte Works  ")
    assert state.company_name == "Byte Works"
    assert state.year == 1998 and state.month == 1
    assert state.money == 4_000_000


def test_can_design_first_gpu_and_reject_duplicate_name():
    state = create_new_game()
    ok, _ = design_product(state, "NovaFire 100", ARCHITECTURES[0].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    assert ok
    assert len(state.products) == 1
    assert state.products[0].benchmark > 0
    ok, message = design_product(state, "NovaFire 100", ARCHITECTURES[0].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    assert not ok and "zaten" in message


def test_month_turn_generates_sales_and_financial_history(monkeypatch):
    monkeypatch.setattr("gpu_tycoon.economy.save_game", lambda state: None)
    state = create_new_game()
    ok, _ = design_product(state, "NovaFire 100", ARCHITECTURES[0].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    assert ok
    state.products[0].production_target = 1400
    result = advance_month(state, random.Random(7))
    assert result["date"] == "1998 / 02"
    assert state.month == 2
    assert len(state.history) == 2
    assert state.products[0].produced_total > 0
    assert state.money != 4_000_000


def test_price_and_production_controls_respect_limits():
    state = create_new_game()
    design_product(state, "NovaFire 100", ARCHITECTURES[0].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    set_price(state, 0, -999999)
    assert state.products[0].price == 25
    set_production(state, 0, -10000)
    assert state.products[0].production_target == 0


def test_save_load_roundtrip(tmp_path):
    state = create_new_game("Pixel Foundry")
    design_product(state, "Pixel One", ARCHITECTURES[0].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    path = tmp_path / "save.json"
    save_game(state, path)
    loaded = load_game(path)
    assert loaded.company_name == "Pixel Foundry"
    assert loaded.products[0].name == "Pixel One"
    assert loaded.products[0].benchmark == state.products[0].benchmark


def test_technology_is_locked_until_its_historical_year_and_research():
    state = create_new_game()
    ok, message = design_product(state, "Too Early", ARCHITECTURES[1].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    assert not ok
    state.year = 2001
    state.research_points = 999
    state.money = 10_000_000
    ok, _ = invest_research(state, "architecture")
    assert ok
    ok, _ = design_product(state, "Shaderless", ARCHITECTURES[1].name, PROCESS_NODES[0].name, MEMORIES[0].name, 200)
    assert ok


def test_money_formatting():
    assert money(1_500_000) == "$1.50M"
    assert money(-2500) == "-$2.5K"
