from vmath import Vector, DotProduct, AngleVectors
from entities import entity, networked
from core.units import UnitInfo, UnitBaseCombat as BaseClass
from sound import CSoundEnvelopeController, CHAN_STATIC, ATTN_NORM
from gameinterface import CPASAttenuationFilter

from unit_helper import UnitVehicleAnimState
if isserver:
    from unit_helper import UnitVehicleNavigator
    
@networked
class UnitBaseVehicle(BaseClass):
    #: Animation State class component
    AnimStateClass = UnitVehicleAnimState
    if isserver:
        #: Navigator class component
        NavigatorClass = UnitVehicleNavigator
        
    if isclient:
        def OnDataUpdateCreated(self):
            super().OnDataUpdateCreated()
            
            self.StartEngine()
            
    def UpdateOnRemove(self):
        super().UpdateOnRemove()
        
        self.StopEngine()
            
    def PostOnNewModel(self):
        super().PostOnNewModel()
        
        self.animstate.CalcWheelData()
        
    def GetDriver(self):
        return None # TODO?
        
    def VehicleAngleVectors(self, angles, forward, right, up):
        ''' AngleVectors equivalent that accounts for the hacked 90 degree rotation of vehicles. 
            BUGBUG: VPhysics is hardcoded so that vehicles must face down Y instead of X like everything else.'''
        AngleVectors(angles, right, forward, up)
        if forward:
            forward *= -1
        
    def IsOverturned(self):
        ''' Tells whether or not the car has been overturned.
            Returns true on success, false on failure. '''
        up = Vector()
        self.VehicleAngleVectors(self.GetAbsAngles(), None, None, up)

        upDot = DotProduct(Vector(0,0,1), up)

        # Tweak this number to adjust what's considered "overturned"
        if upDot < 0.0:
            return True

        return False;
            
    def StartEngine(self):
        self.PlayLoopingSound('ATV_engine_idle')
        
    def StopEngine(self):
        self.StopLoopingSound()
        
    def StopLoopingSound(self, fadetime=0.0):
        controller = CSoundEnvelopeController.GetController()
        if self.statesoundfade:
            controller.SoundDestroy(self.statesoundfade)
            self.statesoundfade = None
            
        if self.statesound:
            self.statesoundfade = self.statesound
            self.statesound = None
            controller.SoundFadeOut(self.statesoundfade, fadetime, False)
        
    def PlayLoopingSound(self, soundname):
        controller = CSoundEnvelopeController.GetController()
        
        filter = CPASAttenuationFilter(self)
        newsound = None
        if soundname:
            newsound = controller.SoundCreate(filter, self.entindex(), CHAN_STATIC, soundname, ATTN_NORM)

        if self.statesound and newsound and controller.SoundGetName(newsound) == controller.SoundGetName(self.statesound):
            # if the sound is the same, don't play this, just re-use the old one
            controller.SoundDestroy(newsound)
            newsound = self.statesound
            controller.SoundChangeVolume(newsound, 1.0, 0.0)
            self.statesound = None

        self.StopLoopingSound()
        self.statesound = newsound
        if self.statesound:
            controller.Play(self.statesound, 1.0, 100)
        
    def CreateComponents(self):
        self.locomotion = self.LocomotionClass(self)
        self.animstate = self.AnimStateClass(self)

        # Server only
        if isserver:
            self.navigator = self.NavigatorClass(self)
            self.senses = self.SensesClass(self)
            self.CreateBehaviors()
            
        # Components that receive events
        if isserver:
            self.eventcomponents = [self.locomotion, self.navigator, self.animstate]
        else:
            self.eventcomponents = [self.locomotion, self.animstate]
            
        self.componentsinitalized = True
        
    def UpdateTranslateActivityMap(self):
        pass
        
    statesound = None
    statesoundfade = None
    
class BaseVehicleInfo(UnitInfo):
    pass
    