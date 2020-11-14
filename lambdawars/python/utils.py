from srcbase import COLLISION_GROUP_NPC, MASK_NPCSOLID
from vmath import QAngle, anglemod, AngleVectors, Vector, vec3_origin
from math import atan, pi, sqrt, pow
from navmesh import NavMeshGetPositionNearestNavArea, NavMeshAvailable, NavMeshGetPathDistance
from gameinterface import concommand, FCVAR_CHEAT, CSingleUserRecipientFilter
    
from _utils import *
from _entities import Disposition_t

# Tracer Flags
TRACER_FLAG_WHIZ = 0x0001
TRACER_FLAG_USEATTACHMENT = 0x0002

TRACER_DONT_USE_ATTACHMENT = -1

# To be used with UTIL_ClientPrintAll
HUD_PRINTNOTIFY = 1
HUD_PRINTCONSOLE = 2
HUD_PRINTTALK = 3
HUD_PRINTCENTER = 4

# UTIL_BloodSpray flags
FX_BLOODSPRAY_DROPS = 0x01
FX_BLOODSPRAY_GORE = 0x02
FX_BLOODSPRAY_CLOUD = 0x04
FX_BLOODSPRAY_ALL = 0xFF

if isserver:
    def ClientPrint(player, msg_dest, msg_name, param1, param2, param3, param4):
        if not player:
            return

        user = CSingleUserRecipientFilter(player)
        user.MakeReliable()

        UTIL_ClientPrintFilter(user, msg_dest, msg_name, param1, param2, param3, param4)
else:
    def ClientPrint(player, msg_dest, msg_name, param1, param2, param3, param4): pass
    
if isserver:
    def UTIL_GetPlayers():
        """ Gets all connected players. """
        players = []
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if not player or not player.IsConnected():
                continue   
            players.append(player)
        return players
else:
    def UTIL_GetPlayers():
        """ Gets all players client side.
            Note that other player entities might not exist on a client, even
            though they exist on the server. 
        """
        players = []
        for i in range(1, gpGlobals.maxClients+1):
            player = UTIL_PlayerByIndex(i)
            if not player:
                continue   
            players.append(player)
        return players

def ClampYaw( yawSpeedPerSec, current, target, time ):
    """ Clamps a yaw """
    if current != target:
        speed = yawSpeedPerSec * time
        move = target - current

        if target > current:
            if move >= 180:
                move = move - 360
        else:
            if move <= -180:
                move = move + 360

        if move > 0: # turning to the npc's left
            if move > speed:
                move = speed
        else: # turning to the npc's right
            if move < -speed:
                move = -speed
        
        return anglemod(current + move)

    return target
    
class PositionInRadiusInfo(object):
    """ Stores info when scanning for positions in a radius. """
    def __init__(self, startposition, mins, maxs, radius, fan=None, stepsize=None, ignore=None, 
                 beneathlimit = 256.0, mask=MASK_NPCSOLID, testposition=True, usenavmesh=True):
        super(PositionInRadiusInfo, self).__init__()

        self.startposition = Vector(startposition)
        self.position = Vector(startposition)
        self.mins = mins
        self.maxs = maxs
        self._radius = radius
        if fan is None:
            self.fan = QAngle(0, 0, 0)
        else:
            self.fan = fan
        self.ignore = ignore
        self.beneathlimit = beneathlimit
        self.success = False
        self.mask = mask
        self.testposition = testposition
        self.usenavmesh = usenavmesh

        if not stepsize:
            self.ComputeRadiusStepSize() 
        else:
            self.stepsize = int(stepsize)
            self.usecustomstepsize = True
            
    def ComputeRadiusStepSize(self):
        if not self.radius:
            self.stepsize = 0
            return
        perimeter = 2 * pi * self.radius
        sizeunit = int(sqrt(pow(self.maxs.x - self.mins.x, 2)+ pow(self.maxs.y - self.mins.y, 2))*1.25)
        try:
            self.stepsize = max(8, int(360 / (perimeter / sizeunit)))
        except ZeroDivisionError:
            PrintWarning('utils: Zero unit size in PositionInRadiusInfo!\n')
            self.stepsize = max(8, int(360 / (perimeter / 64.0)))
            
    def getradius(self):
        return self._radius
    def setradius(self, radius):
        self._radius = radius
        if not self.usecustomstepsize:
            self.ComputeRadiusStepSize()
    radius = property(getradius, setradius, "Radius")
    
    usecustomstepsize = False
    
def UTIL_FindPositionInRadius(info):
    """ Scans all positions on the perimeter of the circle
        The field success is put to True if a position is found. 
        The field position contains the result. 
        Pass in the info object again to find the next position (for optimization). """
    info.success = False
    starty = int(info.fan.y)
    vecDir = Vector()
    tr = trace_t()
    for info.fan.y in range(starty, 360, info.stepsize):
        AngleVectors(info.fan, vecDir)

        vecTest = info.startposition + vecDir * info.radius

        if info.usenavmesh and NavMeshAvailable():
            endpos = NavMeshGetPositionNearestNavArea(vecTest, info.beneathlimit, unit=info.ignore)
            if endpos == vec3_origin or NavMeshGetPathDistance(vecTest, endpos, unit=info.ignore) < 0:
                continue
        else:
            # Maybe no nav mesh? Fallback to trace line
            UTIL_TraceLine(vecTest, vecTest - Vector(0, 0, info.beneathlimit), info.mask, info.ignore, COLLISION_GROUP_NPC, tr)
            #import ndebugoverlay; ndebugoverlay.Cross3D(tr.endpos, 32.0, 255, 0, 0, False, 10.0)
            if tr.fraction == 1.0:
                continue
            endpos = tr.endpos
        
        endpos.z += -info.mins.z
        
        if info.testposition:
            UTIL_TraceHull( endpos,
                            endpos + Vector(0, 0, 10),
                            info.mins,
                            info.maxs,
                            info.mask,
                            info.ignore,
                            COLLISION_GROUP_NPC,
                            tr )

            if tr.fraction == 1.0:
                info.position = Vector(endpos)
                info.success = True
                info.fan.y += info.stepsize
                return info 
        else:
            info.position = Vector(endpos)
            info.success = True
            info.fan.y += info.stepsize
            return info
    return info

class FindPositionInfo(object):
    def __init__(self, startposition, mins, maxs, startradius=0, maxradius=None, radiusgrow=None, radiusstep=None, ignore=None, 
                 beneathlimit=256.0, mask=MASK_NPCSOLID, testposition=True, usenavmesh=True, startyaw=0):
        """ Find Position information for UTIL_FindPosition.
        
            Args:
                startposition (Vector): position around which to a find a valid position in a radius.
                mins (Vector): The minimum bounds of what we are trying to place.
                maxs (Vector): The maximum bounds of what we are trying to place
                
            Kwargs:
                startradius (float): The radius at which we should start looking for a position.
                maxradius (float/none): The max radius. Fails if reached.
                radiusgrow (float): The radius grow step after each scanned circle at the current radius.
                  If None, this is based on the mins/maxs.
                radiusstep (float): Step size used when scanning the circle. If None, this is based on the mins/maxs.
                ignore (entity): Entity to be ignored during traces
                beneathlimit (float): The maximum beneath limit to a nav area from the scan position
                mask (int): Content mask used during traces.
                testposition (bool): Whether or not to test the position found a on navigation area.
                  This prevents from finding a position which is occupied by a unit (if using the right content mask).
                usenavmesh (bool): Whether or not to use the navigation mesh for finding positions.
                startyaw (float): The starting yaw for scanning in a circle.
        """
        super(FindPositionInfo, self).__init__()
        
        self.position = Vector(startposition)
        self._mins = mins
        self._maxs = maxs
        self.radius = startradius
        self._ignore = ignore
        self.beneathlimit = beneathlimit
        self.success = False
        self.mask = mask
        self.radiusstep = radiusstep
        self.testposition = testposition
        self.usenavmesh = usenavmesh
        
        if not radiusgrow:
            self.radiusgrow = (maxs - mins).Length2D()
        else:
            self.radiusgrow = radiusgrow
            
        if not maxradius:
            self.maxradius = self.radiusgrow * 50.0
        else:
            self.maxradius = maxradius
            
        self.inradiusinfo = PositionInRadiusInfo(self.position, mins, maxs, 0, stepsize=radiusstep,
                ignore=ignore, beneathlimit=beneathlimit, mask=mask, testposition=testposition, 
                usenavmesh=usenavmesh, fan=QAngle(0, startyaw, 0))

    def getmins(self):
        return self._mins
    def setmins(self, mins):
        self._mins = mins
        if self.inradiusinfo: self.inradiusinfo.mins = mins
    mins = property(getmins, setmins, "Mins")
    
    def getmaxs(self):
        return self._maxs
    def setmaxs(self, maxs):
        self._maxs = maxs
        if self.inradiusinfo: self.inradiusinfo.maxs = maxs
    maxs = property(getmaxs, setmaxs, "Maxs")
    
    def getignore(self):
        return self._ignore
    def setignore(self, ignore):
        self._ignore = ignore
        if self.inradiusinfo: self.inradiusinfo.ignore = ignore
    ignore = property(getignore, setignore, "Ignore entity")
    
def UTIL_FindPosition(info):
    """ Finds a position in radius given info.
        You can continue finding the next position by passing in the previous result.
        
        If the navigation mesh is available, it will only try to find a position on 
        the nav mesh (unless info.usenavmesh is False). If no nav mesh is available
        (or ignored), it will fall back to using trace lines.
    
        Args:
            info (FindPositionInfo): Find position parameters and result.
    """
    info.success = False
    tr = trace_t()
    if info.radius == 0:
        # Try startPos
        if info.usenavmesh and NavMeshAvailable():
            endpos = NavMeshGetPositionNearestNavArea(info.position, info.beneathlimit, unit=info.ignore)
            if NavMeshGetPathDistance(info.position, endpos, unit=info.ignore) < 0:
                endpos = vec3_origin
        else:
            # Maybe no nav mesh? Fallback to trace line
            UTIL_TraceLine(info.position, info.position - Vector(0, 0, info.beneathlimit), info.mask, info.ignore, COLLISION_GROUP_NPC, tr)
            endpos = tr.endpos if tr.fraction != 1.0 else vec3_origin
        
        info.radius += info.radiusgrow

        if endpos != vec3_origin:
            endpos.z += -info.mins.z
            if info.testposition:
                UTIL_TraceHull( endpos,
                                endpos + Vector(0, 0, 10),
                                info.mins,
                                info.maxs,
                                info.mask,
                                info.ignore,
                                COLLISION_GROUP_NPC,
                                tr )

                if tr.fraction == 1.0:
                    info.position = Vector(endpos)
                    info.success = True
                    return info
            else:
                info.position = Vector(endpos)
                info.success = True
                return info
                    
    while info.radius <= info.maxradius:
        info.inradiusinfo.radius = info.radius
        UTIL_FindPositionInRadius(info.inradiusinfo)
        if info.inradiusinfo.success:
            info.position = Vector(info.inradiusinfo.position)
            info.success = True        
            return info
        info.inradiusinfo.fan.Init(0,0,0)
        info.radius += info.radiusgrow
    return info
    
def UTIL_FindPositionSimple(targetposition, radius, mins=-Vector(16, 16, 0), maxs=Vector(16, 16, 24)):
    """ Simple version of UTIL_FindPosition. Only accepts a small number of arguments and returns the position.
    
        Args:
            targetposition (Vector): position around which to find a placeable position.
            radius (float): max radius to search in.
          
        Kwargs:
            mins (Vector): The minimum bounds of what we are trying to place.
            maxs (Vector): The maximum bounds of what we are trying to place
    """
    info = FindPositionInfo(targetposition, mins, maxs, maxradius=radius)
    UTIL_FindPosition(info)
    if not info.success:
        return vec3_origin
    return info.position
    
if isserver:
    @concommand('test_findposition', '', FCVAR_CHEAT)
    def TestFindPosition(args):
        import ndebugoverlay
        player = UTIL_GetCommandClient()
        data = player.GetMouseData()
        
        radius = float(args[1])
        info = FindPositionInfo(data.groundendpos, -Vector(16, 16, 16), Vector(16, 16, 16), maxradius=radius)
        for i in range(0, 10000):
            UTIL_FindPosition(info)
            if not info.success:
                break
            ndebugoverlay.Cross3D(info.position, 32.0, 255, 0, 0, False, 10.0)


def UTIL_ListPlayersForOwners(owners):
    """ List players for one or more owners.

        Args:
            owners (iterable): Owners for which to check.
    """
    if type(owners) == int:
        owners = set([owners])
    players = []
    for i in range(1, gpGlobals.maxClients+1):
        player = UTIL_PlayerByIndex(i)
        if player is None:
            continue
        if player.GetOwnerNumber() in owners:
            players.append(player)
    return players

UTIL_ListPlayersForOwnerNumber = UTIL_ListPlayersForOwners
    
def UTIL_ListForOwnerNumberWithDisp(ownernumber, d=Disposition_t.D_LI, skipobservers=True):
    """ Lists players with a certain disposition towards the specified owner. """
    import playermgr 
    players = []
    for i in range(1, gpGlobals.maxClients+1):
        player = UTIL_PlayerByIndex(i)
        if player == None:
            continue
        if playermgr.relationships[(ownernumber, player.GetOwnerNumber())] != d:
            continue
        if skipobservers and player.IsObserver():
            continue
        players.append(player)
    return players
    
def UTIL_ListForOwnerNumberExclDisp(ownernumber, d=Disposition_t.D_LI, skipobservers=True):
    """ Lists players excluding those with a certain disposition towards the specified owner. """
    import playermgr 
    players = []
    for i in range(1, gpGlobals.maxClients+1):
        player = UTIL_PlayerByIndex(i)
        if player == None:
            continue
        if playermgr.relationships[(ownernumber, player.GetOwnerNumber())] == d:
            continue
        if skipobservers and player.IsObserver():
            continue
        players.append(player)
    return players