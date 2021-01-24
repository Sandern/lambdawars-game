from vmath import VectorNormalize, Vector
from core.abilities import AbilityTarget, AbilityUpgrade
from core.units import CreateUnitNoSpawn, PrecacheUnit
from fields import FloatField

if isserver:
    from entities import DispatchSpawn
    from core.units import BaseBehavior

    class ActionPlaceC4Explosive(BaseBehavior.ActionAbility):
        def Update(self):
            outer = self.outer
            
            target = self.order.target if self.order.target else self.order.position
            
            # In range of target
            if not self.movedtospot:
                self.movingtospot = True
                return self.SuspendFor(self.behavior.ActionMoveTo, 'Moving to target', target) 

            #outer.DoAnimation(outer.ANIM_MELEE_ATTACK1)
            outer.EmitSound('ability_c4exposive')
            abi = self.order.ability
            trans = self.SuspendFor(self.behavior.ActionChanneling, 'Placing c4 explosive', abi.placetime)
            self.placingaction = self.nextaction
            return trans
            
        def OnEnd(self):
            super().OnEnd()
            
            if not self.placedc4explosive:
                self.order.ability.Cancel()

        def OnResume(self):
            abi = self.order.ability
            if self.movingtospot:
                self.movingtospot = False
                self.movedtospot = self.outer.navigator.path.success
            elif self.placingaction:
                if self.placingaction.channelsuccess:
                    abi.PlaceC4Explosive(self.place_position)
                    self.placedc4explosive = True
                    abi.SetRecharge(self.outer)
                    abi.Completed()
                    
                self.placingaction = None
                self.order.Remove(dispatchevent=False)
                
            return super().OnResume()

        @property
        def place_position(self):
            return self.outer.GetAbsOrigin()
            
        movingtospot = False
        movedtospot = False
        placedc4explosive = False
        placingaction = None
        facingminimum = 0.7
        
class AbilityC4Explosive(AbilityTarget):
    # Info
    name = "c4explosive"
    image_name = 'vgui/rebels/abilities/rebel_saboteur_tnt.vmt'
    rechargetime = 7
    costs = [[('scrap', 10)], [('kills', 1)]]
    displayname = "#AbilityC4Explosive_Name"
    description = "#AbilityC4Explosive_Description"
    cloakallowed = True
    techrequirements = ['c4explosive_unlock']
    
    placetime = FloatField(value=3)
    detonatetime = FloatField(value=9.0)
     
    if isserver:
        @classmethod
        def Precache(info):
            super().Precache()
            
            PrecacheUnit('c4explosive_ent')
            
        def PlaceC4Explosive(self, position):
            c4explosive = CreateUnitNoSpawn('c4explosive_ent')
            c4explosive.detonatetime = self.detonatetime
            c4explosive.SetAbsOrigin(position)
            c4explosive.SetOwnerNumber(self.ownernumber)
            DispatchSpawn(c4explosive)
            c4explosive.Activate()
    
        def DoAbility(self):
            data = self.mousedata
            
            if self.ischeat:
                self.PlaceC4Explosive(data.endpos)
                self.Completed()
                return

            pos = data.groundendpos
            target = data.ent if data.ent and not data.ent.IsWorld() else None
            
            if not self.TakeResources(refundoncancel=True):
                self.Cancel(cancelmsg='#Ability_NotEnoughResources', debugmsg='not enough resources')
                return

            self.unit.AbilityOrder(position=pos,
                        target=target,
                        ability=self)
            self.SetNotInterruptible()
            
        behaviorgeneric_action = ActionPlaceC4Explosive
        
    allowmultipleability = True

class AbilityC4ExplosiveUnlock(AbilityUpgrade):
	name = 'c4explosive_unlock'
	displayname = '#AbilityC4ExplosiveUnlock_Name'
	description = '#AbilityC4ExplosiveUnlock_Description'
	image_name = "vgui/rebels/abilities/rebel_tnt_unlock.vmt"
	#techrequirements = ['build_reb_specialops']
	buildtime = 55.0
	costs = [[('kills', 4)], [('requisition', 20), ('scrap', 40)]]

class CharC4Explosive(AbilityC4Explosive):
    name = 'c4explosive_char'
    rechargetime = 15
    costs = []
    techrequirements = []
    placetime = FloatField(value=0)
    detonatetime = FloatField(value=3.0)

