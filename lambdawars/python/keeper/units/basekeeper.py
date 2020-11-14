from srcbase import *
from vmath import Vector, VectorNormalize, QAngle, VectorAngles, Vector2D
from core.units import UnitBaseCombat as BaseClass, UnitInfo
from keeper import keeperworld
from entities import networked, entity, CBaseAnimating
from fields import IntegerField, StringField, BooleanField, FloatField
from unit_helper import UnitAnimConfig
from particles import *
from core.hud import InsertResourceIndicator
from core.resources import TakeResources, HasEnoughResources
from keeper.common import GetDungeonHeart

import math
import random

from keeper.tiles import tilespertype
from keeper.rooms import controllerspertype

if isserver:
    from .behavior import BehaviorCreature, BehaviorHero, BehaviorHeroDigger
    from entities import CreateEntityByName, DispatchSpawn, CTakeDamageInfo
    from gameinterface import GameEvent, FireGameEvent
else:
    from utils import MainViewUp, MainViewRight, MainViewForward, GetVectorInScreenSpace
    
STATUS_NONE = -1
STATUS_SLEEPING = 1
STATUS_EATING = 2
STATUS_TRAINING = 3
STATUS_PAYDAY = 4
STATUS_UNHAPPY = 5

if isclient:
    from vgui import cursors, surface, scheme, FontVertex_t, FontDrawType_t
    from vgui.controls import Panel
    from vgui.entitybar import UnitBarScreen, BaseScreen
    
    class CreateHealthLevelPanel(Panel):
        def __init__(self):
            super(CreateHealthLevelPanel, self).__init__()
        
            self.textureid = surface().CreateNewTextureID()
            surface().DrawSetTextureFile(self.textureid, "effects/radialtest" , True, False)
            
        def Paint(self):
            barfilled = int(self.weight * self.GetTall())
        
            #print '%f %d' % (self.weight, int(self.weight*255))
            surface().DrawSetColor(255,255,255, int(self.weight*255))
            surface().DrawSetTexture(self.textureid)
            surface().DrawTexturedRect(0, 0, self.GetWide(), self.GetTall())
            
        weight = 1.0
    
    class CreateHealthLevelScreen(UnitBarScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit):
            super(CreateHealthLevelScreen, self).__init__(unit,
                Color(), Color(40, 40, 40, 250), Color(150, 150, 150, 250), panel=CreateHealthLevelPanel())
                
            self.GetPanel().SetBounds(0, 0, 640, 640)
            
            mins = self.unit.WorldAlignMins()
            maxs = self.unit.WorldAlignMaxs()
            wide = maxs.x - mins.x
            self.SetWorldSize(wide, wide)
        
        def Draw(self):
            if not self.unit:
                return
            panel = self.GetPanel()
            panel.weight = self.unit.HealthFraction()
            panel.barcolor = Color(int(255 - (panel.weight * 200.0)),
                    int(panel.weight * 220.0),
                    20+int(panel.weight*20.0),
                    250)
                    
            super(CreateHealthLevelScreen, self).Draw()
        
    class StatusBalloonPanel(Panel):
        def __init__(self):
            super(StatusBalloonPanel, self).__init__()
        
            self.textureid = surface().CreateNewTextureID()
            surface().DrawSetTextureFile(self.textureid, 'vgui/keeper/statusballoon' , True, False)
            
            statusicons = {
                STATUS_SLEEPING : 'vgui/keeper/statussleeping',
                STATUS_EATING : 'vgui/keeper/statuseating',
                STATUS_TRAINING : 'vgui/keeper/statustraining',
                STATUS_PAYDAY : 'vgui/keeper/statuspayday',
                STATUS_UNHAPPY : 'vgui/keeper/statusunhappy',
            }
        
            self.statustextures = {}
            for k, v in statusicons.items():
                self.statustextures[k] = surface().CreateNewTextureID()
                surface().DrawSetTextureFile(self.statustextures[k], v , True, False)

        def Paint(self):
            if not self.curstatus:
                return
                
            drawpoints = [
                FontVertex_t(Vector2D(0,0), Vector2D(0,1)),
                FontVertex_t(Vector2D(self.GetWide(),0) , Vector2D(0,0)),
                FontVertex_t(Vector2D(self.GetWide(),self.GetTall()), Vector2D(1,0)),
                FontVertex_t(Vector2D(0,self.GetTall()), Vector2D(1,1)),
                               
            ]
            surface().DrawSetColor(255,255,255, 255)
            
            surface().DrawSetTexture(self.textureid)
            surface().DrawTexturedPolygon(drawpoints)
            
            surface().DrawSetTexture(self.statustextures[self.curstatus])
            surface().DrawTexturedPolygon(drawpoints)
            
        curstatus = None
            
    class StatusBalloonScreen(BaseScreen):
        """ Draws the unit health bar. """
        def __init__(self, unit, offsety=0.0):
            super(StatusBalloonScreen, self).__init__()
                
            self.offsety = offsety
            
            self.unit = unit
            self.SetPanel(unit.statusballoonpanel)
            self.GetPanel().SetBounds(0, 0, 640, 640)
            
            mins = self.unit.WorldAlignMins()
            maxs = self.unit.WorldAlignMaxs()
            wide = maxs.x - mins.x
            wide /= 2.0
            self.SetWorldSize(wide, wide)

        def Draw(self):
            if not self.unit:
                return
                
            maxs = self.unit.WorldAlignMaxs()
            
            origin = self.unit.GetAbsOrigin() + MainViewRight()*(self.GetHeight()/2)
            origin.z += maxs.z
            origin += MainViewUp()*(8.0 + self.offsety)
            self.SetOrigin( origin )
            
            angles = QAngle()
            dir = MainViewUp()
            VectorAngles(dir, angles)
            self.SetAngles(angles)
                
            super(StatusBalloonScreen, self).Draw()
            
@networked
class UnitBaseKeeper(BaseClass):
    def __init__(self):
        super(UnitBaseKeeper, self).__init__()
        
        # Set to MASK_SOLID, otherwise they sense through the wall.
        # Probably due the model/materials, but can't bother to fix it (resulting in a grate/window content type).
        self.attacklosmask = MASK_SOLID
        
        if isclient:
            self.statusballoonpanel = StatusBalloonPanel()

    if isclient:
        def EnableGlow(self, enable):
            super(UnitBaseKeeper, self).EnableGlow(True) # Always glow
            
        def OnHoverPaint(self):
            pos = self.EyePosition()
            pos.z += 32.0
            success, x, y = GetVectorInScreenSpace(pos)
            if not success:
                return
            s = surface()
            
            levelstr = 'Level %s' % (str(self.level))
            wide, tall = s.GetTextSize(self.hfontsmall, levelstr)
            
            s.DrawSetTextFont(self.hfontsmall)
            s.DrawSetTextColor(255, 255, 255, 255)
            s.DrawSetTextPos(int(x - wide/2.0), y)
            s.DrawUnicodeString('Level %s' % (str(self.level)), FontDrawType_t.FONT_DRAW_DEFAULT)
            
            # For debug
            if hasattr(self, 'happinessnetworked'):
                s.DrawSetTextFont(self.hfontsmall)
                s.DrawSetTextColor(0, 255, 255, 255)
                s.DrawSetTextPos(int(x - wide/2.0), y+32)
                s.DrawUnicodeString('Happiness %s' % (str(self.happinessnetworked)), FontDrawType_t.FONT_DRAW_DEFAULT)
                
            
        def Spawn(self):
            super(UnitBaseKeeper, self).Spawn()
            
            self.EnableGlow(True)
            
            schemeid = scheme().LoadSchemeFromFile("resource/GameLobbyScheme.res", "GameLobbyScheme")
            schemeobj = scheme().GetIScheme(schemeid)
            self.hfontsmall = schemeobj.GetFont("HeadlineLarge")
            
        def OnChangeOwnerNumber(self, oldownernumber):
            super(UnitBaseKeeper, self).OnChangeOwnerNumber(oldownernumber)
            
            self.EnableGlow(True) # Update color
            
        def UpdateOnRemove(self):
            # ALWAYS CHAIN BACK!
            super(UnitBaseKeeper, self).UpdateOnRemove()
            
            self.creaturestatus = STATUS_NONE
            self.OnCreatureStatusChanged()
        
        '''
        def ShowBars(self):
            if self.barsvisible:
                return
            #self.healthbarscreen = CreateStatusScreen(self)
            self.statusscreen = StatusBalloonScreen(self)
            
            self.barsvisible = True
            
        def HideBars(self):
            if not self.barsvisible:
                return
            #self.healthbarscreen.Shutdown()
            #self.healthbarscreen = None
            self.statusscreen.Shutdown()
            self.statusscreen = None
            
            self.barsvisible = False
        '''
        
        def OnCreatureStatusChanged(self):
            if self.creaturestatus != STATUS_NONE:
                if self.creaturestatus not in self.statusballoonpanel.statustextures:
                    PrintWarning('#%d OnCreatureStatusChanged: invalid creature status %s\n' % (self.entindex(), self.creaturestatus))
                    return
                if not self.statusscreen:
                    self.statusscreen = StatusBalloonScreen(self)
                self.statusballoonpanel.curstatus = self.creaturestatus
            elif self.statusscreen:
                self.statusscreen.Shutdown()
                self.statusscreen = None
        
    def IsSelectableByPlayer(self, player, target_selection):
        return False
        
    def Order(self, player):
        pass # Don't do anything when selected
        
    def RebuildAttackInfo(self):
        super(UnitBaseKeeper, self).RebuildAttackInfo()
        
        # Just scale the damage of our attacks by our level
        for a in self.attacks:
            a.damage = (a.damage * max(1, self.level * 0.75))
            
        self.digdamage = int(self.basedigdamage * max(1, self.level * 0.75))
            
    # Training
    def CanTrain(self):
        if not self.unitinfo.traincost:
            return True
        return HasEnoughResources([('gold', self.unitinfo.traincost)], self.GetOwnerNumber())
        
    def FindTrainRoom(self):
        trainrooms = list(controllerspertype[self.GetOwnerNumber()]['dk_training_controller'])
        trainrooms = [r for r in trainrooms if not r.IsFull()]
        if not trainrooms:
            return None
        return random.sample(trainrooms, 1)[0]

    def StartTraining(self):
        self.creaturestatus = STATUS_TRAINING
        self.trainroom = self.FindTrainRoom()
        if self.trainroom:
            self.trainroom.creaturesusingroom.add(self.GetHandle())
        
    def EndTraining(self):
        if self.trainroom:
            self.trainroom.creaturesusingroom.discard(self.GetHandle())
        self.creaturestatus = STATUS_NONE
        self.nexttraintime = gpGlobals.curtime + random.randint(10, 30)
        self.trainroom = None
        
    def DoTraining(self):
        ''' Execute a training interval.
            Expects the unit to play an animation. '''
        if self.unitinfo.traincost:
            if not HasEnoughResources([('gold', self.unitinfo.traincost)], self.GetOwnerNumber()):
                return False, ''
            TakeResources(self.GetOwnerNumber(), [('gold', self.unitinfo.traincost)])
            
        self.AddExperience(self.unitinfo.trainperexp)
        InsertResourceIndicator(self.GetAbsOrigin(), '%s' % (str(self.unitinfo.traincost)))
        
        # Just pick the first attack from our list
        for attack in self.attacks:
            waitingforactivity = attack.Attack(self, None)
            break
            
        return True, waitingforactivity
        
    def ShouldContinueTraining(self):
        return random.random() > 0.1
        
    if isserver:
        def Precache(self):
            super(UnitBaseKeeper, self).Precache()
            
            self.PrecacheScriptSound('Misc.Slap')
            if self.unitinfo.hangsound: self.PrecacheScriptSound(self.unitinfo.hangsound)
            if self.unitinfo.dropsound: self.PrecacheScriptSound(self.unitinfo.dropsound)
            
        def Spawn(self):
            super(UnitBaseKeeper, self).Spawn()
            
            self.navigator.noavoid = True

            self.senses.testlos = True
            #self.SetCollisionGroup(self.CalculateIgnoreOwnerCollisionGroup())
            self.SetCollisionGroup(WARS_COLLISION_GROUP_IGNORE_ALL_UNITS)
            
            if not self.ishero:
                self.SetBloodColor(BLOOD_COLOR_GREEN)
                
            self.heart = GetDungeonHeart(self.GetOwnerNumber())
        
        def PerformGrabbedLocomotion(self):
            self.mv.interval = gpGlobals.curtime - self.GetLastThink()
            
            if self.grabbedbyplayer:
                data = self.grabbedbyplayer.GetMouseData()
                
                pos = data.groundendpos + Vector(0, 0, 96.0)
                self.SetAbsOrigin(pos)
                
                self.mv.origin = pos
                self.locomotion.CategorizePosition()
            
            self.simulationtime = gpGlobals.curtime
            
        def PlayerGrab(self, player, release=False):
            if not release:
                if self.GetHandle() not in player.grabbedunits and player.GetOwnerNumber() == self.GetOwnerNumber():
                    self.fnoriginallocomotion = self.PerformLocomotion
                    self.grabbedbyplayer = player
                    self.PerformLocomotion = self.PerformGrabbedLocomotion
                    player.grabbedunits.append(self.GetHandle())
                    self.AddSolidFlags(FSOLID_NOT_SOLID)
                    
                    if self.unitinfo.hangsound:
                        self.EmitAmbientSound(-1, self.GetAbsOrigin(), self.unitinfo.hangsound)
                        
                    self.DispatchEvent('OnPlayerGrab')
                    
                    event = GameEvent('sk_playergrabbed')
                    event.SetInt("entindex", self.entindex())
                    FireGameEvent(event)
            else:
                kw = keeperworld.keeperworld
                canrelease = True
                if kw:
                    tile = kw.tilegrid[self.key]
                    if tile.isblock or tile.GetOwnerNumber() != player.GetOwnerNumber():
                        canrelease = False

                if canrelease and self.GetHandle() in player.grabbedunits:
                    self.grabbedbyplayer = None
                    
                    if self.fnoriginallocomotion:
                        self.PerformLocomotion = self.fnoriginallocomotion
                    try:
                        player.grabbedunits.remove(self.GetHandle())
                    except ValueError:
                        pass
                    self.RemoveSolidFlags(FSOLID_NOT_SOLID)
                    
                    if self.unitinfo.dropsound:
                        self.EmitAmbientSound(-1, self.GetAbsOrigin(), self.unitinfo.dropsound)
                        
                    event = GameEvent('sk_playerreleased')
                    event.SetInt("entindex", self.entindex())
                    FireGameEvent(event)
                    
            self.UpdateMoveMethods()
            
        def UpdateKey(self):
            # Update position on grid
            kw = keeperworld.keeperworld
            if kw:
                self.key = kw.GetKeyFromPos(self.GetAbsOrigin())
                
        def UnitThink(self):
            self.UpdateKey()
            super(UnitBaseKeeper, self).UnitThink()
            
        def OnClickLeftReleased(self, player):
            self.PlayerGrab(player)
        
        def OnClickRightReleased(self, player):
            if player.GetOwnerNumber() != self.GetOwnerNumber():
                return
               
            self.Slap(player)
                
        def Slap(self, player):
            # Slap!
            self.EmitSound('Misc.Slap')
            info = CTakeDamageInfo(None, None, 5, 0)
            self.TakeDamage(info)
            
            azimuth = random.random() * 2 * math.pi;
            dir = Vector(math.cos(azimuth), math.sin(azimuth), 0.0)
            VectorNormalize(dir)

            # NOTE: Don't add extra speed if we are in the air, otherwise you can keep slapping the creature up.
            if self.GetGroundEntity():
                speed = 250.0
                self.SetGroundEntity(None)
                self.SetAbsVelocity(dir * speed + Vector(0, 0, 400.0))
                
            self.lasttaskkey = None
            
            self.DispatchEvent('OnSlap')
            
        def OnNewLevel(self):
            self.maxhealth = int(self.maxhealth * 2)
            self.health += int(self.maxhealth / 2)
            print('#%d Creature advanced to level %d' % (self.entindex(), self.level))
        
        def AddExperience(self, experience):
            self.experience += experience
            while self.experience >= self.nextlevel:
                self.level += 1
                self.nextlevel *= 2
                self.OnNewLevel()
                
        def IncreaseSpeedTemporary(self, scalespeed, time):
            if self.speedincrease:
                PrintWarning('IncreaseSpeedTemporary: Speed already increased!\n')
                return
            newspeed = self.mv.maxspeed * scalespeed
            self.speedincrease = newspeed - self.mv.maxspeed
            self.mv.maxspeed = newspeed
            self.SetThink(self.IncreaseSpeedEnd, gpGlobals.curtime + time, 'IncreaseSpeedEnd')
            
        def IncreaseSpeedEnd(self):
            self.mv.maxspeed -= self.speedincrease
            self.speedincrease = 0

    grabbedbyplayer = None
    fnoriginallocomotion = None
    key = (0,0)
    
    #: Current level of this creature.
    level = IntegerField(value=1, networked=True)
    experience = 0
    nextlevel = 600
    #: If this unit can dig blocks (otherwise damage is ignored by a block)
    candigblocks = BooleanField(value=False)
    #: Used by blocks to determine if this unit is digging that block
    targetblock = None
    #: Dig damage of this unit (overrides attack damage)
    basedigdamage = 15
    #: Whether this unit is a hero.
    ishero = BooleanField(value=False)
    #: Target dungeon heart of hero
    targetheart = None
    #: If this creature is currently executing a task.
    executingtask = False
    #: If this creature can execute tasks by the taskqueue.
    canexecutetasks = False
    #: Key of the last task we executed
    lasttaskkey = None
    #: Handle to dungeon heart entity
    heart = None
    #: Handle to train room if training
    trainroom = None
    #: Current status of the creature. Used for displaying the activity on the client.
    creaturestatus = IntegerField(value=STATUS_NONE, networked=True, clientchangecallback='OnCreatureStatusChanged')
    # eye offset of the alien swarm models sucks
    customeyeoffset = Vector(0,0,32.0)
    #: Current speed increase of the unit
    speedincrease = 0
    
    grabreleased = False
    
    if isclient:
        statusscreen = None
        
    if isserver:
        def CreateBehaviors(self):
            if self.ishero:
                if self.candigblocks:
                    self.AddBehavior('behaviorgeneric', self.BehaviorHeroDiggerClass(self))
                else:
                    self.AddBehavior('behaviorgeneric', self.BehaviorHeroClass(self))
            else:
                self.AddBehavior('behaviorgeneric', self.BehaviorGenericClass(self))
    
        BehaviorGenericClass = BehaviorCreature
        BehaviorHeroClass = BehaviorHero
        BehaviorHeroDiggerClass = BehaviorHeroDigger
        
    # Animation State
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=180.0,
        bodyyawnormalized=True,
        invertposeparameters=False,
    )
    class AnimStateClass(BaseClass.AnimStateClass):
        def __init__(self, outer, animconfig):
            super(UnitBaseKeeper.AnimStateClass, self).__init__(outer, animconfig)
            self.newjump = False
        
        def OnNewModel(self):
            super(UnitBaseKeeper.AnimStateClass, self).OnNewModel()

            self.bodyyaw = self.outer.LookupPoseParameter("aim_yaw")
            #self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")
            
            bodypitch = self.outer.LookupPoseParameter("aim_pitch")
            if bodypitch >= 0:
                self.outer.SetPoseParameter(bodypitch, 0.0) # Just set fixed for now
                
@entity('creaturelair')
class Lair(CBaseAnimating):
    def Precache(self):
        PrecacheParticleSystem('acid_touch_smoke')

    def Spawn(self):
        self.Precache()
        
        super(Lair, self).Spawn()
        
        self.SetModel(self.GetModelName())
        
        DispatchParticleEffect('acid_touch_smoke', PATTACH_ABSORIGIN, self)
        
        
class UnitBaseCreature(UnitBaseKeeper):
    if isserver:
        def Precache(self):
            super(UnitBaseCreature, self).Precache()
            
            self.PrecacheModel(self.unitinfo.lairmodel)
            PrecacheParticleSystem('pg_heal')
            
        def Spawn(self):
            self.creatureentertime = gpGlobals.curtime
            self.lasteattime = gpGlobals.curtime
            self.lasthadlairtime = gpGlobals.curtime
            
            self.nextrandomsleeptime = gpGlobals.curtime + random.randint(20, 25)
            self.nexteattime = gpGlobals.curtime + random.randint(20, 25)
            self.nexttraintime = gpGlobals.curtime + random.randint(20, 50)
        
            super(UnitBaseCreature, self).Spawn() 
 
    def UpdateOnRemove(self):
        # ALWAYS CHAIN BACK!
        super(UnitBaseCreature, self).UpdateOnRemove()
        
        if self.lair:
            self.lair.Remove()
            self.lair = None
            
    def UnitThink(self):
        super(UnitBaseCreature, self).UnitThink()
        
        self.UpdateHappiness()
            
    def FindLair(self):
        freelairs = [l for l in tilespertype[self.GetOwnerNumber()]['lair'] if not l.attachedlair]
        if not freelairs:
            return None
        return random.sample(freelairs, 1)[0]

    def CreateLair(self, tile):
        assert(tile.type == 'lair')
        
        origin = tile.GetAbsOrigin()
        origin.z += 32.0
        
        self.lair = CreateEntityByName('creaturelair')
        self.lair.SetModelName(self.unitinfo.lairmodel)
        self.lair.SetAbsOrigin(origin)
        self.lair.SetOwnerEntity(self)
        DispatchSpawn(self.lair)
        self.lair.Activate()
        
        tile.attachedlair = self.lair.GetHandle()
        
        self.lasthadlairtime = gpGlobals.curtime
        
    def Slap(self, player):
        super(UnitBaseCreature, self).Slap(player)
        
        self.happiness -= self.unitinfo.slappenalty
        
    # Sleep methods
    def NeedSleep(self):
        if self.nextrandomsleeptime < gpGlobals.curtime:
            return True
        return False
            
    def StartSleeping(self):
        if self.sleeping:
            return
        self.creaturestatus = STATUS_SLEEPING
        self.sleeping = True
        
    def Sleep(self):
        assert(self.sleeping)
        if self.health < self.maxhealth:
            self.TakeHealth(1.0, 0)
            DispatchParticleEffect("pg_heal", PATTACH_ABSORIGIN_FOLLOW, self)
        
    def EndSleeping(self):
        if not self.sleeping:
            return
        self.creaturestatus = STATUS_NONE
        self.nextrandomsleeptime = gpGlobals.curtime + random.randint(10, 30)
        self.sleeping = False
        
    def IsSleepless(self):
        return gpGlobals.curtime - self.lastsleeptime < 60.0
        
    def GetSleepPriority(self):
        if self.IsSleepless():
            return 2
        return 0
        
    # Eat methods
    def FindHatchery(self):
        hatcheries = tilespertype[self.GetOwnerNumber()]['hatchery']
        if not hatcheries:
            return
        return random.sample(hatcheries, 1)[0]
        
    def NeedEating(self):
        if self.nexteattime < gpGlobals.curtime:
            return True
        
        return False
        
    def StartEating(self):
        self.creaturestatus = STATUS_EATING
        
    def Eat(self):
        self.TakeHealth(5.0, 0)
        self.lasteattime = gpGlobals.curtime
        self.happiness += self.unitinfo.eatgain
        
    def EndEating(self):
        self.creaturestatus = STATUS_NONE
        self.nexteattime = gpGlobals.curtime + random.randint(10, 30)
        
    def GetEatPriority(self):
        if self.IsStarving():
            return 2
        return 0
        
    # Training methods
    def NeedTraining(self):
        if self.nexttraintime < gpGlobals.curtime:
            return True
        return False
        
    def ShouldContinueTraining(self):
        if self.IsStarving() or self.IsSleepless() or self.paypending:
            return False
        return random.random() > 0.05
        
    def GetTrainPriority(self):
        return 0
        
    # Creature happiness methods
    def ShouldLeave(self):
        ''' Wheter this creature should leave the dungeon.
            If we have no lair for a long time or are starving, we are moving away.
        '''
        if not self.portal:
            return False
        if not self.heart:
            return True
            
        return self.happiness < -80
        
    def OnLeaving(self):
        self.creaturestatus = STATUS_UNHAPPY
        
    def IsStarving(self):
        return gpGlobals.curtime - self.lasteattime > 240.0
        
    # Misc
    def GetWanderPriority(self):
        return 0
        
    def DoNothingPriority(self):
        return 0
        
    # Pay related methods
    def CanBePayed(self):
        return HasEnoughResources([('gold', self.unitinfo.paycost)], self.GetOwnerNumber())
    
    def OnPayDay(self):
        self.paypending = True
        self.lastpaydaytime = gpGlobals.curtime
        self.creaturestatus = STATUS_PAYDAY
        # Don't respond. Pass to the AI.
        
    def GetPay(self):
        if not self.CanBePayed():
            return False
        TakeResources(self.GetOwnerNumber(), [('gold', self.unitinfo.paycost)])
        
        self.creaturestatus = STATUS_NONE
        self.lastpaytime = gpGlobals.curtime
        self.paypending = False
        self.happiness += self.unitinfo.paygain
        self.EmitAmbientSound(-1, self.GetAbsOrigin(), 'Misc.CoinSack')
        InsertResourceIndicator(self.GetAbsOrigin(), '%s' % (str(self.unitinfo.paycost)))
        return True
        
    # Happiness
    def UpdateHappiness(self):
        info = self.unitinfo
        
        if self.ishero:
            self.happiness = 100
            self.happinessnetworked = 100
            return
        
        interval = gpGlobals.curtime - self.GetLastThink()
        
        if self.sleeping:
            self.happiness += info.sleepgain * interval
            
        if not self.enemy:
            if self.paypending and gpGlobals.curtime - self.lastpaytime < 60.0:
                self.happiness -= info.paypenalty * interval
            if self.IsStarving():
                self.happiness -= info.starvingpenalty * interval
            if not self.lair:
                self.happiness -= info.nolairpenalty * interval
            if self.IsSleepless():
                self.happiness -= info.sleeppenalty * interval
            
        self.happinessnetworked = int(self.happiness)
           
    def OnNewLevel(self):
        super(UnitBaseCreature, self).OnNewLevel()
        
        self.happiness += self.unitinfo.trainlevelgain
    
    # Handle to our lair
    lair = None
    #: Is this creature sleeping?
    sleeping = False
    #: Time at which this creature entered the dungeon.
    creatureentertime = 0.0
    #: Last time a creature had a lair
    lasthadlairtime = 0.0
    #: Last time the creature was sleeping
    lastsleeptime = 0.0
    #: Next time we want to eat.
    nexteattime = 0.0
    #: Last time we ate.
    lasteattime = 0.0
    #: Next time we want to sleep.
    nextrandomsleeptime = 0.0
    #: Next time we want to train.
    nexttraintime = 0.0
    #: Last payday time (not last time we got payed).
    lastpaydaytime = 0.0
    #: Last pay time
    lastpaytime = 0.0
    #: Portal we used to enter this dungeon
    portal = None
    #: Wheter a payment for this creature is pending.
    paypending = False
    
    #: Happiness of our creature
    _happiness = FloatField(value=0.0)
    @property
    def happiness(self):
        return self._happiness
    @happiness.setter
    def happiness(self, value):
        self._happiness = value
        self._happiness = max(min(100.0, self._happiness), -100.0)
        
    happinessnetworked = IntegerField(value=0, networked=True, propname='propint1')
    
class UnitKeeperInfo(UnitInfo):
    hangsound = ''
    dropsound = ''
    lairmodel = 'models/aliens/egg/egggib_1.mdl'
    traincost = 1 # Gold cost per hit when training
    trainperexp = 15 # Experience received per hit when doing training
    paycost = 50 # Gold required per pay
    
    # Happiness penalties
    nolairpenalty = 0.5 # per second
    sleeppenalty = 0.5 # per second
    starvingpenalty = 0.5 # per second
    paypenalty = 0.5 # per second
    slappenalty = 4
    
    # Happiness gains (possible per second)
    sleepgain = 0.5 # per second
    eatgain = 2.0 # per eat grub
    paygain = 10.0 # per pay
    trainlevelgain = 10.0 # Gain happiness for achieving a new level