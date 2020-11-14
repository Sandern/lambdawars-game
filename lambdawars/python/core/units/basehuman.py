from vmath import VectorNormalize, VectorAngles, QAngle, Vector
from .basecombat import UnitBaseCombat as BaseClass
from entities import Activity, networked
from unit_helper import UnitAnimConfig, LegAnimType_t
from utils import UTIL_PlayerByIndex, UTIL_PrecacheOther
from fields import BooleanField

if isserver:
    from unit_helper import UnitExpresser

@networked
class UnitBaseCombatHuman(BaseClass):
    """ Defines a human like unit.
        The main difference is that it can aim by 
        controlling the upper body pitch and yaw and
        can carry weapons. """
    if isserver:
        def OnPlayerDefeated(self):
            self.Suicide()

        def CreateComponents(self):
            super().CreateComponents()
            
            self.expresser = UnitExpresser(self)

        def DestroyComponents(self):
            if self.componentsinitalized:
                del self.expresser
            super().DestroyComponents()

        def Precache(self):
            super().Precache()
            
            for weapon in self.unitinfo.weapons:
                UTIL_PrecacheOther(weapon)

            # since combine are directly exported, we should precache it beforehand...
            self.PrecacheScriptSound("unit_combine_hurt")

    def Spawn(self):
        """ On Spawn, adds weapons to the unit using the info class. """
        super().Spawn()
        
        self.hackedgunpos = Vector(0, 0, 55)
        self.animstate.combatstateifenemy = True

        self.EquipWeapons()

    def EquipWeapons(self):
        """ Create weapons and equip """
        if not isserver or not self.unitinfo.weapons:
            return
        for weapon in self.unitinfo.weapons:
            w = self.Weapon_Create(weapon)
            if not w:
                continue
            w.MakeWeaponNameFromEntity(self)
            self.Weapon_Equip(w)

    def UnitThink(self):
        super().UnitThink()
        self.Weapon_FrameUpdate()
    
    def UserCmd(self, cmd):
        super().UserCmd(cmd)
        
        if isclient:
            self.Weapon_FrameUpdate()
        
        if self.controlledbyplayer:
            player = UTIL_PlayerByIndex(self.controlledbyplayer)
            
            end = player.GetMouseData().endpos
            dir = end - self.Weapon_ShootPosition() 
            dist = VectorNormalize(dir)

            angle = QAngle()
            VectorAngles(dir, angle)
            self.eyeyaw = self.EyeAngles().y
            self.eyepitch = angle.x
            
    def Mount(self):
        if self.mounted:
            return
        self.mounted = True
        if self.activeweapon:
            self.activeweapon.Holster()
        self.UpdateTranslateActivityMap()
        
    def Dismount(self):
        if not self.mounted:
            return
        self.mounted = False
        if self.activeweapon:
            self.activeweapon.Deploy()
        self.UpdateTranslateActivityMap()
        
    def Order(self, player):
        if self.garrisoned:
            return
        return super().Order(player)
        
    def IsSelectableByPlayer(self, player, target_selection):
        if self.garrisoned:
            return False
        if len(target_selection) > 1 and self.mounted:
            return False
        return super().IsSelectableByPlayer(player, target_selection)
        
    def UpdateTranslateActivityMap(self):
        if self.mounted:
            table = self.acttransmaps['mounted']
            self.animstate.SetActivityMap(table)
            return
        super().UpdateTranslateActivityMap()
            
    if isclient:
        def OnDataChanged(self, type):
            super().OnDataChanged(type)
            
            if self.oldmounted != self.mounted:
                self.UpdateTranslateActivityMap()
                self.oldmounted = self.mounted
            
    if isserver:
        def OnChangeOwnerNumber(self, oldownernumber):
            super().OnChangeOwnerNumber(oldownernumber)
            if self.activeweapon:
                self.activeweapon.SetOwnerNumber(self.GetOwnerNumber())
                
    def EventHandlerPrimaryAttack(self, data=0):
        self.lasttakedamageperowner[self.GetOwnerNumber()] = gpGlobals.curtime
    
        # Play range attack animation (use fire layer?)
        #self.specificmainactivity = self.outer.attackrange1act
        #self.RestartMainSequence()
        
        # Just dispatch the muzzle flash effect manually here
        # The weapon animation is not really important, it only dispatched an animation
        # event for this.
        self.animstate.combatstatetime = gpGlobals.curtime + 2.0
        activeweapon = self.activeweapon
        if isclient and activeweapon:
            if activeweapon.muzzleoptions and not self.controlledbyplayer or activeweapon.GetMuzzleAttachEntity() == activeweapon:
                activeweapon.DispatchMuzzleEffect(activeweapon.muzzleoptions, False)
            activeweapon.PrimaryAttack()

    def EventHandlerSecondaryAttack(self, data=0):
        self.lasttakedamageperowner[self.GetOwnerNumber()] = gpGlobals.curtime
        
        # Just dispatch the muzzle flash effect manually here
        # The weapon animation is not really important, it only dispatched an animation
        # event for this.
        self.animstate.combatstatetime = gpGlobals.curtime + 2.0
        activeweapon = self.activeweapon
        if isclient and activeweapon and activeweapon.muzzleoptions:
            if not self.controlledbyplayer or activeweapon.GetMuzzleAttachEntity() == activeweapon:
                activeweapon.DispatchMuzzleEffect(activeweapon.muzzleoptions, False)
            activeweapon.SecondaryAttack()
            
    def EventHandlerMeleeAttack1(self, data=0):
        self.lasttakedamageperowner[self.GetOwnerNumber()] = gpGlobals.curtime
        
        animstate = self.animstate
        animstate.miscsequence = animstate.SelectWeightedSequence(animstate.TranslateActivity(self.attackmelee1act))
        animstate.playermisc = True
        animstate.misccycle = 0
        animstate.misconlywhenstill = False
        animstate.miscnooverride = True
        animstate.miscplaybackrate = 1.0
        
    def EventHandlerMeleeAttack2(self, data=0):
        self.lasttakedamageperowner[self.GetOwnerNumber()] = gpGlobals.curtime
        
        animstate = self.animstate
        animstate.miscsequence = animstate.SelectWeightedSequence(animstate.TranslateActivity(self.attackmelee2act))
        animstate.playermisc = True
        animstate.misccycle = 0
        animstate.misconlywhenstill = False
        animstate.miscnooverride = True
        animstate.miscplaybackrate = 1.0
    
    oldmounted = False
    
    #: Indicates if this unit is mounting a turret (networked bool).
    mounted = BooleanField(value=False, networked=True)
    #: Indicates if this unit is garrisoned inside a building (networked bool).
    garrisoned = BooleanField(value=False, networked=True)

    # Anims Events
    events = dict(BaseClass.events)
    events.update( {
        'ANIM_ATTACK_PRIMARY' : EventHandlerPrimaryAttack,
        'ANIM_ATTACK_SECONDARY' : EventHandlerSecondaryAttack,
        'ANIM_MELEE_ATTACK1' : EventHandlerMeleeAttack1,
        'ANIM_MELEE_ATTACK2' : EventHandlerMeleeAttack2,
    } )
    
    acttables = dict(BaseClass.acttables)
    acttables.update( { 
        # Default entry for mounting turrets
        'mounted': {
            Activity.ACT_IDLE : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_WALK : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_RUN : Activity.ACT_IDLE_MANNEDGUN,
            
            Activity.ACT_IDLE_AIM_AGITATED : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_WALK_AIM : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_RUN_AIM : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_CROUCH : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_RUN_CROUCH : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_WALK_CROUCH_AIM : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_RUN_CROUCH_AIM : Activity.ACT_IDLE_MANNEDGUN,
            Activity.ACT_CROUCHIDLE_AIM_STIMULATED : Activity.ACT_IDLE_MANNEDGUN, 
        }
    } )
    
    # Anims
    animconfig = UnitAnimConfig(
        maxbodyyawdegrees=60.0,
        leganimtype=LegAnimType_t.LEGANIM_8WAY,
        useaimsequences=False,
    )

    class AnimStateClass(BaseClass.AnimStateClass):
        def OnNewModel(self):
            super().OnNewModel()
            
            self.bodyyaw = self.outer.LookupPoseParameter("aim_yaw")
            self.bodypitch = self.outer.LookupPoseParameter("aim_pitch")
