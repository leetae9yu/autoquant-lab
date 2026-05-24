"""DDQM2-style factor-return research track for autoquant-lab."""

from .definitions import FactorDefinition, all_factor_definitions, implemented_factor_definitions
from .scores import build_factor_scores
from .returns import build_factor_long_short_returns
from .ddqm2 import (
    backtest_factor_allocations,
    backtest_stock_score_long_only_qspread,
    backtest_stock_score_qspread,
    build_factor_allocations,
    conservative_cost_tax_assumptions,
    cost_tax_sensitivity,
    macro_design_columns,
    select_factor_universe,
    train_factor_return_models,
)
from .ablation_plan import AblationPlan, AblationVariant, load_ablation_plan, planned_backlog, runnable_variants

__all__ = [
    "FactorDefinition",
    "all_factor_definitions",
    "implemented_factor_definitions",
    "build_factor_scores",
    "build_factor_long_short_returns",
    "train_factor_return_models",
    "build_factor_allocations",
    "backtest_factor_allocations",
    "backtest_stock_score_qspread",
    "backtest_stock_score_long_only_qspread",
    "conservative_cost_tax_assumptions",
    "cost_tax_sensitivity",
    "macro_design_columns",
    "select_factor_universe",
    "AblationPlan",
    "AblationVariant",
    "load_ablation_plan",
    "planned_backlog",
    "runnable_variants",
]
