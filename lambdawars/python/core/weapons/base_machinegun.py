from srcbase import MAX_TRACE_LENGTH
from .base import WarsWeaponBase as BaseClass
from entities import WeaponSound, FireBulletsInfo_t, Activity

class WarsWeaponMachineGun(BaseClass):
    """ Weapon base for machine gun like weapons. """
    class AttackPrimary(BaseClass.AttackRange):
        # Most machines guns have some spread, so we can start shooting earlier
        cone = BaseClass.AttackRange.DOT_6DEGREE

    '''def PostConstructor(self, clsname):
        super().PostConstructor(clsname)
        
        from gameinterface import engine
        engine.ServerCommand('dtwatchent %d\n' % (self.entindex()))
        #engine.ServerCommand('dtwatchvar m_vecOrigin\n')
        #engine.ServerCommand('dtwatchvar m_angRotation\n')
        #engine.ServerCommand('dtwatchvar m_fViewDistance\n')
        
        engine.ServerExecute()'''
    
    # def PrimaryAttack(self):
        # owner = self.GetOwner()
        # owner.DoMuzzleFlash()
        
        # #self.SendWeaponAnim( self.GetPrimaryAttackActivity() )
        # #self.SetActivity( Activity.ACT_RANGE_ATTACK_SMG1 )

        # vecShootOrigin, vecShootDir = self.GetShootOriginAndDirection()
        
        # shots = 0
        # firerate = self.firerate
        
        # # Assume still firing if gpGlobals.curtime-nextprimaryattack falss within this range
        # # In the other case reset nextprimaryattack, so we only fire one shot
        # if (gpGlobals.curtime-self.nextprimaryattack) > self.firetimeout:
            # self.nextprimaryattack = gpGlobals.curtime

        # self.WeaponSound(WeaponSound.SINGLE, self.nextprimaryattack)
        # while self.nextprimaryattack <= gpGlobals.curtime:
            # # MUST call sound before removing a round from the clip of a CMachineGun
            # #self.WeaponSound(WeaponSound.SINGLE, self.nextprimaryattack)
            # self.nextprimaryattack = self.nextprimaryattack + firerate
            # shots += 1
            # if not firerate:
                # break
    
        # # Fill in bullets info
        # info = FireBulletsInfo_t()
        # info.vecsrc = vecShootOrigin
        # info.vecdirshooting = vecShootDir
        # info.shots = shots
        # info.distance = MAX_TRACE_LENGTH
        # info.ammotype = self.primaryammotype
        # info.tracerfreq = 2
        # info.vecspread = self.bulletspread

        # #import ndebugoverlay
        # #ndebugoverlay.Line( vecShootOrigin, vecShootOrigin+info.vecdirshooting*8000, 255, 0, 0, True, 5.0 )
        
        # owner.FireBullets( info )

        # # Add our view kick in
        # #self.AddViewKick()
        
    #firetimeout = 0.25 # Unit think is 0.2, so this falls within two intervals
    