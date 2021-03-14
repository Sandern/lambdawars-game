from srcbase import DONT_BLEED, kRenderFxNoDissipation, kRenderGlow, SOLID_NONE, SOLID_VPHYSICS
from vmath import Vector, QAngle
from entities import networked, entity, Activity
from fields import BooleanField

from core.units import (UnitInfo, UnitBaseCombat as BaseClass, UnitBaseAirLocomotion, CreateUnitNoSpawn,
    EventHandlerAnimation, GetUnitInfo)

if isserver:
    from core.units import UnitCombatAirNavigator
    from entities import CSprite, CGib
    from utils import UTIL_Remove, UTIL_PrecacheOther

@networked
class UnitBaseScanner(BaseClass):
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
    
    def __init__(self):
        super().__init__()
        self.savedrop = 2048.0
        self.maxclimbheight = 2048.0
        self.testroutestartheight = 2048.0
        
    def Precache(self):
        super().Precache()
        
        # Sprites
        m_nHaloSprite = self.PrecacheModel("sprites/light_glow03.vmt")
        self.PrecacheModel("sprites/glow_test02.vmt")
        
    def Spawn(self):    
        super().Spawn()
        
        self.SetBloodColor(DONT_BLEED)
        self.locomotion.desiredheight = 370.0
        self.locomotion.flynoiserate = 32.0
        self.locomotion.flynoisez = 24.0

    if isserver:
        def UpdateOnRemove(self):
            super().UpdateOnRemove()
            
            # Remove sprite
            UTIL_Remove(self.eyeflash)
            self.eyeflash = None
            
        def Event_Killed(self, info):
            super().Event_Killed(info)
            
            # Remove sprite
            UTIL_Remove(self.eyeflash)
            self.eyeflash = None
            
        def ShouldGib(self, info):
            return True
            
        def CorpseGib(self, info):
            # Cover the gib spawn
            #ExplosionCreate(self.WorldSpaceCenter(), self.GetAbsAngles(), self, 64, 64, False)
            
            return True
            
        def Activate(self):
            super().Activate()

            # Have to do this here because sprites do not go across level transitions
            self.eyeflash = CSprite.SpriteCreate( "sprites/blueflare1.vmt", self.GetLocalOrigin(), False )
            self.eyeflash.SetTransparency( kRenderGlow, 255, 255, 255, 0, kRenderFxNoDissipation )
            self.eyeflash.SetAttachment( self, self.LookupAttachment( "light" ) )
            self.eyeflash.SetBrightness( 0 )
            self.eyeflash.SetScale( 1.4 )
            
        def AttackFlash(self):
            self.EmitSound( "%s.AttackFlash" % (self.soundprefix) )
            self.eyeflash.SetScale( 1.8 )
            self.eyeflash.SetBrightness( 255 )
            self.eyeflash.SetColor(255,255,255)

            #if self.enemy:
                #Vector pos = GetEnemyLKP()
                #CBroadcastRecipientFilter filter
                #te->DynamicLight( filter, 0.0, &pos, 200, 200, 255, 0, 300, 0.2, 50 )
                
            self.SetThink(self.EndAttackFlashThink, gpGlobals.curtime + 0.1, 'EndAttackFlashThink')
                
        def EndAttackFlashThink(self):
            self.eyeflash.SetBrightness( 0 )
        
    selectionparticlename = 'unit_circle_ground'
    cancappcontrolpoint = False
    
    soundprefix = ''
    eyeflash = None
    
    abilitysounds = {
        'holdposition' : 'ability_comb_scanner_holdposition',
    }

@entity('unit_cscanner', networked=True)
class UnitScanner(UnitBaseScanner):
    @classmethod
    def PrecacheUnitType(cls, info):
        super().PrecacheUnitType(info)
        
        cls.combinemineinfo = GetUnitInfo('combine_mine')

        if info == ClawScannerInfo:
            cls.PrecacheModel("models/shield_scanner.mdl")

            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib1.mdl")
            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib2.mdl")
            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib3.mdl")
            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib4.mdl")
            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib5.mdl")
            cls.PrecacheModel("models/gibs/Shield_Scanner_Gib6.mdl")

            cls.PrecacheScriptSound( "NPC_SScanner.Shoot")
            cls.PrecacheScriptSound( "NPC_SScanner.Alert" )
            cls.PrecacheScriptSound( "NPC_SScanner.Die" )
            cls.PrecacheScriptSound( "NPC_SScanner.Combat" )
            cls.PrecacheScriptSound( "NPC_SScanner.Idle" )
            cls.PrecacheScriptSound( "NPC_SScanner.Pain" )
            cls.PrecacheScriptSound( "NPC_SScanner.TakePhoto" )
            cls.PrecacheScriptSound( "NPC_SScanner.AttackFlash" )
            cls.PrecacheScriptSound( "NPC_SScanner.DiveBombFlyby" )
            cls.PrecacheScriptSound( "NPC_SScanner.DiveBomb" )
            cls.PrecacheScriptSound( "NPC_SScanner.DeployMine" )

            cls.PrecacheScriptSound( "NPC_SScanner.FlyLoop" )
            UTIL_PrecacheOther("combine_mine")
        else:
            cls.PrecacheModel("models/gibs/scanner_gib01.mdl" )
            cls.PrecacheModel("models/gibs/scanner_gib02.mdl" )
            cls.PrecacheModel("models/gibs/scanner_gib02.mdl" )
            cls.PrecacheModel("models/gibs/scanner_gib04.mdl" )
            cls.PrecacheModel("models/gibs/scanner_gib05.mdl" )

            cls.PrecacheScriptSound( "NPC_CScanner.Shoot")
            cls.PrecacheScriptSound( "NPC_CScanner.Alert" )
            cls.PrecacheScriptSound( "NPC_CScanner.Die" )
            cls.PrecacheScriptSound( "NPC_CScanner.Combat" )
            cls.PrecacheScriptSound( "NPC_CScanner.Idle" )
            cls.PrecacheScriptSound( "NPC_CScanner.Pain" )
            cls.PrecacheScriptSound( "NPC_CScanner.TakePhoto" )
            cls.PrecacheScriptSound( "NPC_CScanner.AttackFlash" )
            cls.PrecacheScriptSound( "NPC_CScanner.DiveBombFlyby" )
            cls.PrecacheScriptSound( "NPC_CScanner.DiveBomb" )
            cls.PrecacheScriptSound( "NPC_CScanner.DeployMine" )

            cls.PrecacheScriptSound( "NPC_CScanner.FlyLoop" )
            
    def CorpseGib(self, info):
        # Cover the gib spawn
        #ExplosionCreate(self.WorldSpaceCenter(), self.GetAbsAngles(), self, 64, 64, False)
    
        # Spawn all gibs
        lifetime = 5.0
        if self.isclawscanner:
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib1.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib2.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib3.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib4.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib5.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/Shield_Scanner_Gib6.mdl", lifetime)
        else:
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/scanner_gib01.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/scanner_gib02.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/scanner_gib04.mdl", lifetime)
            CGib.SpawnSpecificGibs(self, 1, 500, 250, "models/gibs/scanner_gib05.mdl", lifetime)

        self.DeployMine()

        return super().CorpseGib(info)
        
    def Spawn(self):
        super().Spawn()
        
        if self.isclawscanner:
            self.EquipMine()
            
    def OnDataChanged(self, type):
        super().OnDataChanged(type)
            
        hasmine = bool(self.GetEquipedMine())
        if hasmine != self.hasequipedmine:
            self.UpdateAbilities()
            self.hasequipedmine = hasmine
            
    def GetEquipedMine(self):
        """ Returns the first found equiped mine if any. """
        child = self.FirstMoveChild()
        while child:
            if child.IsUnit() and issubclass(child.unitinfo, self.combinemineinfo):
                # Already have a mine!
                return child
            child = child.NextMovePeer()
        return None
        
    def DeployMine(self):
        # iterate through all children
        mine = self.GetEquipedMine()
        if mine:
            mine.SetParent(None)
            mine.SetAbsVelocity(self.GetAbsVelocity())
            mine.SetOwnerEntity(self)
            mine.SetSolid(SOLID_VPHYSICS)

            self.EmitSound("%s.DeployMine" % (self.soundprefix))

            pPhysObj = mine.VPhysicsGetObject()
            if pPhysObj:
                # Make sure the mine's awake
                pPhysObj.Wake()
                # Fold up?
                # SetActivity( ACT_DISARM )
                
            self.UpdateAbilities()
        return mine

    def StartProducingMine(self, productiontime):
        if self.isproducingmine:
            return False
        self.isproducingmine = True
        self.mineproductionendtime = gpGlobals.curtime + productiontime
        self.SetThink(self.ResupplyMineThink, self.mineproductionendtime, 'ResupplyMineThink')
        return True
        
    def EquipMine(self):
        mine = self.GetEquipedMine()
        if mine:
            # Already have a mine!
            return

        pEnt = CreateUnitNoSpawn("combine_mine", owner_number=self.GetOwnerNumber())
        placedmine = False

        if self.isclawscanner:
            vecOrigin = Vector()
            angles = QAngle()

            attachment = self.LookupAttachment("claw")

            if attachment > -1:
                self.GetAttachment(attachment, vecOrigin, angles)
                
                pEnt.SetAbsOrigin(vecOrigin)
                pEnt.SetAbsAngles(angles)
                pEnt.SetOwnerEntity(self)
                pEnt.SetParent(self, attachment)
                pEnt.SetSolid(SOLID_NONE)

                self.isopen = True
                #SetActivity( ACT_IDLE_ANGRY )
                placedmine = True

        if not placedmine:
            vecMineLocation = self.GetAbsOrigin()
            vecMineLocation.z -= 32.0

            pEnt.SetAbsOrigin( vecMineLocation )
            pEnt.SetAbsAngles( self.GetAbsAngles() )
            pEnt.SetOwnerEntity( self )
            pEnt.SetParent( self )

        pEnt.Spawn()
        
        self.UpdateAbilities()
        
    def ResupplyMineThink(self):
        self.EquipMine()
        self.isproducingmine = False
        
    __isproducingmine = BooleanField(value=False, networked=True)

    @property
    def isproducingmine(self):
        return self.__isproducingmine

    @isproducingmine.setter
    def isproducingmine(self, state):
        if self.__isproducingmine == state:
            return
        self.__isproducingmine = state
        
    def ScannerClosedEventHandler(self, data):
        self.isopen = False
        
    @property
    def isclawscanner(self):
        return issubclass(self.unitinfo, ClawScannerInfo)
        
    @property
    def soundprefix(self):
        if self.isclawscanner:
            return 'NPC_SScanner'
        return 'NPC_CScanner'
        
    # Custom activities
    activitylist = list(UnitBaseScanner.activitylist)
    activitylist.extend([
        #'ACT_SSCANNER_OPEN',
        #'ACT_SSCANNER_FLINCH_BACK',
    ])
        
    # Events
    events = dict(UnitBaseScanner.events)
    events.update( {
        'ANIM_DEPLOYMINE' : EventHandlerAnimation(Activity.ACT_DISARM),
    } )
    
    if isserver:
        aetable = {
            'AE_SCANNER_CLOSED' : ScannerClosedEventHandler,
        }
    
    combinemineinfo = None
    isopen = True
    hasequipedmine = False
    detector = True

@entity('unit_clawscanner', networked=True)
class UnitClawScanner(UnitScanner):
    detector = True

@entity('unit_observer')
class UnitObserver(UnitScanner):
    def Spawn(self):
        super().Spawn()
        
        self.Cloak()
        
    cloakenergydrain = 0
    detector = True

class ScannerInfo(UnitInfo):
    name = 'unit_scanner'
    displayname = '#CombScanner_Name'
    description = '#CombScanner_Description'
    cls_name = 'unit_cscanner'
    image_name = 'vgui/combine/units/unit_observer'
    modelname = 'models/combine_scanner.mdl'
    health = 30
    buildtime = 15.0
    costs = [('requisition', 10), ('power', 5)]
    sai_hint = set(['sai_unit_scout', 'sai_unit_combat'])
    attributes = ['mechanic', 'metal']
    sound_death = 'NPC_CScanner.Die'
    maxspeed = 352
    viewdistance = 1152
    
    ability_0 = 'flash'
    ability_9 = 'holdposition'
    ability_10 = 'patrol'
    
    sound_select = 'unit_scanner_select'
    sound_move = 'unit_scanner_move'

class ScannerCharInfo(ScannerInfo):
    name = 'char_scanner'
    health = 10
    unitenergy = 100
    costs = []
    viewdistance = 1200
    population = 0
    buildtime = 0.0
    rechargetime = 30.0
    maxspeed = 300

    ability_0 = 'infiltrate_char'
    ability_1 = 'flash'
    ability_9 = 'holdposition'
    ability_10 = 'patrol'

class ObserverInfo(ScannerInfo):
    name = 'unit_observer'
    displayname = '#CombObserver_Name'
    description = '#CombObserver_Description'
    image_name = 'vgui/combine/units/unit_observer'
    cls_name = 'unit_observer'
    health = 30
    buildtime = 20.0
    costs = [('requisition', 20), ('power', 30)]
    sai_hint = set(['sai_unit_support'])
    sound_death = 'NPC_CScanner.Die'
    maxspeed = 200

class ClawScannerInfo(ScannerInfo):
    name = 'unit_clawscanner'
    cls_name = 'unit_clawscanner'
    displayname = '#CombClawScanner_Name'
    description = '#CombClawScanner_Description'
    image_name = 'vgui/combine/units/unit_clawscanner'
    modelname = 'models/shield_scanner.mdl'
    attributes = ['synth']
    costs = [('requisition', 10), ('power', 20)]
    buildtime = 15.0
    sound_death = 'NPC_SScanner.Die'
    health = 40
    maxspeed = 248
    viewdistance = 1408
    ability_0 = 'deploymine'
    #ability_1 = 'producemine'
    sai_hint = set([])
