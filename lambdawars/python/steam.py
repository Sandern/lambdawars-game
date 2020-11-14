from _steam import *

# Add a __hash__ and __str__ implementation to CSteamID class
CSteamID.__hash__ = lambda self: self.GetAccountID()
CSteamID.__str__ = lambda self: str(self.ConvertToUint64())

# Add wrappers for a few Matchmaking functions
__fnSteamMatchmaking = steamapicontext.SteamMatchmaking
def __SteamMatchmakingModifier():
    # Add wrappers
    matchmaking = __fnSteamMatchmaking()
    if matchmaking:
        matchmaking.GetLobbyDataByIndex = PyGetLobbyDataByIndex
        matchmaking.SendLobbyChatMsg = PySendLobbyChatMsg
        matchmaking.GetLobbyChatEntry = PyGetLobbyChatEntry
    return matchmaking
steamapicontext.SteamMatchmaking = __SteamMatchmakingModifier

# Add wrappers for a few UserStats functions
__fnSteamUserStats = steamapicontext.SteamUserStats
def __SteamUserStatsModifier():
    # Add wrappers
    userstats = __fnSteamUserStats()
    if userstats:
        userstats.GetStatFloat = PyGetStatFloat
        userstats.GetStatInt = PyGetStatInt
    return userstats
steamapicontext.SteamUserStats = __SteamUserStatsModifier


steamapicontext.SteamMatchmakingServers = SteamMatchmakingServers

# Add wrappers for a few SteamUGC functions
if hasattr(steamapicontext, 'SteamUGC'):
    __fnSteamUGC = steamapicontext.SteamUGC
    def __fnSteamUGCModifier():
        # Add wrappers
        steamugc = __fnSteamUGC()
        if steamugc:
            steamugc.GetItemInstallInfo = PyGetItemInstallInfo
        return steamugc
    steamapicontext.SteamUGC = __fnSteamUGCModifier
