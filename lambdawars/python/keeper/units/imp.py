from srcbase import DMG_SLASH
from vmath import Vector, QAngle
from .basekeeper import UnitBaseKeeper as BaseClass, UnitKeeperInfo
from unit_helper import UnitAnimConfig, LegAnimType_t
from entities import entity, Activity, ACT_INVALID
import random
from keeper import keeperworld

if isserver:
    from .behavior import BehaviorImp
    from entities import SpawnBlood
    from unit_helper import BaseAnimEventHandler, EmitSoundAnimEventHandler
else:
    from core.signals import FireSignalRobust, refreshhud
    
@entity('unit_imp', networked=True)
class UnitImp(BaseClass):
    def Precache(self):
        super(UnitImp, self).Precache()
        
        self.PrecacheScriptSound('Imp.ConvertTile')
        self.PrecacheScriptSound('Imp.FortifyWall')
        self.PrecacheScriptSound('Imp.Dig')
        self.PrecacheScriptSound('Imp.FootstepLeft')
        self.PrecacheScriptSound('Imp.FootstepRight')
        self.PrecacheScriptSound('Imp.Hang')
        self.PrecacheScriptSound('Imp.Drop')
        
        self.PrecacheScriptSound('Misc.CoinDrop')
        self.PrecacheScriptSound('Misc.CoinSack')

        self.PrecacheScriptSound( "Shaman.Pain" )
        self.PrecacheScriptSound( "Shaman.Die" )
        
    def Spawn(self):
        super(UnitImp, self).Spawn()
        
        self.nextregenhp = gpGlobals.curtime
        
        if isserver:
            self.skin = random.randint(0, 4)
            #self.SetBodygroup(self.BG_HEAD, random.randint(0, 3))
            #self.SetBodygroup(self.BD_UPPERBODY, random.randint(0, 7))
            
        if isclient:
            FireSignalRobust(refreshhud)
            
    if isclient:
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super(UnitImp, self).UpdateOnRemove()
            
            FireSignalRobust(refreshhud)
            
    def UnitThink(self):
        super(UnitImp, self).UnitThink()
        
        if self.health < self.maxhealth and gpGlobals.curtime > self.nextregenhp:
            kw = keeperworld.keeperworld
            if kw:
                tile = kw.tilegrid[self.key]
                if tile and tile.GetOwnerNumber() == self.GetOwnerNumber():
                    self.health = self.health + 1
                    self.nextregenhp = gpGlobals.curtime + 2.5
    
    def ShouldContinueTraining(self):
        return True # Keep training, until told otherwise
        
    def StartMeleeAttack(self, enemy):
        # By default, assume the attack animation fires
        # an event which does the actually attack
        self.DoAnimation(self.ANIM_MELEE_ATTACK1, 2048)
        self.nextattacktime = gpGlobals.curtime + self.unitinfo.AttackMelee.attackspeed
        return True
            
    def MeleeAttack(self, distance, damage, viewpunch, shove):
        attackinfo = self.unitinfo.AttackMelee
        enthurt = self.CheckTraceHullAttack(distance, -Vector(16,16,32), Vector(16,16,32), damage, attackinfo.damagetype, 1.2, False)
        if enthurt:
            # Play a random attack hit sound
            self.EmitSound("Imp.Dig")
            SpawnBlood(enthurt.GetAbsOrigin(), Vector(0,0,1), self.BloodColor(), damage)
        else:
            self.EmitSound("ASW_Drone.Swipe")
            
    # Anim event handlers
    def ImpAttack(self, event):
        attackinfo = self.unitinfo.AttackMelee
        self.MeleeAttack(attackinfo.maxrange, attackinfo.damage, QAngle( 20.0, 0.0, -12.0 ), Vector( -250.0, 1.0, 1.0 )) 

    def CarryGold(self, gold):
        gold.carriedbyimp = self.GetHandle() # FIXME: TEMP HACK. Otherwise it will immediately try to merge again
        if gold.goldvalue > 100:
            gold.SplitOffGold(gold.goldvalue - 100)
        gold.AttachToImp(self)
        self.carryinggold = gold.GetHandle()
        
    def DropGold(self):
        gold = self.carryinggold
        if gold:
            gold = gold.AttachToImp(None)
            self.carryinggold = None
            self.EmitAmbientSound(-1, self.GetAbsOrigin(), 'Misc.CoinSack')
            return gold
        return None
        
    # Activity list
    activitylist = list(BaseClass.activitylist)
    activitylist.extend( [
        'ACT_SPRAY',
    ] )
    
    # Translation table
    acttables = {
        Activity.ACT_MELEE_ATTACK1 : 'ACT_SPRAY',
    }
    
    if isserver:
        BehaviorGenericClass = BehaviorImp
        
        # Anim events
        aetable = {
            'AE_SHAMAN_SPRAY_START' : ImpAttack,
            'AE_SHAMAN_SPRAY_END' : BaseAnimEventHandler(),
        }
        
    # Vars
    maxspeed = 270.0
    yawspeed = 40.0
    jumpheight = 40.0
    candigblocks = True
    nextregenhp = 0.0
    
    carryinggold = None
    canexecutetasks = True
    
class ImpInfo(UnitKeeperInfo):
    cls_name = 'unit_imp'
    hulltype = 'HULL_MEDIUM'
    name = 'unit_imp'
    abilities = {
        8 : 'attackmove',
        9 : 'holdposition',
    }
    image_name = 'vgui/units/unit_rebel.vmt'
    costs = []
    buildtime = 1.5
    health = 30
    viewdistance = 300
    attackpriority = -3 # trash, they flee
    displayname = 'Imp'
    description = 'An imp!'
    modelname = 'models/aliens/shaman/shaman.mdl'
    #modelname = 'models/swarm/drone/drone.mdl'
    #modelname = 'models/infected/common_male01.mdl'
    sound_select = ''#'Imp.Eew'
    sound_move = 'Imp.Eew'
    sound_death = 'Imp.Die'
    
    hangsound = 'Imp.Eew' # 'Imp.Hang' # FIXME: loops for whatever reason
    dropsound = 'Imp.Drop'
    
    class AttackMelee(UnitKeeperInfo.AttackMelee):
        maxrange = 32.0
        damage = 2 # Pretty weak
        damagetype = DMG_SLASH
        attackspeed = 0.5
    attacks = 'AttackMelee'
    