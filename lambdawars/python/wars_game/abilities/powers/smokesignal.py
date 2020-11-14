from vmath import QAngle
if isserver:
    from particles import PrecacheParticleSystem, DispatchParticleEffect
from core.abilities import AbilityBase

# Dispatches a smoke particle.
class AbilitySmokeSignal(AbilityBase):
    name = "smokesignal"
    rechargetime = 0
    description = "Smoke Signal :)"
        
    @classmethod
    def Precache(info):
        PrecacheParticleSystem("steampuff")
        
    def Init(self):
        super().Init()
        data = self.player.GetMouseData()
        DispatchParticleEffect("steampuff", data.groundendpos, QAngle() )
        self.Completed()
        
    serveronly = True # Do not instantiate on the client