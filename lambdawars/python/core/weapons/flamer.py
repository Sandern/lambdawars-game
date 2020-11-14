from srcbase import *
from vmath import *
from entities import CShotManipulator
from .base import WarsWeaponBase as BaseClass
from .flamer_projectile import FlamerProjectile
from particles import PATTACH_POINT_FOLLOW
import random
from gameinterface import CPASAttenuationFilter

if isserver:
    from particles import PrecacheParticleSystem
    from te import CEffectData, DispatchEffect
    from gameinterface import CPASFilter
else:
    from entities import DATA_UPDATE_CREATED, CLIENT_THINK_ALWAYS
    from sound import CSoundEnvelopeController

class WeaponFlamer(BaseClass):
    if isserver:
        def Precache(self):
            self.PrecacheModel( "swarm/sprites/whiteglow1.vmt" )
            self.PrecacheModel( "swarm/sprites/greylaser1.vmt" )
            self.PrecacheScriptSound("ASW_Flamer.ReloadA")
            self.PrecacheScriptSound("ASW_Flamer.ReloadB")
            self.PrecacheScriptSound("ASW_Flamer.ReloadC")
            PrecacheParticleSystem( "wars_flamethrower" )
            PrecacheParticleSystem( "asw_fireextinguisher" )

            super().Precache()

    def OnDataChanged(self, updateType):
        super().OnDataChanged( updateType )

        if updateType == DATA_UPDATE_CREATED:
            self.SetNextClientThink(CLIENT_THINK_ALWAYS)

            if not self.pilotlight:
                self.pilotlight = self.ParticleProp().Create("asw_flamethrower_pilot_sml", PATTACH_POINT_FOLLOW, "fire")

                if self.pilotlight:
                    self.pilotlight.SetControlPoint(1, Vector( 1, 0, 0 ))
                    
        if self.pilotlight:
            iPilot = 0 if (self.switchingweapons or not self.IsVisible() or not self.GetOwner() or self.isfiring or self.issecondaryfiring) else 1 #or self.IsReloading() or (Clip1() <= 0)) ? 0 : 1

            self.pilotlight.SetControlPoint(1, Vector(iPilot, 0, 0))

    def UpdateOnRemove(self):
        super().UpdateOnRemove()

        if self.pilotlight:
            self.ParticleProp().StopEmissionAndDestroyImmediately(self.pilotlight)
            self.pilotlight = None
            
        if isclient:
            self.StopFlamerLoop()

    def ClientThink(self):
        super().ClientThink()

        if self.isfiring:
            if not self.effect:
                self.effect = self.ParticleProp().Create( "wars_flamethrower", PATTACH_POINT_FOLLOW, "fire" )
            self.StartFlamerLoop()
        else:
            if self.effect:
                self.effect.StopEmission()
                self.effect = None
            self.StopFlamerLoop()

        if self.issecondaryfiring:
            if not self.extinguisheffect:
                self.extinguisheffect = self.ParticleProp().Create( "asw_fireextinguisher", PATTACH_POINT_FOLLOW, "fire" )
        else:
            if self.extinguisheffect:
                self.extinguisheffect.StopEmission()
                self.extinguisheffect = None

    def ClearIsFiring(self):
        super().ClearIsFiring()

        self.issecondaryfiring = False

    def ItemPostFrame(self):
        super().ItemPostFrame()

        pOwner = self.GetOwner()

        if not pOwner:
            return

        #bool bAttack1, bAttack2, bReload, bOldReload, bOldAttack1
        #GetButtons(bAttack1, bAttack2, bReload, bOldReload, bOldAttack1 )

        #if ( !bAttack2 )
            #self.issecondaryfiring = False
            
    def GetWeaponDamage(self):
        #float flDamage = 35.0
        flDamage = self.AttackPrimary.damage
        
        #CALL_ATTRIB_HOOK_FLOAT( flDamage, mod_damage_done )

        return flDamage

    def PrimaryAttack(self):
        '''
        # If my clip is empty (and I use clips) start reload
        if self.UsesClipsForAmmo1() and !m_iClip1:
            Reload()
            return'''

        if self.issecondaryfiring:
            self.isfiring = False
            return

        pMarine = self.GetOwner()

        if pMarine: # firing from a marine
            # MUST call sound before removing a round from the clip of a CMachineGun
            #WeaponSound(SINGLE)

            self.isfiring = True

            # tell the marine to tell its weapon to draw the muzzle flash
            pMarine.DoMuzzleFlash()

            # sets the animation on the weapon model iteself
            self.SendWeaponAnim( self.GetPrimaryAttackActivity() )

            if isserver:
                # sets the animation on the marine holding self weapon
                #vecSrc = pMarine.Weapon_ShootPosition( )
                #vecAiming = vec3_origin
                #if pPlayer and pMarine.IsInhabited():
                #    vecAiming = pPlayer.GetAutoaimVectorForMarine(pMarine, GetAutoAimAmount(), GetVerticalAdjustOnlyAutoAimAmount())	# 45 degrees = 0.707106781187
                #else
                #   vecAiming = pMarine.GetActualShootTrajectory(vecSrc)
                vecSrc, vecAiming = self.GetShootOriginAndDirection()

                # Fire the bullets, and force the first shot to be perfectly accuracy
                Manipulator = CShotManipulator( vecAiming )
                rotSpeed = AngularImpulse(0,0,720)
                
                # create a pellet at some random spread direction		
                newVel = Manipulator.ApplySpread(self.GetBulletSpread())
                if pMarine.GetWaterLevel() != 3:
                    newVel *= self.FLAMER_PROJECTILE_AIR_VELOCITY
                    newVel *= (1.0 + (0.1 * random.uniform(-1,1)))
                    pellet = FlamerProjectile.Flamer_Projectile_Create(self.GetWeaponDamage(), vecSrc, QAngle(0,0,0),
                            newVel, rotSpeed, pMarine, pMarine, self)
                    if pellet:
                        pellet.dietime = gpGlobals.curtime + (self.maxbulletrange / newVel.Length()) + 0.185

                    #if (ASWGameRules())
                    #    ASWGameRules().m_fLastFireTime = gpGlobals.curtime

                    #pMarine.OnWeaponFired(self, 1)

            '''
            if (!m_bBulletMod)
            
                # decrement ammo
                m_iClip1 -= 1
                if isserver:
                    CASW_Marine *pMarine = GetMarine()
                    if (pMarine and m_iClip1 <= 0 and pMarine.GetAmmoCount(m_iPrimaryAmmoType) <= 0 )
                    
                        # check he doesn't have ammo in an ammo bay
                        CASW_Weapon_Ammo_Bag* pAmmoBag = dynamic_cast<CASW_Weapon_Ammo_Bag*>(pMarine.GetASWWeapon(0))
                        if (!pAmmoBag)
                            pAmmoBag = dynamic_cast<CASW_Weapon_Ammo_Bag*>(pMarine.GetASWWeapon(1))
                        if (!pAmmoBag or !pAmmoBag.CanGiveAmmoToWeapon(self))
                            pMarine.OnWeaponOutOfAmmo(True)
            
            m_bBulletMod = !m_bBulletMod

            if (!m_iClip1 and pMarine.GetAmmoCount(m_iPrimaryAmmoType) <= 0)
            
                # HEV suit - indicate out of ammo condition
                if (pPlayer)
                    pPlayer.SetSuitUpdate("!HEV_AMO0", False, 0) '''
        '''
        if m_iClip1 > 0: # only force the fire wait time if we have ammo for another shot
            self.nextprimaryattack = gpGlobals.curtime + GetFireRate()
            self.nextsecondaryattack = gpGlobals.curtime + GetFireRate()
        else:
            self.nextprimaryattack = gpGlobals.curtime'''
        
        self.lastfiretime = gpGlobals.curtime

    def SecondaryAttack(self):
        # If my clip is empty (and I use clips) start reload
        '''if self.UsesClipsForAmmo1() and !m_iClip1:
            Reload()
            return'''
        
        pMarine = self.GetOwner()

        # clear primary fire if we're secondary firing
        if self.isfiring:
            self.isfiring = False
            return
        if pMarine:# firing from a marine
        
            # MUST call sound before removing a round from the clip of a CMachineGun
            #WeaponSound(SINGLE)

            self.issecondaryfiring = True

            # tell the marine to tell its weapon to draw the muzzle flash
            pMarine.DoMuzzleFlash()

            # sets the animation on the weapon model iteself
            self.SendWeaponAnim(self.GetPrimaryAttackActivity())

            # sets the animation on the marine holding self weapon
            if isserver:
                #vecSrc = pMarine.Weapon_ShootPosition( )
                #vecAiming = vec3_origin
                #if pPlayer and pMarine.IsInhabited():
                #    vecAiming = pPlayer.GetAutoaimVectorForMarine(pMarine, GetAutoAimAmount(), GetVerticalAdjustOnlyAutoAimAmount())	# 45 degrees = 0.707106781187
                #else:
                #   vecAiming = pMarine.GetActualShootTrajectory(vecSrc)
                vecSrc, vecAiming = self.GetShootOriginAndDirection()

                Manipulator = CShotManipulator( vecAiming )
                rotSpeed = AngularImpulse(0,0,720)

                # create a pellet at some random spread direction			
                newVel = Manipulator.ApplySpread(self.GetBulletSpread())
                if pMarine.GetWaterLevel() != 3:
                    newVel *= self.EXTINGUISHER_PROJECTILE_AIR_VELOCITY
                    newVel *= (1.0 + (0.1 * random.uniform(-1,1)))
                    # aim it downwards a bit
                    newVel.z -= 40.0
                    CASW_Extinguisher_Projectile.Extinguisher_Projectile_Create( vecSrc, QAngle(0,0,0),
                        newVel, rotSpeed, pMarine )

                    # check for putting outselves out
                    if pMarine.IsOnFire():
                    
                        pFireChild = None#dynamic_cast<CEntityFlame *>( pMarine.GetEffectEntity() )
                        if pFireChild:
                            pMarine.SetEffectEntity(None)
                            UTIL_Remove(pFireChild)
                        
                        pMarine.Extinguish()
                        # spawn a cloud effect on self marine
                        data = CEffectData()
                        data.origin = pMarine.GetAbsOrigin()
                        #data.m_nEntIndex = pMarine.entindex()
                        filter = CPASFilter( data.origin )
                        filter.SetIgnorePredictionCull(True)
                        DispatchEffect(filter, 0.0, "ExtinguisherCloud", data)

                    pMarine.OnWeaponFired(self, 1, True)
            
            '''
            # decrement ammo
            m_iClip1 -= 1

            if (!m_iClip1 and pMarine.GetAmmoCount(m_iPrimaryAmmoType) <= 0)
            
                # HEV suit - indicate out of ammo condition
                if (pPlayer)
                    pPlayer.SetSuitUpdate("!HEV_AMO0", False, 0) 
            '''
        '''
        if (m_iClip1 > 0)		# only force the fire wait time if we have ammo for another shot
        
            self.nextsecondaryattack = gpGlobals.curtime + GetFireRate()
            self.nextprimaryattack = gpGlobals.curtime + GetFireRate()
        else:
            self.nextsecondaryattack = gpGlobals.curtime
        '''
        
        self.lastfiretime = gpGlobals.curtime
    

    def Simulate(self):
        super().Simulate()

        # hide our blue flame tip when appropriate
        self.skin = 0 if (self.isfiring or self.issecondaryfiring) else 1 #or self.IsReloading() or (Clip1() <= 0)) ? 0 : 1

        return True
        
    def StartFlamerLoop(self):
        if self.flamerloopsound:
            return

        filter = CPASAttenuationFilter(self)
        controller = CSoundEnvelopeController.GetController()
        self.flamerloopsound = controller.SoundCreate(filter, self.entindex(), self.flamerloopsoundscript)
        CSoundEnvelopeController.GetController().Play(self.flamerloopsound, 1.0, 100)

    def StopFlamerLoop(self):
        if self.flamerloopsound:
            #Msg("Ending flamer loop!\n");
            controller = CSoundEnvelopeController.GetController()
            controller.SoundDestroy(self.flamerloopsound)
            self.flamerloopsound = None
            self.EmitSound(self.flamerstopsoundscript)
        
    __firingtimeout = 0.0
    @property
    def isfiring(self):
        return self.__firingtimeout > gpGlobals.curtime
    @isfiring.setter
    def isfiring(self, isfiring):
        if isfiring:
            self.__firingtimeout = gpGlobals.curtime + 0.25
        else:
            self.__firingtimeout = 0.0
        
    pilotlight = None
    effect = None
    extinguisheffect = None
    issecondaryfiring = False
    lastfiretime = 0.0
    switchingweapons = False
    flamerloopsound = None
    flamerloopsoundscript = 'ASW_Weapon_Flamer.FlameLoop'
    flamerstopsoundscript = 'ASW_Weapon_Flamer.FlameStop'
    
    FLAMER_PROJECTILE_AIR_VELOCITY = 600
    EXTINGUISHER_PROJECTILE_AIR_VELOCITY = 400

    clientclassname = 'asw_weapon_flamer'
    
    class AttackPrimary(BaseClass.AttackRange):
        minrange = 0.0
        maxrange = 350.0
        attackspeed = 0.075 # Fire rate
        usesbursts = True
        minburst = 3
        maxburst = 5
        minresttime = 0.4
        maxresttime = 0.6