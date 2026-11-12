"""Frontline mode helpers (roles, FP, respawn, camera, body switch).

Design: docs/design/commander_captains_mode.md
Feasibility: docs/design/frontline_feasibility.md

Gamerules entry point: wars_game.gamerules.frontline
"""

from .roles import (
    ROLE_COMMANDER,
    ROLE_CAPTAIN,
    ROLE_SPECTATOR,
    FrontlineRoleHelper,
)
from .faction_points import FrontlineFactionPoints
from .respawn import FrontlineRespawnQueue
from .camera import FrontlineCameraPolicy
from .body_switch import FrontlineBodySwitch
from .milestones import FrontlineMilestones

__all__ = [
    'ROLE_COMMANDER',
    'ROLE_CAPTAIN',
    'ROLE_SPECTATOR',
    'FrontlineRoleHelper',
    'FrontlineFactionPoints',
    'FrontlineRespawnQueue',
    'FrontlineCameraPolicy',
    'FrontlineBodySwitch',
    'FrontlineMilestones',
]
