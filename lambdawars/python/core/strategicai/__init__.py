"""Strategic AI system for Lambda Wars.

Provides AI systems that control CPU players, making strategic decisions about
unit production, building placement, and combat tactics. The AI uses ability
rules and group behaviors to execute game plans.
"""
import srcmgr
srcmgr.VerifyIsServer()

from . info import StrategicAIInfo, CreateAIForFaction, strategicplayers, EnableStrategicAI, DisableStrategicAI, dbstrategicai
from . base import StrategicAIDefault
from . abilityrules import AbilityRuleBase, AbilityProdRuleRandom, AbilityPlaceBuildingRuleRandom, AbilityPlaceBuildingRuleHintBased
from . groups import GroupBase, GroupGeneric, GroupRandomAttackMove, GroupAttackEnemyBuilding