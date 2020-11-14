import srcmgr
srcmgr.VerifyIsServer()

from . info import StrategicAIInfo, CreateAIForFaction, strategicplayers, EnableStrategicAI, DisableStrategicAI, dbstrategicai
from . base import StrategicAIDefault
from . abilityrules import AbilityRuleBase, AbilityProdRuleRandom, AbilityPlaceBuildingRuleRandom, AbilityPlaceBuildingRuleHintBased
from . groups import GroupBase, GroupGeneric, GroupRandomAttackMove, GroupAttackEnemyBuilding