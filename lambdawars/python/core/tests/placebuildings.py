from unittest.util import strclass
from srctests.gametestcase import GenericGameTestCase
from srctests.gametestsuite import GameTestSuite
from vmath import Vector

from playermgr import OWNER_LAST, SimulatedPlayer
from gamemgr import dblist
from core.buildings import WarsBuildingInfo
from core.units import GetUnitInfo, PrecacheUnit, CreateUnit
from core.abilities import CreateAbility

def CreatePlaceBuildingsTestSuite():
    suite = GameTestSuite(suitename='placebuildings')

    for name, info in dblist['units'].items():
        unitinfo = GetUnitInfo(name)
        if not unitinfo or not issubclass(unitinfo, WarsBuildingInfo) or suite.name in unitinfo.exclude_from_testsuites:
            continue
            
        suite.addTest(GamePlaceBuildingTestCase(unitname=name))
            
    return suite
    
class GamePlaceBuildingTestCase(GenericGameTestCase):
    ''' Tests placing a building at the origin on the map unitest1.
    '''
    unitname = None
    
    def __init__(self, unitname='', *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.unitname = unitname
        
    def __str__(self):
        return "test %s (%s)" % (self.unitname, strclass(self.__class__))
        
    def setUp(self):
        super().setUp()
        
        unitname = self.unitname
        
        # TODO: Only do this for the combine buildings, but shouldn't really be part of the core test package.
        self.OnUnitCreated(CreateUnit('build_comb_powergenerator', Vector(-320, 0, 0), owner_number=OWNER_LAST))
        
        self.testsleft = [
            (self.testPlaceBuilding, [unitname]),
        ]
        
    def testPlaceBuilding(self, unitname):
        unitinfo = GetUnitInfo(unitname)
        
        position = Vector(0, 0, 16)
        if unitinfo.placeatmins:
            PrecacheUnit(unitinfo.name)
            position.z += -unitinfo.mins.z
        
        ability = CreateAbility(unitinfo.name, SimulatedPlayer(OWNER_LAST), ischeat=True, skipcheck=True, forcedserveronly=True)
        validposition = ability.IsValidPosition(position)
        self.assertTrue(validposition, msg='Not a valid position: %s' % (ability.debugvalidposition))
        ability.Cancel()