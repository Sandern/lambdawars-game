from core.abilities import AbilityInstant

if isserver:
    from srcbase import DMG_BLAST, DMG_ALWAYSGIB, DMG_PREVENT_PHYSICS_FORCE
    from utils import UTIL_PlayerByIndex
    from gameinterface import engine
    from entities import CTakeDamageInfo

class AbilityInstantSlayDiscrate(AbilityInstant):
    name = "instantslaydiscrate"

    def DoAbility(self):
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if not player:
                continue
            steamIDForPlayer = engine.GetClientSteamID(player)
            #print '%d == %d (%s)' % (steamIDForPlayer.GetAccountID(), self.iddiscrate, steamIDForPlayer.GetAccountID() == self.iddiscrate)
            if steamIDForPlayer and steamIDForPlayer.GetAccountID() == self.iddiscrate:
                unit = player.GetControlledUnit()
                if unit:
                    damage = DMG_BLAST|DMG_ALWAYSGIB|DMG_PREVENT_PHYSICS_FORCE
                    unit.health = 0
                    unit.Event_Killed( CTakeDamageInfo( player, player, 0, damage, 0 ) )
                damage = DMG_BLAST|DMG_ALWAYSGIB|DMG_PREVENT_PHYSICS_FORCE
                player.Event_Killed( CTakeDamageInfo( player, player, 0, damage, 0 ) )
                player.Event_Dying()
                return
        PrintWarning("InstantSlayDiscrate: No discrate's found :(\n")
    iddiscrate = 14684921*2 # STEAM_0:1:14684921
    serveronly=True
            