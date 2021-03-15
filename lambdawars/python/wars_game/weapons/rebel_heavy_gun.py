from vmath import Vector
from entities import entity 
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_3DEGREES
from te import CEffectData, DispatchEffect


@entity('weapon_rebel_heavy_gun', networked=True)
class WeaponRebelHeavyGun(WarsWeaponMachineGun):
    def __init__(self):
        super().__init__()

        self.bulletspread = VECTOR_CONE_3DEGREES
        self.tracercolor = Vector(0.1882, 0.502, 0.596)
        
    def GetTracerType(self): return "AR2Tracer"
    
    def DoImpactEffect(self, tr, damagetype):
        data = CEffectData()

        data.origin = tr.endpos + (tr.plane.normal * 1.0)
        data.normal = tr.plane.normal

        DispatchEffect("AR2Impact", data)

        super().DoImpactEffect(tr, damagetype)
        
    clientclassname = 'weapon_rebel_heavy_gun'
    muzzleoptions = 'COMBINE MUZZLE'
    
    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        maxrange = 768.0
        attackspeed = 0.075
        attributes = ['ar1']