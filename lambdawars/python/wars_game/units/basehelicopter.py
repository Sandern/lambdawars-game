from srcbase import *
from vmath import *
from core.units import UnitInfo, UnitBaseCombat as BaseClass
from sound import CSoundEnvelopeController
from core.units import UnitBaseAnimState, UnitBaseAirLocomotion
from entities import networked
from fields import input
if isserver:
    from core.units import UnitCombatAirNavigator
    from core.units.intention import BaseAction
    
class UnitBaseHelicopterAnimState(UnitBaseAnimState):
    def SetActivityMap(self, *args, **kwargs): 
        pass
    
    if isclient:
        def Update(self, eyeyaw, eyepitch):
            outer = self.outer
            enemy = outer.enemy
            
            # GetAnimTimeInterval returns gpGlobals.frametime on client, and interval between main think (non context) on server
            interval = self.GetAnimTimeInterval()
            
            iPitch = 50
            outer.UpdateRotorSoundPitch(iPitch)

@networked
class BaseHelicopter(BaseClass):
    AnimStateClass = UnitBaseHelicopterAnimState

    def __init__(self):
        super().__init__()
    
        if isserver:
            self.SetShadowCastDistance(2048.0) # Use a much higher shadow cast distance
            
    def Spawn(self):
        super().Spawn()
        
        self.SetBloodColor(DONT_BLEED)
        
        self.locomotion.desiredheight = self.flyheight
        self.locomotion.flynoiserate = self.flynoiserate
        self.locomotion.flynoisez = self.flynoisez
        
    def UpdateOnRemove(self):
        super().UpdateOnRemove()
        
        self.StopLoopingSounds()

    def Event_Killed(self, info):
        super().Event_Killed(info)
        
        self.StopLoopingSounds()
        
    #def UnitThink(self):
    #    super().UnitThink()
        
        #iPitch = 50
        #self.UpdateRotorSoundPitch(iPitch)

    def InitializeRotorSound(self):
        controller = CSoundEnvelopeController.GetController()

        if self.rotorsound:
            # Get the rotor sound started up.
            controller.Play( self.rotorsound, 0.0, 100 )
            self.UpdateRotorWashVolume()

        if self.rotorblast:
            # Start the blast sound and then immediately drop it to 0 (starting it at 0 wouldn't start it)
            controller.Play( self.rotorblast, 1.0, 100 )
            controller.SoundChangeVolume(self.rotorblast, 0, 0.0)

        #self.soundstate = SND_CHANGE_PITCH # hack for going through level transitions
 
    def UpdateRotorSoundPitch(self, iPitch):
        if self.rotorsound:
            controller = CSoundEnvelopeController.GetController()
            controller.SoundChangePitch( self.rotorsound, iPitch, 0.1 )
            self.UpdateRotorWashVolume()

    def UpdateRotorWashVolume(self):
        ''' Updates the rotor wash volume '''
        if not self.rotorsound:
            return

        controller = CSoundEnvelopeController.GetController()
        flVolDelta = self.GetRotorVolume() - controller.SoundGetVolume( self.rotorsound )
        if flVolDelta:
            # We can change from 0 to 1 in 3 seconds. 
            # Figure out how many seconds flVolDelta will take.
            flRampTime = abs( flVolDelta ) * 3.0
            controller.SoundChangeVolume( self.rotorsound, self.GetRotorVolume(), flRampTime )

    def GetRotorVolume(self):
        ''' For scripted times where it *has* to shoot '''
        return 0.0 if self.supresssound or self.IsInFOW() else 1.0

    def StopRotorWash(self):
        if self.rotorwash:
            UTIL_Remove( self.rotorwash )
            self.rotorwash = None

    def StopLoopingSounds(self):
        # Kill the rotor sounds
        controller = CSoundEnvelopeController.GetController()
        if self.rotorsound:
            controller.SoundDestroy(self.rotorsound)
            self.rotorsound = None
        if self.rotorblast:
            controller.SoundDestroy(self.rotorblast)
            self.rotorblast = None

        super().StopLoopingSounds()
        
    def Land(self):
        self.locomotion.desiredheight = 0.0
        self.locomotion.flynoiserate = 0.0
        self.locomotion.flynoisez = 0.0
        
    def Ascend(self):
        self.locomotion.desiredheight = self.flyheight
        self.locomotion.flynoiserate = self.flynoiserate
        self.locomotion.flynoisez = self.flynoisez
        
    @input(inputname='Land')
    def InputLand(self, inputdata):
        self.Land()
    @input(inputname='Ascend')
    def InputAscend(self, inputdata):
        self.Ascend()
        
    # Helicopter AI actions
    if isserver:
        class BehaviorGenericClass(BaseClass.BehaviorGenericClass):
            class ActionIdle(BaseClass.BehaviorGenericClass.ActionIdle):
                pass
                
            class ActionAscend(BaseAction):
                pass
        
    rotorsound = None
    rotorblast = None
    rotorwash = None
    supresssound = False
    
    scaleprojectedtexture = 3.5
    selectionparticlename = 'unit_circle_ground'
    jumpheight = 0.0
    canshootmove = True
    
    flyheight = 350.0
    flynoiserate = 48.0
    flynoisez = 24.0
    
    aiclimb = False
    LocomotionClass = UnitBaseAirLocomotion
    if isserver:
        NavigatorClass = UnitCombatAirNavigator
    