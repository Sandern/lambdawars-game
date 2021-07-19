from vmath import Vector
from entities import entity, Activity, WeaponSound
from core.weapons import WarsWeaponMachineGun, VECTOR_CONE_3DEGREES
from te import CEffectData, DispatchEffect
from fields import FloatField

if isserver:
    from wars_game.ents.prop_combine_ball import CreateCombineBall

@entity('weapon_ar2', networked=True)
class WeaponAR2(WarsWeaponMachineGun):
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
        
    def SecondaryAttack(self):
        self.nextprimaryattack = self.nextsecondaryattack = gpGlobals.curtime + self.secondaryfiredelay

        self.SendWeaponAnim(Activity.ACT_VM_FIDGET)
        self.WeaponSound(WeaponSound.SPECIAL1)
        
        # Delay fire using SetThink
        self.SetThink(self.DelayedAttack, self.nextprimaryattack, "DelayedFire")
    
    def DelayedAttack(self):
        owner = self.GetOwner()

        owner.DoMuzzleFlash()
        
        self.SendWeaponAnim(Activity.ACT_VM_SECONDARYATTACK)
        
        self.WeaponSound(WeaponSound.WPN_DOUBLE)

        if isserver:
            vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
            vecVelocity = vecShootDir * 1000.0 * self.ballspeed
            
            # Fire the combine ball
            CreateCombineBall(vecShootOrigin, 
                               vecVelocity, 
                               10, 
                               150,
                               self.balllife,
                               owner)

            # View effects
            #white color32(255, 255, 255, 64)
            #UTIL_ScreenFade(owner, white, 0.1, 0, FFADE_IN )
    
        # Can shoot again immediately
        self.nextprimaryattack = gpGlobals.curtime + 0.5

        # Can blow up after a short delay (so have time to release mouse button)
        self.nextsecondaryattack = gpGlobals.curtime + 1.0

    clientclassname = 'weapon_ar2'
    muzzleoptions = 'COMBINE MUZZLE'
    secondaryfiredelay = FloatField(value=0.5)
    ballspeed = FloatField(value=1.5)
    balllife = FloatField(value=1.00)
    
    class AttackPrimary(WarsWeaponMachineGun.AttackPrimary):
        maxrange = 768.0
        attackspeed = 0.08
        usesbursts = True
        minburst = 3
        maxburst = 3
        minresttime = 0.30
        maxresttime = 0.30
        attributes = ['pulse']