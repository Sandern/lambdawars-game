from vmath import *
from . units import GenericGameUnitTestCase
from srctests.gametestsuite import GameTestSuite
from playermgr import OWNER_NEUTRAL, OWNER_ENEMY, OWNER_LAST
from fow import FogOfWarMgr

from playermgr import SimulatedPlayer
if isserver:
    from entities import CreateEntityByName, DispatchSpawn, variant_t, MouseTraceData

def CreateUnitAttackPropTestSuite():
    suite = GameTestSuite()
    suite.addTest(UnitAttackPropTestCase())
    return suite
    
class UnitAttackPropTestCase(GenericGameUnitTestCase):
    ''' Tests a soldier attacking a prop by using the "Attack Move" ability.
    '''
    def setUp(self):
        super(UnitAttackPropTestCase, self).setUp()
        
        self.testsleft = [
            (self.testAtackProp, []),
            (self.testIsEnemy, []),
            (self.testAttackResult, []),
        ]
        
    def testAtackProp(self):
        ''' Spawns the unit and prop and performs attack move. '''
        ownernumber = OWNER_LAST
        unitname = 'unit_combine'
        unitmsg = 'unit: %s, owner: %d' % (unitname, ownernumber)
        
        spawnspot = self.GetPositionByTargetName('target_origin')
        propspot = self.GetPositionByTargetName('target_min_512')
        
        # Create unit
        unit = self.CreateUnit('unit_combine', spawnspot, owner_number=ownernumber)
        self.assertIsNotNone(unit, msg=unitmsg)
        self.unit = unit
        
        # Create prop
        prop = CreateEntityByName( "prop_physics" )
        prop.KeyValue('model', 'models/props_c17/oildrum001_explosive.mdl')
        prop.SetAbsOrigin(propspot)
        prop.AcceptInput('Wake', None, None, variant_t(), 0)
        DispatchSpawn( prop )
        prop.Activate()
        prop.health = 5
        self.prop = prop
        
        # Perform attack move on the prop
        leftpressed = MouseTraceData()
        leftpressed.endpos = propspot
        leftpressed.groundendpos = propspot
        leftpressed.ent = prop
        mouse_inputs=[('leftpressed', leftpressed)]
        unit.DoAbility('attackmove', mouse_inputs)

        return 0.5
        
    def testIsEnemy(self):
        ''' Test if the prop has become the enemy of the unit. '''
        self.assertTrue(self.unit.enemy == self.prop)
        return 3.0
        
    def testAttackResult(self):
        ''' Tests if the prop was destroyed. '''
        self.assertTrue(self.prop == None, msg='Prop is not none! -> %s' % (self.prop))
        
    def tearDown(self):
        super(UnitAttackPropTestCase, self).tearDown()
        
        if self.prop:
            self.prop.Remove()
        
    prop = None