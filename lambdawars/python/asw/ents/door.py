from core.units import UnitInfo
if isserver:
    from srcbase import SOLID_BBOX, DAMAGE_YES
    from entities import entity
    from core.units import UnitBase

    @entity('asw_door')
    class ASWDoor(UnitBase):
        """ Stub for alien swarm doors """
        def Precache(self):
            super(ASWDoor, self).Precache()
            
            self.PrecacheModel(self.SINGLE_DOOR)
            self.PrecacheModel(self.RIGHT_DOOR)
            self.PrecacheModel(self.LEFT_DOOR)
            self.PrecacheModel(self.SINGLE_DOOR_FLIPPED)
            
        def Spawn(self):
            self.SetUnitType('asw_door')
            
            self.SetSolid(SOLID_BBOX)
            self.SetCollisionGroup(self.CalculateOwnerCollisionGroup())
            self.takedamage = DAMAGE_YES
        
            self.Precache()
        
            super(ASWDoor, self).Spawn()
            
        def Event_Killed(self, info):
            super(ASWDoor, self).Event_Killed(info)

            self.Remove()
            
        SINGLE_DOOR = "models/swarm/doors/swarm_singledoor.mdl"
        RIGHT_DOOR = "models/props/doors/heavy_doors/doorright.mdl"
        LEFT_DOOR = "models/props/doors/heavy_doors/doorleft.mdl"
        SINGLE_DOOR_FLIPPED = "models/swarm/doors/swarm_singledoor_flipped.mdl"

class ASWDoorInfo(UnitInfo):
    name = 'asw_door'
    cls_name = 'asw_door'
    health = 100