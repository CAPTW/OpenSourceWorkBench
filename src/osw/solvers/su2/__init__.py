"""Optional SU2 adapter surfaces for OSW v0.1."""

from __future__ import annotations

from .adapter import Su2BasicAdapter
from .config import (
    Su2BoundaryConfig,
    Su2ConfigError,
    Su2ConfigGenerator,
    Su2GeneratedConfig,
    Su2SimulationConfig,
    generate_su2_config,
)
from .residuals import Su2ResidualParser, Su2ResidualPoint, Su2ResidualSeries
from .runner import Su2Runner

__all__ = [
    "Su2BasicAdapter",
    "Su2BoundaryConfig",
    "Su2ConfigError",
    "Su2ConfigGenerator",
    "Su2GeneratedConfig",
    "Su2ResidualParser",
    "Su2ResidualPoint",
    "Su2ResidualSeries",
    "Su2Runner",
    "Su2SimulationConfig",
    "generate_su2_config",
]
