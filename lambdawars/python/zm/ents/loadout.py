from srcbase import *
from vmath import *
from zm.shared import *
from fields import IntegerField, StringField, BooleanField, input, OutputField
import random

if isserver:
    from entities import CPointEntity, entity
    from utils import UTIL_PlayerByIndex

    @entity('info_loadout')
    class ZombieMasterLoadOut(CPointEntity):
        LO_MELEE = 0
        LO_SMALL = 1
        LO_LARGE = 2
        LO_EQUIPMENT = 3
        LO_CATEGORY_COUNT = 4
        
        method = IntegerField(keyname='Method')
        
        # STODO
        '''
DEFINE_KEYFIELD(m_iWeaponCounts[LO_PISTOL], FIELD_INTEGER, "Pistols"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_SHOTGUN], FIELD_INTEGER, "Shotguns"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_RIFLE], FIELD_INTEGER, "Rifles"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_MAC10], FIELD_INTEGER, "Mac10s"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_MOLOTOV], FIELD_INTEGER, "Molotovs"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_SLEDGEHAMMER], FIELD_INTEGER, "Sledgehammers"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_IMPROVISED], FIELD_INTEGER, "Improvised"), 
DEFINE_KEYFIELD(m_iWeaponCounts[LO_REVOLVER], FIELD_INTEGER, "Revolvers"), 
        '''
        
        def __init__(self):
            super(ZombieMasterLoadOut, self).__init__()
            
            self.weaponcounts = [0]*LO_WEAPONS_TOTAL 
            self.weaponsall = [0]*LO_WEAPONS_TOTAL
            
            self.weaponscategorised = []
            for i in range(0, self.LO_CATEGORY_COUNT):
                self.weaponscategorised.append([])
            
        def Spawn(self):
            self.SetSolid(SOLID_NONE)
            self.AddEffects(EF_NODRAW)

            self.SetMoveType(MOVETYPE_NONE)

            #TGB: figure out what we have to hand out
            self.FillWeaponLists()

        #--------------------------------------------------------------
        # TGB: fill our lists with the available weapons
        #--------------------------------------------------------------
        def FillWeaponLists(self):
            '''TGB: a fundamental difference with the old method is that we shuffle our weapons list
            * instead of our player list. self means we can just randomly pick an entry from the list, hand
            * it to the player and remove it from the list. No shuffling required
            '''

            #TGB: added option to disable self entity, requested by people for RP or difficulty-pumped servers
            if zm_loadout_disable.GetInt() == 1:
                print("info_loadout entities have been disabled with zm_loadout_disable")
                return

            if self.method == 1:
                #CATEGORISED
                #ugh...

                for i in range(0, self.LO_CATEGORY_COUNT):
                    self.weaponscategorised[i] = []

                #have to resort to ugly churning

                #MELEE
                for i in range(0, LO_IMPROVISED):
                    self.weaponscategorised[self.LO_MELEE].append(LO_IMPROVISED)
                
                for i in range(0, LO_SLEDGEHAMMER):
                    self.weaponscategorised[self.LO_MELEE].append(LO_SLEDGEHAMMER)

                #SMALL
                for i in range(0, LO_PISTOL):
                    self.weaponscategorised[self.LO_SMALL].append(LO_PISTOL)

                for i in range(0, LO_REVOLVER):
                    self.weaponscategorised[self.LO_SMALL].append(LO_REVOLVER)

                #LARGE
                for i in range(0, LO_SHOTGUN):
                    self.weaponscategorised[self.LO_LARGE].append(LO_SHOTGUN)
                
                for i in range(0, LO_RIFLE):
                    self.weaponscategorised[self.LO_LARGE].append(LO_RIFLE)
                
                for i in range(0, LO_MAC10):
                    self.weaponscategorised[self.LO_LARGE].append(LO_MAC10)

                #EQUIP
                for i in range(0, LO_MOLOTOV):
                    self.weaponscategorised[self.LO_EQUIPMENT].append(LO_MOLOTOV)
            else:
                #INDISCR.
                #just dump all weapons in a big ol list

                #loop through all types
                #basically array copy in self case, we don't want to do destructive things to our defaults-array
                for i in range(0, LO_WEAPONS_TOTAL):
                    self.weaponsall[i] = self.weaponcounts[i]

        #--------------------------------------------------------------
        # TGB: hand weapon(s) to a given player
        #--------------------------------------------------------------
        def DistributeToPlayer(self, pPlayer):
            if not pPlayer or zm_loadout_disable.GetInt() == 1 or pPlayer.GetOwnerNumber() != ON_SURVIVOR:
                return

            if self.method == 1:
                #categorised

                #hand out a weapon of each type
                for i in range(0, self.LO_CATEGORY_COUNT):
                    #for each category, randomly pick a weapon from the list and give it to the player
                    if len(self.weaponscategorised[i]) > 0:
                        pick = random.randint(0, len(self.weaponscategorised[i]) - 1)
                        ZombieMasterLoadOut.CreateAndGiveWeapon(pPlayer, self.weaponscategorised[i][pick])
                        del self.weaponscategorised[i][pick]
            else:
                #indiscriminate

                #eh, build a quick vector of types we still have
                remaining = []
                for i in range(0, LO_WEAPONS_TOTAL):
                    if self.weaponsall[i] > 0:
                        remaining.append(i)

                if len(remaining) > 0:
                    #pick a random weapon type, hand it out, and remove an entry of that type from the list
                    pick = remaining[random.randint(0, len(remaining) - 1)]
                    ZombieMasterLoadOut.CreateAndGiveWeapon(pPlayer, pick)
                    self.weaponsall[pick] -= 1

        #--------------------------------------------------------------
        # TGB: distribute now simply calls DistributeToPlayer for all survivors
        #--------------------------------------------------------------
        def Distribute(self):
            #TGB: added option to disable self entity, requested by people for RP or difficulty-pumped servers
            if zm_loadout_disable.GetInt() == 1:
                print("info_loadout entities have been disabled with zm_loadout_disable")
                return

            DevMsg(1, "Loadout of type %d\n" % self.method)

            playerlist = []  #I just always purge these to be sure

            #LAWYER:  Build an array of players that we can pop things from
            for i in range(1, gpGlobals.maxClients+1):
                pPlayer = UTIL_PlayerByIndex( i )
                if pPlayer:
                    if pPlayer.GetOwnerNumber() == ON_SURVIVOR:
                        #TGB: have to do some vector hussling so that we avoid categorised handout bias
                        playerlist.append(pPlayer)

            #Fisher-Yates shuffle mm yeah, mostly ripped from wpedia
            n = len(playerlist)
            while n > 1:
                k = random.randint(0, n-1)  # 0 <= k < n.
                n -= 1
                #swappy swaps some values, we don't move actual elements (as in memory blocks)
                temp = playerlist[n]
                playerlist[n] = playerlist[k]
                playerlist[k] = temp

            for i in range(0, len(playerlist)):
                #TGB: get self man a gun, good sir
                self.DistributeToPlayer(playerlist[i])

        #TGB: quick helper
        def CreateAndGiveWeapon(self, pPlayer, weapon_type):
            if not pPlayer: return
            
            #braap
            WeaponTypeToName = [
                    "weapon_zm_improvised",
                    "weapon_zm_sledge",
                    "weapon_zm_pistol",
                    "weapon_zm_shotgun",
                    "weapon_zm_rifle",
                    "weapon_zm_mac10",
                    "weapon_zm_revolver",
                    "weapon_zm_molotov",
            ]

            #determine weapon name
            weapon_name = WeaponTypeToName[weapon_type]

            add_ammo = True
            if weapon_type in [LO_IMPROVISED, LO_SLEDGEHAMMER, LO_MOLOTOV]:
                add_ammo = False

            weapon = pPlayer.Weapon_Create(weapon_name)
            if weapon:
                #TGB: loadout was not updating weapon carrying flags properly 0000413
                #could do self in weapon_create or something, but that might affect other systems
                pPlayer.m_iWeaponFlags += weapon.GetWeaponTypeNumber()

                pPlayer.Weapon_Equip(weapon)

                if add_ammo:
                    pPlayer.GiveAmmo(weapon.GetMaxClip1(), weapon.GetPrimaryAmmoType(), True)

                DevMsg(1, "LoadOut: gave %s to %s\n" % (weapon_name, pPlayer.GetPlayerName()))
