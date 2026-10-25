"""Serializable game entities."""
from dataclasses import dataclass, asdict, field
from typing import Any

@dataclass
class Product:
    name: str
    architecture: str
    node: str
    memory: str
    clock: int
    benchmark: float
    unit_cost: float
    price: float
    inventory: int = 0
    produced_total: int = 0
    sold_total: int = 0
    revenue_total: float = 0.0
    launched_year: int = 1998
    launched_month: int = 1
    production_target: int = 1000
    driver_level: int = 0
    last_month_sales: int = 0
    last_month_profit: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Product":
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in data.items() if k in allowed})

@dataclass
class GameState:
    company_name: str = "NovaSilicon"
    year: int = 1998
    month: int = 1
    money: float = 4_000_000
    reputation: int = 42
    market_share: float = 0.0
    architecture_tier: int = 0
    process_tier: int = 0
    memory_tier: int = 0
    driver_level: int = 0
    research_points: float = 18.0
    engineers: int = 3
    researchers: int = 2
    marketers: int = 1
    factory_level: int = 1
    factory_capacity: int = 2500
    marketing_budget: int = 25_000
    products: list[Product] = field(default_factory=list)
    active_tab: str = "dashboard"
    messages: list[dict[str, str]] = field(default_factory=list)
    history: list[dict[str, Any]] = field(default_factory=list)
    current_event: dict[str, Any] | None = None
    event_cost_multiplier: float = 1.0
    event_demand_multiplier: float = 1.0
    campaign_demand_bonus: float = 1.0
    last_month_revenue: float = 0.0
    last_month_expenses: float = 0.0
    last_month_profit: float = 0.0
    total_sales: int = 0
    total_revenue: float = 0.0
    tech_investment: float = 0.0
    launch_count: int = 0
    game_over: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["products"] = [p.to_dict() for p in self.products]
        return data

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "GameState":
        values = dict(data)
        values["products"] = [Product.from_dict(p) for p in values.get("products", [])]
        allowed = cls.__dataclass_fields__.keys()
        return cls(**{k: v for k, v in values.items() if k in allowed})
