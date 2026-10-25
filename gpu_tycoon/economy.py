"""Turn-based company and hardware simulation rules."""
from __future__ import annotations
import json
import random
from pathlib import Path
from typing import Any
from .data import ARCHITECTURES, PROCESS_NODES, MEMORIES, COMPETITORS, EVENTS, MILESTONES
from .models import GameState, Product

BASE_MONTHLY_DEMAND = 2_400


def money(value: float) -> str:
    value = float(value)
    sign = "-" if value < 0 else ""
    value = abs(value)
    if value >= 1_000_000:
        return f"{sign}${value / 1_000_000:.2f}M"
    if value >= 1_000:
        return f"{sign}${value / 1_000:.1f}K"
    return f"{sign}${value:,.0f}"


def date_label(state: GameState) -> str:
    return f"{state.year} / {state.month:02d}"


def technology_choices(state: GameState) -> dict[str, list[dict[str, Any]]]:
    return {
        "architectures": [as_choice(x.name, x.year, x.tier, x.multiplier, x.description) for x in ARCHITECTURES],
        "nodes": [as_choice(x.name, x.year, x.tier, x.cost_factor, f"{x.nm} nm · üretim maliyet katsayısı") for x in PROCESS_NODES],
        "memories": [as_choice(x.name, x.year, x.tier, x.multiplier, f"Bellek bant genişliği katsayısı · maliyet {x.cost_factor:.2f}x") for x in MEMORIES],
    }


def as_choice(name: str, year: int, tier: int, factor: float, description: str) -> dict[str, Any]:
    return {"name": name, "year": year, "tier": tier, "factor": factor, "description": description}


def tech_unlocked(state: GameState, kind: str, tier: int) -> bool:
    lvl = {"architecture": state.architecture_tier, "node": state.process_tier, "memory": state.memory_tier}[kind]
    item_list = {"architecture": ARCHITECTURES, "node": PROCESS_NODES, "memory": MEMORIES}[kind]
    return tier <= lvl and state.year >= item_list[tier].year


def available_items(state: GameState, kind: str) -> list[Any]:
    items = {"architecture": ARCHITECTURES, "node": PROCESS_NODES, "memory": MEMORIES}[kind]
    level = {"architecture": state.architecture_tier, "node": state.process_tier, "memory": state.memory_tier}[kind]
    return [item for item in items if item.tier <= level and item.year <= state.year]


def compute_specs(architecture: str, node: str, memory: str, clock: int, driver_level: int = 0) -> tuple[float, float]:
    arch = next(x for x in ARCHITECTURES if x.name == architecture)
    proc = next(x for x in PROCESS_NODES if x.name == node)
    mem = next(x for x in MEMORIES if x.name == memory)
    benchmark = arch.multiplier * (250 / proc.nm) ** 0.29 * mem.multiplier * (max(100, clock) / 200) ** 0.75 * 100
    benchmark *= 1 + 0.055 * driver_level
    unit_cost = (31 + 39 * proc.cost_factor + 26 * mem.cost_factor) * (1 + arch.tier * 0.055)
    unit_cost *= max(0.65, 1 - 0.035 * driver_level)
    return round(benchmark, 1), round(unit_cost, 2)


def create_new_game(company_name: str = "NovaSilicon") -> GameState:
    name = " ".join(company_name.strip().split())[:28] or "NovaSilicon"
    state = GameState(company_name=name)
    state.messages = [
        {"title": "Şirket kuruldu", "text": f"{name} 1998 yılında ilk ürününü geliştirmek üzere kuruldu."},
        {"title": "Yönetim notu", "text": "Pazara ürün çıkarmadan önce GPU Laboratuvarı'nda tasarım yap. Fabrikada üretimi planla ve ay sonunda sonuçları gör."},
    ]
    state.history = [{"date": "1998 / 01", "revenue": 0, "expenses": 0, "profit": 0, "sales": 0, "money": state.money}]
    return state


def design_product(state: GameState, name: str, architecture: str, node: str, memory: str, clock: int) -> tuple[bool, str]:
    name = " ".join(name.strip().split())[:32]
    if not name:
        return False, "Ürün adı boş olamaz."
    if len(state.products) >= 8:
        return False, "Ürün portföyü dolu. Yeni seri için şirket seviyesini geliştir."
    if any(p.name.casefold() == name.casefold() for p in state.products):
        return False, "Bu isimde bir ürün zaten var."
    try:
        arch = next(x for x in ARCHITECTURES if x.name == architecture)
        proc = next(x for x in PROCESS_NODES if x.name == node)
        mem = next(x for x in MEMORIES if x.name == memory)
    except StopIteration:
        return False, "Geçersiz teknoloji seçimi."
    if not (tech_unlocked(state, "architecture", arch.tier) and tech_unlocked(state, "node", proc.tier) and tech_unlocked(state, "memory", mem.tier)):
        return False, "Bu teknoloji henüz araştırılmadı veya tarihsel olarak kullanıma açılmadı."
    cost = 180_000 + arch.tier * 90_000 + proc.tier * 65_000 + mem.tier * 45_000
    if state.money < cost:
        return False, f"Tasarım için {money(cost)} gerekiyor."
    benchmark, unit_cost = compute_specs(architecture, node, memory, clock, state.driver_level)
    suggested = max(49, round((85 + benchmark * 1.15) / 10) * 10)
    product = Product(
        name=name, architecture=architecture, node=node, memory=memory, clock=max(100, min(3000, clock)),
        benchmark=benchmark, unit_cost=unit_cost, price=suggested,
        launched_year=state.year, launched_month=state.month, production_target=1000,
        driver_level=state.driver_level,
    )
    state.money -= cost
    state.tech_investment += cost
    state.products.append(product)
    state.launch_count += 1
    state.reputation = min(100, state.reputation + 2)
    state.messages.insert(0, {"title": f"{name} piyasaya çıktı", "text": f"{architecture} mimarili ürün hazır. Önerilen başlangıç fiyatı {money(suggested)}."})
    return True, f"{name} tasarlandı ve ürün portföyüne eklendi."


def set_price(state: GameState, index: int, delta: float) -> tuple[bool, str]:
    if not 0 <= index < len(state.products):
        return False, "Ürün bulunamadı."
    p = state.products[index]
    p.price = max(25, min(12_000, round(p.price + delta, 2)))
    return True, f"{p.name} yeni fiyatı: {money(p.price)}"


def set_production(state: GameState, index: int, delta: int) -> tuple[bool, str]:
    if not 0 <= index < len(state.products):
        return False, "Ürün bulunamadı."
    p = state.products[index]
    p.production_target = max(0, min(state.factory_capacity * 2, p.production_target + delta))
    return True, f"{p.name} üretim hedefi: {p.production_target:,} adet/ay"


def invest_research(state: GameState, kind: str) -> tuple[bool, str]:
    levels = {"architecture": state.architecture_tier, "node": state.process_tier, "memory": state.memory_tier}
    lists = {"architecture": ARCHITECTURES, "node": PROCESS_NODES, "memory": MEMORIES}
    labels = {"architecture": "Mimari", "node": "Üretim teknolojisi", "memory": "Bellek teknolojisi"}
    if kind == "drivers":
        cost = 180_000 + state.driver_level * 125_000
        points = 24 + state.driver_level * 8
        if state.driver_level >= 8:
            return False, "Sürücü ekibi en üst seviyede."
        if state.money < cost or state.research_points < points:
            return False, f"Gerekli: {money(cost)} ve {points} AR-GE puanı."
        state.money -= cost
        state.research_points -= points
        state.driver_level += 1
        state.reputation = min(100, state.reputation + 1)
        for p in state.products:
            p.driver_level = state.driver_level
            p.benchmark, p.unit_cost = compute_specs(p.architecture, p.node, p.memory, p.clock, p.driver_level)
        state.messages.insert(0, {"title": "Sürücü güncellemesi", "text": "Sürücü optimizasyonu ürünlerin performansını ve verimliliğini artırdı."})
        return True, "Sürücü teknolojisi geliştirildi."
    if kind not in levels:
        return False, "Bilinmeyen araştırma alanı."
    next_tier = levels[kind] + 1
    if next_tier >= len(lists[kind]):
        return False, "Bu teknoloji ağacının sonuna ulaştın."
    item = lists[kind][next_tier]
    if state.year < item.year:
        return False, f"{item.year} yılından önce bu teknolojiye geçilemiyor."
    points = 18 + next_tier * 12
    cost = 160_000 + next_tier * 140_000
    if state.money < cost or state.research_points < points:
        return False, f"Gerekli: {money(cost)} ve {points} AR-GE puanı."
    state.money -= cost
    state.research_points -= points
    levels[kind] = next_tier
    if kind == "architecture": state.architecture_tier = next_tier
    elif kind == "node": state.process_tier = next_tier
    else: state.memory_tier = next_tier
    state.tech_investment += cost
    state.messages.insert(0, {"title": f"{labels[kind]} araştırması tamamlandı", "text": f"{item.name} teknolojisi artık yeni ürün tasarımlarında kullanılabilir."})
    return True, f"{item.name} araştırması tamamlandı."


def hire_staff(state: GameState, role: str) -> tuple[bool, str]:
    options = {
        "engineer": ("engineers", 2, 72_000, "Mühendis"),
        "researcher": ("researchers", 1, 92_000, "Araştırmacı"),
        "marketer": ("marketers", 1, 58_000, "Pazarlamacı"),
    }
    if role not in options: return False, "Bilinmeyen pozisyon."
    field, increment, hiring_cost, label = options[role]
    if getattr(state, field) >= 30: return False, "Bu ekipte daha fazla çalışan alamazsın (30 kişi sınırı)."
    if state.money < hiring_cost: return False, f"İşe alım için {money(hiring_cost)} gerekiyor."
    state.money -= hiring_cost
    setattr(state, field, getattr(state, field) + increment)
    state.messages.insert(0, {"title": "Yeni çalışanlar", "text": f"{increment} {label.lower()} işe alındı."})
    return True, f"{increment} {label.lower()} işe alındı."


def run_marketing_campaign(state: GameState) -> tuple[bool, str]:
    cost = max(25_000, state.marketing_budget)
    if state.money < cost: return False, f"Kampanya için {money(cost)} gerekiyor."
    state.money -= cost
    state.reputation = min(100, state.reputation + min(5, 1 + state.marketers // 3))
    state.campaign_demand_bonus = max(state.campaign_demand_bonus, 1.08)
    state.messages.insert(0, {"title": "Pazarlama kampanyası", "text": f"{money(cost)} bütçeli kampanya marka bilinirliğini artırdı."})
    return True, "Pazarlama kampanyası başlatıldı."


def upgrade_factory(state: GameState) -> tuple[bool, str]:
    cost = 450_000 * state.factory_level
    if state.factory_level >= 10: return False, "Fabrika kapasitesi en üst seviyede."
    if state.money < cost: return False, f"Fabrika yatırımı için {money(cost)} gerekiyor."
    state.money -= cost
    state.factory_level += 1
    state.factory_capacity = int(2500 * (1.45 ** (state.factory_level - 1)))
    state.messages.insert(0, {"title": "Fabrika genişletildi", "text": f"Aylık kapasite {state.factory_capacity:,} adede yükseldi."})
    return True, "Fabrika genişletildi."


def _event_for_month(state: GameState, rng: random.Random) -> dict[str, Any] | None:
    if rng.random() > 0.36:
        state.current_event = None
        state.event_cost_multiplier = 1.0
        state.event_demand_multiplier = 1.0
        return None
    event = dict(rng.choice(EVENTS))
    state.current_event = event
    state.event_cost_multiplier = 1.0
    state.event_demand_multiplier = 1.0
    if event["kind"] == "cost": state.event_cost_multiplier = 1 + event["value"]
    elif event["kind"] == "discount": state.event_cost_multiplier = 1 - event["value"]
    elif event["kind"] == "demand": state.event_demand_multiplier = 1 + event["value"]
    elif event["kind"] == "recession": state.event_demand_multiplier = 1 + event["value"]
    elif event["kind"] == "reputation": state.reputation = max(0, state.reputation + int(event["value"]))
    return event


def advance_month(state: GameState, rng: random.Random | None = None) -> dict[str, Any]:
    """Advance one month, pay recurring costs, manufacture, sell, and update records."""
    rng = rng or random.Random()
    state.month += 1
    if state.month > 12:
        state.month = 1
        state.year += 1
        state.messages.insert(0, {"title": f"{state.year} yılı başladı", "text": "Yeni mali yıl için ürün, teknoloji ve nakit akışını gözden geçir."})
    event = _event_for_month(state, rng)
    milestone = MILESTONES.get(state.year) if state.month == 1 else None
    if milestone:
        state.messages.insert(0, {"title": f"Sektör dönüm noktası: {milestone[0]}", "text": milestone[1]})

    salary = state.engineers * 8_500 + state.researchers * 11_000 + state.marketers * 6_800
    fixed_cost = 38_000 + state.factory_level * 16_000
    research_generated = 7 + state.researchers * 4 + state.engineers * 0.6
    state.research_points = min(999, state.research_points + research_generated)
    expenses = salary + fixed_cost + state.marketing_budget
    state.total_sales = 0
    revenue = 0.0
    operating_costs = 0.0
    capacity = state.factory_capacity
    targets = [max(0, p.production_target) for p in state.products]
    total_target = sum(targets)
    if total_target > capacity and total_target > 0:
        planned = [int(t * capacity / total_target) for t in targets]
        leftover = capacity - sum(planned)
        for i in range(leftover): planned[i % len(planned)] += 1
    else:
        planned = targets

    # Production is paid up front. Expensive products may be partially produced when cash is low.
    for product, target in zip(state.products, planned):
        affordable = int(max(0, state.money - expenses) / max(1, product.unit_cost * state.event_cost_multiplier))
        qty = min(target, affordable)
        cost = qty * product.unit_cost * state.event_cost_multiplier
        state.money -= cost
        operating_costs += cost
        product.inventory += qty
        product.produced_total += qty

    for product in state.products:
        base = BASE_MONTHLY_DEMAND * (1 + max(0, state.year - 1998) * 0.035)
        tech_demand = 1 + max(0, product.benchmark / 100 - 1) * 0.22
        relative_price = (105 + product.benchmark * 0.82) / max(25, product.price)
        price_factor = max(0.18, min(1.55, relative_price ** 1.18))
        quality_factor = 0.75 + state.reputation / 150 + product.driver_level * 0.025
        competition_factor = max(0.45, 1 - max(0, product.benchmark - 180) / 1500)
        reputation_factor = 0.8 + state.reputation / 250
        demand = int(base * tech_demand * price_factor * quality_factor * competition_factor * reputation_factor * state.event_demand_multiplier * state.campaign_demand_bonus)
        # Competition rises over time; the player's price, performance and reputation matter more than RNG.
        sales = min(product.inventory, max(0, int(demand * rng.uniform(0.82, 1.13))))
        product.inventory -= sales
        product.sold_total += sales
        product.last_month_sales = sales
        sale_revenue = sales * product.price
        revenue += sale_revenue
        product.revenue_total += sale_revenue
        product.last_month_profit = sale_revenue - sales * product.unit_cost
        state.total_sales += sales

    state.campaign_demand_bonus = 1.0
    state.money -= expenses
    if state.money < 0:
        state.reputation = max(0, state.reputation - 2)
        state.messages.insert(0, {"title": "Nakit akışı uyarısı", "text": "Kasa eksiye düştü. Üretim hedefini, pazarlama bütçesini veya personel giderini azalt."})
    profit = revenue - operating_costs - expenses
    state.last_month_revenue = revenue
    state.last_month_expenses = expenses + operating_costs
    state.last_month_profit = profit
    state.total_revenue += revenue
    state.market_share = min(100.0, state.total_sales / max(1, BASE_MONTHLY_DEMAND * max(1, len(state.products))) * 100)
    state.history.append({"date": date_label(state), "revenue": round(revenue, 2), "expenses": round(expenses + operating_costs, 2), "profit": round(profit, 2), "sales": state.total_sales, "money": round(state.money, 2)})
    state.history = state.history[-36:]

    summary = {"date": date_label(state), "revenue": revenue, "expenses": expenses + operating_costs, "profit": profit, "sales": state.total_sales, "event": event, "research": research_generated}
    state.messages.insert(0, {"title": f"{date_label(state)} mali raporu", "text": f"Satış {state.total_sales:,} adet · Gelir {money(revenue)} · Net {money(profit)}"})
    state.messages = state.messages[:30]
    # Automatic save is a safety net, not a requirement for the simulation to work.
    try:
        save_game(state)
    except (OSError, TypeError, ValueError):
        pass
    return summary


def save_path() -> Path:
    import os
    if os.name == "nt":
        base = Path(os.environ.get("APPDATA", str(Path.home()))) / "SiliconFoundry"
    else:
        base = Path.home() / ".local" / "share" / "silicon-foundry"
    return base / "save.json"


def save_game(state: GameState, path: Path | None = None) -> Path:
    target = path or save_path()
    target.parent.mkdir(parents=True, exist_ok=True)
    temporary = target.with_suffix(".tmp")
    temporary.write_text(json.dumps(state.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")
    temporary.replace(target)
    return target


def load_game(path: Path | None = None) -> GameState:
    target = path or save_path()
    raw = json.loads(target.read_text(encoding="utf-8"))
    state = GameState.from_dict(raw)
    if not state.company_name or state.year < 1998 or not 1 <= state.month <= 12:
        raise ValueError("Kayıt dosyası geçersiz.")
    return state


def competitor_snapshot(state: GameState) -> list[dict[str, Any]]:
    result = []
    elapsed = state.year - 1998
    for i, rival in enumerate(COMPETITORS):
        result.append({
            **rival,
            "score": int(rival["score"] * (1 + max(0, elapsed) * (0.025 + i * 0.004))),
            "price": int(rival["price"] * (1 + max(0, elapsed) * 0.018)),
        })
    return result
