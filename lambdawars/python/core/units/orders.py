from srcbuiltins import RegisterTickMethod, UnregisterTickMethod
from vmath import vec3_origin, vec3_angle, Vector
from operator import itemgetter
from math import ceil, sqrt
from gameinterface import ConVar, FCVAR_CHEAT, FCVAR_REPLICATED
from particles import *

from core.dispatch import receiver
from core.signals import pre_orderunits, post_orderunits, prelevelshutdown, prelevelinit
from core.decorators import clientonly
from core.util.units import UnitProjector

from navmesh import GetHidingSpotsInRadius

if isclient:
    from . rallyline import FXRallyLine
    from entities import C_HL2WarsPlayer
    
coverspotsearchradius = 320.0
coverspotsearchradiushover = 70.0
coverspotsearchmaxunits = 15
            
# Cover spot shower
if isclient:
    curspots = dict()
    curspotshover = dict()
    
    @receiver(prelevelshutdown)
    def OnPreLevelShutdown(**kwargs):
        ClearAllSpots()
        UnregisterTickMethod(UpdateHidingSpots)
        
    @receiver(prelevelinit)
    def OnPreLevelInit(**kwargs):
        RegisterTickMethod(UpdateHidingSpots, 0.2)
        PrecacheParticleSystem('unit_cover')
        PrecacheParticleSystem('unit_cover_over')
    
    def GetSpotOrigin(hidespots, id):
        for hs in hidespots:
            if hs[0] == id:
                return hs[1]
        return vec3_origin
        
    def ClearSpots(spots, deletespots):
        for key in deletespots:
            spots[key].StopEmission(False, True, False, True)
            del spots[key]
        
    def ClearAllSpots():
        ClearSpots(curspots, list(curspots.keys()))
        ClearSpots(curspotshover, list(curspotshover.keys()))
        
    def CreateNewSpots(spots, hidespots, newspots, effectname):
        for key in newspots:
            size = Vector(12, 12, 12)
            spots[key] = CNewParticleEffect.Create(None, effectname)
            spots[key].SetControlPoint(0, GetSpotOrigin(hidespots, key))
            spots[key].SetControlPoint(1, Vector(1, 1, 0))
            spots[key].SetControlPoint(2, size)
            
    def UpdateHidingSpots():
        player = C_HL2WarsPlayer.GetLocalPlayer()
        selection = player.GetSelection() if player else []
        if (not player or len(selection) > coverspotsearchmaxunits or 
                not player.IsStrategicModeOn()):
            ClearAllSpots()
            return
            
        unit = selection[0] if selection else None
        
        curkeys = set(curspots.keys())
        curkeyshover = set(curspotshover.keys())

        hidespots = GetHidingSpotsInRadius(player.GetMouseData().endpos+Vector(0, 0, 48.0), coverspotsearchradius,
                                           unit, False)
        hidespotshover = GetHidingSpotsInRadius(player.GetMouseData().endpos+Vector(0, 0, 48.0),
                                                coverspotsearchradiushover, unit, False)
        #ndebugoverlay.Cross3D(player.GetMouseData().endpos+Vector(0,0,64.0), 64.0, 255, 0, 0, False, 1.0)
        
        ids = set(map(itemgetter(0), hidespots))
        idshover = set(map(itemgetter(0), hidespotshover))
        
        deletekeys = curkeys - ids - idshover
        deletekeyshover = curkeyshover - idshover
        newkeys = ids - curkeys
        newkeyshover = idshover - curkeyshover
        
        ClearSpots(curspots, deletekeys)
        ClearSpots(curspotshover, deletekeyshover)
            
        CreateNewSpots(curspots, hidespots, newkeys, 'unit_cover')
        CreateNewSpots(curspotshover, hidespotshover, newkeyshover, 'unit_cover_over')

if isclient:
    # Rally line methods
    class OrderRallyLine(FXRallyLine):
        def __init__(self, prevorder, nextorder, rallylinemat='vgui/rallyline'):
            self.nextorder = nextorder
            
            super().__init__(rallylinemat, Vector(1, 1, 1), 
                    prevorder.position, nextorder.position,
                    ent1=prevorder.target, ent2=nextorder.target)

class Order(object):
    def __init__(self, type=0, position=vec3_origin, angle=vec3_angle, 
                       target=None, selection=[], originalposition=None, repeat=False):
        """ Creates a new Order object for an Unit.
        
            Kwargs:
               type (int): The type of order (Move, attack, ability)
               position (Vector): Target position (if used)
               angle (QAngle): Unit arrival facing direction (if used)
               target (Entity): Target entity of this Order (if used)
               selection (list): The selection of the player during issuing the order
               originalposition (Vector): The original position ordered by the player.
                                          Units may modify the position to avoid cluttering to the same
                                          target position when moving.
               repeat (bool): If this order is repeated or not. This is used for patrolling.
        """
        super().__init__()
        self.type = type
        self.position = position
        self.originalposition = position if not originalposition else originalposition
        self.angle = angle
        self.target = target
        self.selection = selection
        self.repeat = repeat
       
    def __str__(self):
        return '<unit: %s, order type %s, ability: %s, repeat: %s>' % (self.unit, self.type, self.ability, self.repeat)
        
    def AllowAutoCast(self, unit):
        if self.ability:
            return self.ability.AllowAutoCast(unit)
        return False
        
    def Remove(self, dispatchevent=True, allowrepeat=False):
        """ Removes the order from the owning unit.
            No-op in casen no unit is attached.

            Kwargs:
                dispatchevent (bool): Dispatch clear order event.
                allowrepeat (bool): Can be repeated (patrol code)
        """
        unit = self.unit
        if not unit:
            return False

        unit.ClearOrder(idx=unit.orders.index(self), dispatchevent=dispatchevent, allowrepeat=allowrepeat)
        return True
        
    def OnRemove(self):
        unit = self.unit
        if self.ability:
            self.ability.OnUnitOrderEnded(unit)
        if self.callback:
            self.callback(unit)
            
        self.DestroyRallyLine()
        
    def OnPrevOrderChanged(self, prevorder=None):
        """ Called when we think the previous order in the unit order queue changed.
            The previous order is None in case there is no such order. 
            
            The most "previous" order is the order currently being executed.
            The most "next" order is the last order in the queue.

            Kwargs:
                prevorder (Order): The previous order
        """
        self.DestroyRallyLine()

        unit = self.unit
        if isclient and unit.selected and len(unit.orders) > 1:
            while prevorder and not prevorder.position and not prevorder.target:
                idx = unit.orders.index(prevorder)
                if idx == 0:
                    prevorder = None
                else:
                    prevorder = unit.orders[idx-1]
                    
            if prevorder:
                self.CreateRallyLine(prevorder)
            elif unit.curorder == self:
                # Front order, connect line to unit
                self.rallyline = FXRallyLine(self.GetRallyLineMat(), Vector(1, 1, 1), 
                    vec3_origin, self.position, ent1=unit.GetHandle(), ent2=self.target)
                    
    @clientonly
    def GetRallyLineMat(self):
        rallylinemat = self.rallylinemat
        if self.ability and self.ability.rallylinemat:
            rallylinemat = self.ability.rallylinemat
        return rallylinemat
        
    @clientonly
    def DestroyRallyLine(self):
        if self.rallyline:
            self.rallyline.Destroy()
            self.rallyline = None
            
    @clientonly
    def CreateRallyLine(self, prevorder):
        if self.rallyline:
            return

        self.rallyline = OrderRallyLine(prevorder, self, rallylinemat=self.GetRallyLineMat())

    unit = None
    ability = None
    hidespot = None
    callback = None # Method called when the order is cleared
    repeat = False
    # Force face the arrival angle
    force_face_angle = False
    
    rallylinemat = 'vgui/rallyline'
    rallyline = None

    # Types
    ORDER_MOVE = 0
    ORDER_ENEMY = 1
    ORDER_ABILITY = 2

class OrderAttack(Order):
    rallylinemat = 'vgui/rallyline_attack'

class OrderAbility(Order):
    rallylinemat = 'vgui/rallyline_defend'

sv_formation_type = ConVar('sv_formation_type', '0', FCVAR_CHEAT | FCVAR_REPLICATED)

class GroupMoveOrder(UnitProjector):
    """ Group ordering code (formations) """
    def __init__(self, player, position, units=None, target=None, findhidespot=None):
        super().__init__(position, units)

        self.player = player
        self.target = target
        self.findhidespot = findhidespot

    def AddUnit(self, unit):
        self.units.append(unit)

    def ComputeSquareFormation(self):
        self.positions = []
        sizesqrt = int(ceil(sqrt(len(self.units))))
        hsizesqrt = int(sizesqrt/2)
        for i in range(sizesqrt):
            for j in range(sizesqrt):
                x = self.position.x + (i - hsizesqrt)*64.0
                y = self.position.y + (j - hsizesqrt)*64.0
                self.positions.append(Vector(x, y, self.position.z))

    def Apply(self):
        # Remove target if in selection
        if self.target in self.units:
            self.target = None

        # If we have no target, determine if the units should find cover
        if not self.target and self.findhidespot == None:
            hidespotshover = GetHidingSpotsInRadius(self.player.GetMouseData().groundendpos+Vector(0, 0, 48.0),
                                                    coverspotsearchradiushover, self.units[0] if self.units else None,
                                                    False)
            self.findhidespot = len(hidespotshover) > 0 and (len(self.units) <= coverspotsearchmaxunits)

        self.Execute()

    def ExecuteUnitForPosition(self, unit, target_pos):
        data = self.player.GetMouseDataRightPressed()
        angle = unit.CalculateArrivalAngle(data, self.player.GetMouseDataRightReleased())

        unit.MoveOrderInternal(target_pos, angle=angle, selection=self.units,
                               originalposition=self.position, target=self.target,
                               findhidespot=self.findhidespot, coverspotsearchradius=self.coverspotsearchradius)

    #: Coverspot search radius
    coverspotsearchradius = coverspotsearchradius

groupmoveorder = None
def AddToGroupMoveOrder(unit):
    if groupmoveorder:
        groupmoveorder.AddUnit(unit)
        return True
    return False

@receiver(pre_orderunits)
def PreOrderUnits(player, **kwargs):
    global groupmoveorder
    data = player.GetMouseDataRightPressed()
    
    target = None
    ent = data.ent
    if ent and ent.IsUnit() and ent.IsAlive():
        target = ent
    
    groupmoveorder = None
    
    # Allow the target entity to override the default group order instance
    if target and target.IsUnit():
        groupmoveorder = target.TargetOverrideGroupOrder(player, data)
    
    if not groupmoveorder:
        groupmoveorder = GroupMoveOrder(player, data.groundendpos, target=target)
    
@receiver(post_orderunits)
def PostOrderUnits(player, **kwargs):
    global groupmoveorder

    if groupmoveorder:
        groupmoveorder.Apply()
        groupmoveorder = None
    
    if isclient:
        data = player.GetMouseData()
        targetent = data.ent
        if targetent and targetent.IsUnit():
            DispatchParticleEffect('clicked_default', PATTACH_ABSORIGIN_FOLLOW, data.ent)
        else:
            DispatchParticleEffect('clicked_default', player.GetMouseData().endpos, vec3_angle)
