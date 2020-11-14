from entities import entity, CBaseEntity
from fields import IntegerField, StringField
from core.units import CreateUnitFancy
import ndebugoverlay
from vmath import Vector
if isserver:
    from entities import eventqueue, variant_t, entlist

@entity('npc_dota_spawner')
class NPCDotaSpawner(CBaseEntity):
    def Spawn(self):
        super(NPCDotaSpawner, self).Spawn()
        
        self.SetThink(self.SpawnNPCThink, gpGlobals.curtime + 5)
        
    def SpawnNPC(self):
        pass
        
    def SpawnNPCThink(self):
        units = self.SpawnNPC()
        self.SetNextThink(gpGlobals.curtime + self.spawninterval)
        
    spawninterval = 40
    
@entity('npc_dota_spawner_bad_bot')
@entity('npc_dota_spawner_bad_mid')
@entity('npc_dota_spawner_bad_top')
@entity('npc_dota_spawner_good_bot')
@entity('npc_dota_spawner_good_mid')
@entity('npc_dota_spawner_good_top')
class NPCDotaSpawnerGoodBad(NPCDotaSpawner):
    lane = IntegerField(keyname='lane')
    firstwaypoint = StringField(keyname='NPCFirstWaypoint')
    
    def SpawnNPC(self):
        units = []
        clsname = self.GetClassname()
        owner = self.GetTeamNumber()
        
        spawntarget = self.GetNextTarget()
        spawnorigin = spawntarget.GetAbsOrigin() if spawntarget else self.GetAbsOrigin()
        
        #ndebugoverlay.Box(spawnorigin, -Vector(16, 16, 16), Vector(16, 16, 16), 0, 255, 0, 255, 5.0)
        
        # Spawn units
        isbad = clsname.startswith('npc_dota_spawner_bad')
        meleeunitname = 'npc_dota_creep_badguys_melee' if isbad else 'npc_dota_creep_goodguys_melee'
        rangeunitname = 'npc_dota_creep_badguys_ranged' if isbad else 'npc_dota_creep_goodguys_ranged'
        
        #units.append( CreateUnitFancy(rangeunitname, spawnorigin, owner_number=owner) )
        for i in range(0, 3):
            units.append(CreateUnitFancy(meleeunitname, spawnorigin, owner_number=owner))
                
        # Collect path corners
        pathcornernames = []
        pathcorner = entlist.FindEntityByName(None, self.firstwaypoint)
        while pathcorner:
            name = pathcorner.GetEntityName()
            if name in pathcornernames:
                break
            pathcornernames.append(name)
            pathcorner = pathcorner.GetNextTarget()
        
        if not pathcornernames:
            return
        
        # Order units
        for unit in units:
            value = variant_t()
            value.SetString('%s:attackmove' % self.firstwaypoint)
            eventqueue.AddEvent(unit, 'Order', value, 0, None, None)
            
            for name in pathcornernames[1:]:
                value = variant_t()
                value.SetString('%s:attackmove' % name)
                eventqueue.AddEvent(unit, 'QueueOrder', value, 0, None, None)
        
        return units
        