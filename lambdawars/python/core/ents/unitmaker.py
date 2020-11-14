''' Purpose: An entity that creates NPCs in the game. There are two types of NPC
    makers -- one which creates NPCs using a template NPC, and one which
    creates an NPC via a classname.'''
    
from srcbase import *
from vmath import *
from entities import entity, CPointEntity, CBaseEntity, gEntList, DispatchSpawn, FClassnameIs
from gameinterface import ConVar, FCVAR_CHEAT
from utils import UTIL_TraceHull, UTIL_PlayerByIndex, UTIL_EntitiesInBox, UTIL_RemoveImmediate, trace_t
from fields import FloatField, StringField, IntegerField, EHandleField, OutputField, BooleanField, FlagsField, PlayerField, input, fieldtypes
from core.units import CreateUnitNoSpawn, PrecacheUnit, PlaceUnit, hull

SF_NPC_FADE_CORPSE = ( 1 << 9  )

def DispatchActivate(pEntity):
    #bAsyncAnims = mdlcache.SetAsyncLoad(MDLCACHE_ANIMBLOCK, False) # TODO
    pEntity.Activate()
    #mdlcache.SetAsyncLoad( MDLCACHE_ANIMBLOCK, bAsyncAnims ) # TODO


ai_inhibit_spawners = ConVar("ai_inhibit_spawners", "0", FCVAR_CHEAT)

@entity('info_npc_spawn_destination')
class CNPCSpawnDestination(CPointEntity):
    reusedelay = FloatField(keyname='ReuseDelay')
    renamenpc = StringField(keyname='RenameNPC')
    timenextavailable = FloatField() # TODO: Add a time field
    onspawnnpc = OutputField(keyname='OnSpawnNPC', fieldtype=fieldtypes.FIELD_EHANDLE)

    #---------------------------------------------------------
    #---------------------------------------------------------
    def CNPCSpawnDestination(self):
        # Available right away, the first time.
        self.timenextavailable = gpGlobals.curtime

    #---------------------------------------------------------
    #---------------------------------------------------------
    def IsAvailable(self):
        if self.timenextavailable > gpGlobals.curtime:
            return False
        return True

    #---------------------------------------------------------
    #---------------------------------------------------------
    def OnSpawnedNPC(self, pNPC):
        # Rename the NPC
        if self.renamenpc:
            pNPC.SetName(self.renamenpc)

        self.onspawnnpc.FireOutput( pNPC, self )
        self.timenextavailable = gpGlobals.curtime + self.reusedelay

class CBaseNPCMaker(CBaseEntity):
    maxnumnpcs = IntegerField(keyname='MaxNPCCount')
    maxlivechildren = IntegerField(keyname='MaxLiveChildren')
    spawnfrequency = IntegerField(keyname='SpawnFrequency')
    disabled = BooleanField(keyname='StartDisabled')
    
    livechildren = IntegerField()
    
    onallspawned = OutputField(keyname='OnAllSpawned')
    onallspawneddead = OutputField(keyname='OnAllSpawnedDead')
    onalllivechildrendead = OutputField(keyname='OnAllLiveChildrenDead')
    onspawnnpc = OutputField(keyname='OnSpawnNPC', fieldtype=fieldtypes.FIELD_EHANDLE)
    
    ignoreentity = EHandleField()
    ingoreent = StringField(keyname='IgnoreEntity')
    
    # Spawnflags
    spawnflags = FlagsField(keyname='spawnflags', flags=
        [('SF_NPCMAKER_START_ON', ( 1 << 0 ), False), # start active ( if has targetname )
         ('SF_NPCMAKER_NPCCLIP', ( 1 << 3 ), False), # Children are blocked by NPCclip
         ('SF_NPCMAKER_FADE', ( 1 << 4 ), False, 'Fade Corpse'), # Children's corpses fade
         ('SF_NPCMAKER_INF_CHILD', ( 1 << 5 ), False, 'Infinite Children'), # Infinite number of children
         ('SF_NPCMAKER_NO_DROP', ( 1 << 6 ), False, 'Do Not Drop'), # Do not adjust for the ground's position when checking for spawn
         ('SF_NPCMAKER_HIDEFROMPLAYER', ( 1 << 7 ), False, 'Don\'t Spawn While Visible'), # Don't spawn if the player's looking at me
         ('SF_NPCMAKER_ALWAYSUSERADIUS', ( 1 << 8 ), False), # Use radius spawn whenever spawning
         ('SF_NPCMAKER_NOPRELOADMODELS', ( 1 << 9 ), False)], # Suppress preloading into the cache of all referenced .mdl files
        cppimplemented=True)
            
    #-----------------------------------------------------------------------------
    # Purpose: Spawn
    #-----------------------------------------------------------------------------
    def Spawn(self):
        self.SetSolid(SOLID_NONE)
        self.livechildren = 0
        self.Precache()

        # If I can make an infinite number of NPC, force them to fade
        if self.GetSpawnFlags() & self.SF_NPCMAKER_INF_CHILD:
            self.AddSpawnFlags(self.SF_NPCMAKER_FADE)

        #Start on?
        if self.disabled == False:
            self.SetThink(self.MakerThink)
            self.SetNextThink(gpGlobals.curtime + 0.1)
        else:
            #wait to be activated.
            self.SetThink(self.SUB_DoNothing)

    #-----------------------------------------------------------------------------
    # A not-very-robust check to see if a human hull could fit at self location.
    # used to validate spawn destinations.
    #-----------------------------------------------------------------------------
    def HumanHullFits(self, vecLocation):
        tr = trace_t()
        UTIL_TraceHull(vecLocation,
                       vecLocation + Vector(0, 0, 1),
                       hull.Mins('HULL_HUMAN'),
                       hull.Maxs('HULL_HUMAN'),
                       MASK_NPCSOLID,
                       self.ignoreentity,
                       COLLISION_GROUP_NONE,
                       tr)

        if tr.fraction == 1.0:
            return True

        return False

    #-----------------------------------------------------------------------------
    # Purpose: Returns whether or not it is OK to make an NPC at self instant.
    #-----------------------------------------------------------------------------
    def CanMakeNPC(self, bIgnoreSolidEntities=False):
        if ai_inhibit_spawners.GetBool():
            return False

        if self.maxlivechildren > 0 and self.livechildren >= self.maxlivechildren:
        # not allowed to make a new one yet. Too many live ones out right now.
            return False

        if self.ingoreent:
            self.ignoreentity = gEntList.FindEntityByName( None, self.ingoreent )

        mins = self.GetAbsOrigin() - Vector( 34, 34, 0 )
        maxs = self.GetAbsOrigin() + Vector( 34, 34, 0 )
        maxs.z = self.GetAbsOrigin().z
        
        # If we care about not hitting solid entities, look for 'em
        if not bIgnoreSolidEntities:
            pList = UTIL_EntitiesInBox(128, mins, maxs, FL_CLIENT|FL_NPC)
            if pList:
                #Iterate through the list and check the results
                for i in range(0, len(pList)):
                    #Don't build on top of another entity
                    if pList[i] == None:
                        continue

                    #If one of the entities is solid, then we may not be able to spawn now
                    if (pList[i].GetSolidFlags() & FSOLID_NOT_SOLID) == False:
                        # Since the outer method doesn't work well around striders on account of their huge bounding box.
                        # Find the ground under me and see if a human hull would fit there.
                        tr = trace_t()
                        UTIL_TraceHull( self.GetAbsOrigin() + Vector( 0, 0, 2 ),
                                        self.GetAbsOrigin() - Vector( 0, 0, 8192 ),
                                        hull.Mins('HULL_HUMAN'),
                                        hull.Maxs('HULL_HUMAN'),
                                        MASK_NPCSOLID,
                                        self.ignoreentity,
                                        COLLISION_GROUP_NONE,
                                        tr )

                        if not self.HumanHullFits(tr.endpos + Vector( 0, 0, 1 ) ):
                            return False

        # Do we need to check to see if the player's looking?
        if self.HasSpawnFlags(self.SF_NPCMAKER_HIDEFROMPLAYER):
            for i in range(1, gpGlobals.maxClients+1):
                pPlayer = UTIL_PlayerByIndex(i)
                if pPlayer:
                    # Only spawn if the player's looking away from me
                    origin = self.GetAbsOrigin()
                    if pPlayer.FInViewCone(origin) and pPlayer.FVisible(origin):
                        if not (pPlayer.GetFlags() & FL_NOTARGET):
                            return False
                        DevMsg(2, "Spawner %s spawning even though seen due to notarget\n" % (self.GetEntityName()))
        return True

    #-----------------------------------------------------------------------------
    # Purpose: If this had a finite number of children, return True if they've all
    #			been created.
    #-----------------------------------------------------------------------------
    def IsDepleted(self):
        if (self.GetSpawnFlags() & self.SF_NPCMAKER_INF_CHILD) or self.maxnumnpcs > 0:
            return False
        return True

    #-----------------------------------------------------------------------------
    # Purpose: Toggle the spawner's state
    #-----------------------------------------------------------------------------
    def Toggle(self):
        if self.disabled:
            self.Enable()
        else:
            self.Disable()

    #-----------------------------------------------------------------------------
    # Purpose: Start the spawner
    #-----------------------------------------------------------------------------
    def Enable(self):
        # can't be enabled once depleted
        if self.IsDepleted():
            return

        self.disabled = False
        self.SetThink(self.MakerThink)
        self.SetNextThink(gpGlobals.curtime)

    #-----------------------------------------------------------------------------
    # Purpose: Stop the spawner
    #-----------------------------------------------------------------------------
    def Disable(self):
        self.disabled = True
        self.SetThink ( None )

    #-----------------------------------------------------------------------------
    # Purpose: Input handler that spawns an NPC.
    #-----------------------------------------------------------------------------
    @input(inputname='Spawn')
    def InputSpawnNPC(self, inputdata):
        if not self.IsDepleted():
            self.MakeNPC()

    #-----------------------------------------------------------------------------
    # Purpose: Input hander that starts the spawner
    #-----------------------------------------------------------------------------
    @input(inputname='Enable')
    def InputEnable(self, inputdata):
        self.Enable()

    #-----------------------------------------------------------------------------
    # Purpose: Input hander that stops the spawner
    #-----------------------------------------------------------------------------
    @input(inputname='Disable')
    def InputDisable(self, inputdata):
        self.Disable()

    #-----------------------------------------------------------------------------
    # Purpose: Input hander that toggles the spawner
    #-----------------------------------------------------------------------------
    @input(inputname='Toggle')
    def InputToggle(self, inputdata):
        self.Toggle()

    #-----------------------------------------------------------------------------
    # Purpose: 
    #-----------------------------------------------------------------------------
    @input(inputname='SetMaxChildren', fieldtype=fieldtypes.FIELD_INTEGER)
    def InputSetMaxChildren(self, inputdata):
        self.maxnumnpcs = inputdata.value.Int()

    #-----------------------------------------------------------------------------
    # Purpose: 
    #-----------------------------------------------------------------------------
    @input(inputname='AddMaxChildren', fieldtype=fieldtypes.FIELD_INTEGER)
    def InputAddMaxChildren(self, inputdata):
        self.maxnumnpcs += inputdata.value.Int()

    #-----------------------------------------------------------------------------
    # Purpose: 
    #-----------------------------------------------------------------------------
    @input(inputname='SetMaxLiveChildren', fieldtype=fieldtypes.FIELD_INTEGER)
    def InputSetMaxLiveChildren(self, inputdata):
        self.maxlivechildren = inputdata.value.Int()

    @input(inputname='SetSpawnFrequency', fieldtype=fieldtypes.FIELD_FLOAT)
    def InputSetSpawnFrequency(self, inputdata):
        self.spawnfrequency = inputdata.value.Float()
        
    def ChildPreSpawn(self, pChild):
        pass

    def ChildPostSpawn(self, pChild):
        # If I'm stuck inside any props, remove them
        bFound = True
        while bFound:
            tr = trace_t()
            UTIL_TraceHull( pChild.GetAbsOrigin(), pChild.GetAbsOrigin(), pChild.WorldAlignMins(), pChild.WorldAlignMaxs(), MASK_NPCSOLID, pChild, COLLISION_GROUP_NONE, tr )
            #NDebugOverlay::Box( pChild.GetAbsOrigin(), pChild.WorldAlignMins(), pChild.WorldAlignMaxs(), 0, 255, 0, 32, 5.0 )
            if tr.fraction != 1.0 and tr.ent:
                if FClassnameIs(tr.ent, "prop_physics"):
                    # Set to non-solid so self loop doesn't keep finding it
                    tr.ent.AddSolidFlags(FSOLID_NOT_SOLID)
                    UTIL_RemoveImmediate(tr.ent)
                    continue

            bFound = False
        
        if self.ignoreentity != None:
            pChild.SetOwnerEntity( self.ignoreentity )

    #-----------------------------------------------------------------------------
    # Purpose: Creates a new NPC every so often.
    #-----------------------------------------------------------------------------
    def MakerThink(self):
        self.SetNextThink( gpGlobals.curtime + self.spawnfrequency )

        self.MakeNPC()

    #-----------------------------------------------------------------------------
    # Purpose: 
    # Input  : *pVictim - 
    #-----------------------------------------------------------------------------
    def DeathNotice(self, pVictim):
        # ok, we've gotten the deathnotice from our child, now clear out its owner if we don't want it to fade.
        self.livechildren -= 1

        # If we're here, we're getting erroneous death messages from children we haven't created
        #AssertMsg( self.livechildren >= 0, "npc_maker receiving child death notice but thinks has no children\n" )

        if self.livechildren <= 0:
            self.onalllivechildrendead.FireOutput(self, self)

            # See if we've exhausted our supply of NPCs
            if ((self.GetSpawnFlags() & self.SF_NPCMAKER_INF_CHILD) == False) and self.IsDepleted():
                # Signal that all our children have been spawned and are now dead
                self.onallspawneddead.FireOutput(self, self)
                
@entity('unit_maker', iconsprite='editor/unit_maker.vmt')
@entity('npc_maker', iconsprite='editor/unit_maker.vmt')
class CNPCMaker(CBaseNPCMaker):
    npcclassname = StringField(keyname='NPCType')
    childtargetname = StringField(keyname='NPCTargetname')
    squadname = StringField(keyname='NPCSquadName')
    spawnequipment = StringField(keyname='additionalequipment')
    hintgroup = StringField(keyname='NPCHintGroup')
    relationshipstring = StringField(keyname='Relationship')

    #-----------------------------------------------------------------------------
    # Constructor
    #-----------------------------------------------------------------------------
    def __init__(self):
        super().__init__()
        
        self.spawnequipment = ''

    #-----------------------------------------------------------------------------
    # Purpose: Precache the target NPC
    #-----------------------------------------------------------------------------
    def Precache(self):
        super().Precache()

        unitname = self.npcclassname
        if not unitname:
            PrintWarning("npc_maker %s has no specified NPC-to-spawn classname.\n" % (self.GetEntityName()))
        else:
            PrecacheUnit(unitname)

    #-----------------------------------------------------------------------------
    # Purpose: Creates the NPC.
    #-----------------------------------------------------------------------------
    def MakeNPC(self):
        if not self.CanMakeNPC(True):
            return
            
        # Strip pitch and roll from the spawner's angles. Pass only yaw to the spawned NPC.
        angles = self.GetAbsAngles()
        angles.x = 0.0
        angles.z = 0.0

        pent = CreateUnitNoSpawn(self.npcclassname, self.GetOwnerNumber())
        if not pent:
            PrintWarning("None Ent in NPCMaker!\n" )
            return

        # ------------------------------------------------
        #  Intialize spawned NPC's relationships
        # ------------------------------------------------
        pent.SetRelationshipString(self.relationshipstring)
        
        origin = self.GetAbsOrigin()
        PlaceUnit(pent, origin)

        #pent.AddSpawnFlags(self.SF_NPC_FALL_TO_GROUND)

        if self.GetSpawnFlags() & self.SF_NPCMAKER_FADE:
            pent.AddSpawnFlags(SF_NPC_FADE_CORPSE)

        pent.spawnequipment = self.spawnequipment
        #pent.SetSquadName(self.squadname)
        #pent.SetHintGroup(self.hintgroup)
        
        self.ChildPreSpawn(pent)

        DispatchSpawn(pent)
        pent.SetOwnerEntity(self)
        DispatchActivate(pent)

        if self.childtargetname:
            # if I have a netname (overloaded), give the child NPC that name as a targetname
            pent.SetName(self.childtargetname)

        self.ChildPostSpawn(pent)
        
        self.onspawnnpc.Set(pent, pent, self)

        self.livechildren += 1# count self NPC

        if not (self.GetSpawnFlags() & self.SF_NPCMAKER_INF_CHILD):
            self.maxnumnpcs -= 1

            if self.IsDepleted():
                self.onallspawned.FireOutput( self, self )

                # Disable self forever.  Don't kill it because it still gets death notices
                self.SetThink(None)
                #self.SetUse(None) # TODO

'''
#-----------------------------------------------------------------------------
# Purpose: Creates new NPCs from a template NPC. The template NPC must be marked
#			as a template (spawnflag) and does not spawn.
#-----------------------------------------------------------------------------

LINK_ENTITY_TO_CLASS( npc_template_maker, CTemplateNPCMaker )

BEGIN_DATADESC( CTemplateNPCMaker )

	DEFINE_KEYFIELD( m_iszTemplateName, FIELD_STRING, "TemplateName" ),
	DEFINE_KEYFIELD( m_flRadius, FIELD_FLOAT, "radius" ),
	DEFINE_FIELD( m_iszTemplateData, FIELD_STRING ),
	DEFINE_KEYFIELD( m_iszDestinationGroup, FIELD_STRING, "DestinationGroup" ),
	DEFINE_KEYFIELD( m_CriterionVisibility, FIELD_INTEGER, "CriterionVisibility" ),
	DEFINE_KEYFIELD( m_CriterionDistance, FIELD_INTEGER, "CriterionDistance" ),
	DEFINE_KEYFIELD( m_iMinSpawnDistance, FIELD_INTEGER, "MinSpawnDistance" ),

	DEFINE_INPUTFUNC( FIELD_VOID, "SpawnNPCInRadius", InputSpawnInRadius ),
	DEFINE_INPUTFUNC( FIELD_VOID, "SpawnNPCInLine", InputSpawnInLine ),
	DEFINE_INPUTFUNC( FIELD_INTEGER, "SpawnMultiple", InputSpawnMultiple ),
	DEFINE_INPUTFUNC( FIELD_STRING, "ChangeDestinationGroup", InputChangeDestinationGroup ),
	DEFINE_INPUTFUNC( FIELD_INTEGER, "SetMinimumSpawnDistance", InputSetMinimumSpawnDistance ),

END_DATADESC()


#-----------------------------------------------------------------------------
# A hook that lets derived NPC makers do special stuff when precaching.
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::PrecacheTemplateEntity( CBaseEntity *pEntity )

	pEntity.Precache()



void CTemplateNPCMaker::Precache()

	BaseClass::Precache()

	if ( !m_iszTemplateData )
	
		#
		# self must be the first time we're activated, not a load from save game.
		# Look up the template in the template database.
		#
		if (!m_iszTemplateName)
		
			Warning( "npc_template_maker %s has no template NPC!\n", STRING(GetEntityName()) )
			UTIL_Remove( self )
			return
		
		else
		
			m_iszTemplateData = Templates_FindByTargetName(STRING(m_iszTemplateName))
			if ( m_iszTemplateData == None_STRING )
			
				DevWarning( "npc_template_maker %s: template NPC %s not found!\n", STRING(GetEntityName()), STRING(m_iszTemplateName) )
				UTIL_Remove( self )
				return
			
		
	

	Assert( m_iszTemplateData != None_STRING )

	# If the mapper marked self as "preload", then instance the entity preache stuff and delete the entity
	#if ( !HasSpawnFlags(SF_NPCMAKER_NOPRELOADMODELS) )
	if ( m_iszTemplateData != None_STRING )
	
		CBaseEntity *pEntity = None
		MapEntity_ParseEntity( pEntity, STRING(m_iszTemplateData), None )
		if ( pEntity != None )
		
			PrecacheTemplateEntity( pEntity )
			UTIL_RemoveImmediate( pEntity )
		
	


#define MAX_DESTINATION_ENTS	100
CNPCSpawnDestination *CTemplateNPCMaker::FindSpawnDestination()

	CNPCSpawnDestination *pDestinations[ MAX_DESTINATION_ENTS ]
	CBaseEntity *pEnt = None
	CBasePlayer *pPlayer = UTIL_GetLocalPlayer()
	int	count = 0

	if( !pPlayer )
	
		return None
	

	# Collect all the qualifiying destination ents
	pEnt = gEntList.FindEntityByName( None, m_iszDestinationGroup )

	if( !pEnt )
	
		DevWarning("Template NPC Spawner (%s) doesn't have any spawn destinations!\n", GetDebugName() )
		return None
	
	
	while( pEnt )
	
		CNPCSpawnDestination *pDestination

		pDestination = dynamic_cast <CNPCSpawnDestination*>(pEnt)

		if( pDestination and pDestination.IsAvailable() )
		
			bool fValid = True
			Vector vecTest = pDestination.GetAbsOrigin()

			if( m_CriterionVisibility != TS_YN_DONT_CARE )
			
				# Right now View Cone check is omitted intentionally.
				Vector vecTopOfHull = NAI_Hull::Maxs( HULL_HUMAN )
				vecTopOfHull.x = 0
				vecTopOfHull.y = 0
				bool fVisible = (pPlayer.FVisible( vecTest ) or pPlayer.FVisible( vecTest + vecTopOfHull ) )

				if( m_CriterionVisibility == TS_YN_YES )
				
					if( !fVisible )
						fValid = False
				
				else
				
					if( fVisible )
					
						if ( !(pPlayer.GetFlags() & FL_NOTARGET) )
							fValid = False
						else
							DevMsg( 2, "Spawner %s spawning even though seen due to notarget\n", STRING( GetEntityName() ) )
					
				
			

			if( fValid )
			
				pDestinations[ count ] = pDestination
				count++
			
		

		pEnt = gEntList.FindEntityByName( pEnt, m_iszDestinationGroup )
	

	if( count < 1 )
		return None

	# Now find the nearest/farthest based on distance criterion
	if( m_CriterionDistance == TS_DIST_DONT_CARE )
	
		# Pretty lame way to pick randomly. Try a few times to find a random
		# location where a hull can fit. Don't try too many times due to performance
		# concerns.
		for( int i = 0  i < 5  i++ )
		
			CNPCSpawnDestination *pRandomDest = pDestinations[ rand() % count ]

			if( HumanHullFits( pRandomDest.GetAbsOrigin() ) )
			
				return pRandomDest
			
		

		return None
	
	else
	
		if( m_CriterionDistance == TS_DIST_NEAREST )
		
			float flNearest = FLT_MAX
			CNPCSpawnDestination *pNearest = None

			for( int i = 0  i < count  i++ )
			
				Vector vecTest = pDestinations[ i ].GetAbsOrigin()
				float flDist = ( vecTest - pPlayer.GetAbsOrigin() ).Length()

				if ( m_iMinSpawnDistance != 0 and m_iMinSpawnDistance > flDist )
					continue

				if( flDist < flNearest and HumanHullFits( vecTest ) )
				
					flNearest = flDist
					pNearest = pDestinations[ i ]
				
			

			return pNearest
		
		else
		
			float flFarthest = 0
			CNPCSpawnDestination *pFarthest = None

			for( int i = 0  i < count  i++ )
			
				Vector vecTest = pDestinations[ i ].GetAbsOrigin()
				float flDist = ( vecTest - pPlayer.GetAbsOrigin() ).Length()

				if ( m_iMinSpawnDistance != 0 and m_iMinSpawnDistance > flDist )
					continue

				if( flDist > flFarthest and HumanHullFits( vecTest ) )
				
					flFarthest = flDist
					pFarthest = pDestinations[ i ]
				
			

			return pFarthest
		
	

	return None


#-----------------------------------------------------------------------------
# Purpose: 
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::MakeNPC( void )

	# If we should be using the radius spawn method instead, do so
	if ( m_flRadius and HasSpawnFlags(SF_NPCMAKER_ALWAYSUSERADIUS) )
	
		MakeNPCInRadius()
		return
	

	if (!CanMakeNPC( ( m_iszDestinationGroup != None_STRING ) ))
		return

	CNPCSpawnDestination *pDestination = None
	if ( m_iszDestinationGroup != None_STRING )
	
		pDestination = FindSpawnDestination()
		if ( !pDestination )
		
			DevMsg( 2, "%s '%s' failed to find a valid spawnpoint in destination group: '%s'\n", GetClassname(), STRING(GetEntityName()), STRING(m_iszDestinationGroup) )
			return
		
	

	CAI_BaseNPC	*pent = None
	CBaseEntity *pEntity = None
	MapEntity_ParseEntity( pEntity, STRING(m_iszTemplateData), None )
	if ( pEntity != None )
	
		pent = (CAI_BaseNPC *)pEntity
	

	if ( !pent )
	
		Warning("None Ent in NPCMaker!\n" )
		return
	
	
	if ( pDestination )
	
		pent.SetAbsOrigin( pDestination.GetAbsOrigin() )

		# Strip pitch and roll from the spawner's angles. Pass only yaw to the spawned NPC.
		QAngle angles = pDestination.GetAbsAngles()
		angles.x = 0.0
		angles.z = 0.0
		pent.SetAbsAngles( angles )

		pDestination.OnSpawnedNPC( pent )
	
	else
	
		pent.SetAbsOrigin( GetAbsOrigin() )

		# Strip pitch and roll from the spawner's angles. Pass only yaw to the spawned NPC.
		QAngle angles = GetAbsAngles()
		angles.x = 0.0
		angles.z = 0.0
		pent.SetAbsAngles( angles )
	

	self.onspawnnpc.Set( pEntity, pEntity, self )

	if ( m_spawnflags & SF_NPCMAKER_FADE )
	
		pent.AddSpawnFlags( SF_NPC_FADE_CORPSE )
	

	pent.RemoveSpawnFlags( SF_NPC_TEMPLATE )

	if ( ( m_spawnflags & SF_NPCMAKER_NO_DROP ) == False )
	
		pent.RemoveSpawnFlags( SF_NPC_FALL_TO_GROUND ) # don't fall, slam
	

	ChildPreSpawn( pent )

	DispatchSpawn( pent )
	pent.SetOwnerEntity( self )
	DispatchActivate( pent )

	ChildPostSpawn( pent )

	self.livechildren++# count self NPC

	if (!(m_spawnflags & SF_NPCMAKER_INF_CHILD))
	
		self.maxnumnpcs--

		if ( IsDepleted() )
		
			self.onallspawned.FireOutput( self, self )

			# Disable self forever.  Don't kill it because it still gets death notices
			SetThink( None )
			SetUse( None )
		
	


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::MakeNPCInLine( void )

	if (!CanMakeNPC(True))
		return

	CAI_BaseNPC	*pent = None
	CBaseEntity *pEntity = None
	MapEntity_ParseEntity( pEntity, STRING(m_iszTemplateData), None )
	if ( pEntity != None )
	
		pent = (CAI_BaseNPC *)pEntity
	

	if ( !pent )
	
		Warning("None Ent in NPCMaker!\n" )
		return
	
	
	self.onspawnnpc.Set( pEntity, pEntity, self )

	PlaceNPCInLine( pent )

	pent.AddSpawnFlags( SF_NPC_FALL_TO_GROUND )

	pent.RemoveSpawnFlags( SF_NPC_TEMPLATE )
	ChildPreSpawn( pent )

	DispatchSpawn( pent )
	pent.SetOwnerEntity( self )
	DispatchActivate( pent )

	ChildPostSpawn( pent )

	self.livechildren++# count self NPC

	if (!(m_spawnflags & SF_NPCMAKER_INF_CHILD))
	
		self.maxnumnpcs--

		if ( IsDepleted() )
		
			self.onallspawned.FireOutput( self, self )

			# Disable self forever.  Don't kill it because it still gets death notices
			SetThink( None )
			SetUse( None )
		
	


#-----------------------------------------------------------------------------
bool CTemplateNPCMaker::PlaceNPCInLine( CAI_BaseNPC *pNPC )

	Vector vecPlace
	Vector vecLine

	GetVectors( &vecLine, None, None )

	# invert self, line up NPC's BEHIND the maker.
	vecLine *= -1

	trace_t tr
	UTIL_TraceLine( GetAbsOrigin(), GetAbsOrigin() - Vector( 0, 0, 8192 ), MASK_SHOT, pNPC, COLLISION_GROUP_NONE, &tr )
	vecPlace = tr.endpos
	float flStepSize = pNPC.GetHullWidth()

	# Try 10 times to place self npc.
	for( int i = 0  i < 10  i++ )
	
		UTIL_TraceHull( vecPlace,
						vecPlace + Vector( 0, 0, 10 ),
						pNPC.GetHullMins(),
						pNPC.GetHullMaxs(),
						MASK_SHOT,
						pNPC,
						COLLISION_GROUP_NONE,
						&tr )

		if( tr.fraction == 1.0 )
		
			pNPC.SetAbsOrigin( tr.endpos )
			return True
		

		vecPlace += vecLine * flStepSize
	

	DevMsg("**Failed to place NPC in line!\n")
	return False


#-----------------------------------------------------------------------------
# Purpose: Place NPC somewhere on the perimeter of my radius.
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::MakeNPCInRadius( void )

	if ( !CanMakeNPC(True))
		return

	CAI_BaseNPC	*pent = None
	CBaseEntity *pEntity = None
	MapEntity_ParseEntity( pEntity, STRING(m_iszTemplateData), None )
	if ( pEntity != None )
	
		pent = (CAI_BaseNPC *)pEntity
	

	if ( !pent )
	
		Warning("None Ent in NPCMaker!\n" )
		return
	
	
	if ( !PlaceNPCInRadius( pent ) )
	
		# Failed to place the NPC. Abort
		UTIL_RemoveImmediate( pent )
		return
	

	self.onspawnnpc.Set( pEntity, pEntity, self )

	pent.AddSpawnFlags( SF_NPC_FALL_TO_GROUND )

	pent.RemoveSpawnFlags( SF_NPC_TEMPLATE )
	ChildPreSpawn( pent )

	DispatchSpawn( pent )

	pent.SetOwnerEntity( self )
	DispatchActivate( pent )

	ChildPostSpawn( pent )

	self.livechildren++# count self NPC

	if (!(m_spawnflags & SF_NPCMAKER_INF_CHILD))
	
		self.maxnumnpcs--

		if ( IsDepleted() )
		
			self.onallspawned.FireOutput( self, self )

			# Disable self forever.  Don't kill it because it still gets death notices
			SetThink( None )
			SetUse( None )
		
	


#-----------------------------------------------------------------------------
# Purpose: Find a place to spawn an npc within my radius.
#			Right now self function tries to place them on the perimeter of radius.
# Output : False if we couldn't find a spot!
#-----------------------------------------------------------------------------
bool CTemplateNPCMaker::PlaceNPCInRadius( CAI_BaseNPC *pNPC )

	Vector vPos

	if ( CAI_BaseNPC::FindSpotForNPCInRadius( &vPos, GetAbsOrigin(), pNPC, m_flRadius ) )
	
		pNPC.SetAbsOrigin( vPos )
		return True
	

	DevMsg("**Failed to place NPC in radius!\n")
	return False



#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::MakeMultipleNPCS( int nNPCs )

	bool bInRadius = ( m_iszDestinationGroup == None_STRING and m_flRadius > 0.1 )
	while ( nNPCs-- )
	
		if ( !bInRadius )
		
			MakeNPC()
		
		else
		
			MakeNPCInRadius()
		
	


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::InputSpawnMultiple( inputdata_t &inputdata )

	MakeMultipleNPCS( inputdata.value.Int() )


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::InputChangeDestinationGroup( inputdata_t &inputdata )

	m_iszDestinationGroup = inputdata.value.StringID()


#-----------------------------------------------------------------------------
#-----------------------------------------------------------------------------
void CTemplateNPCMaker::InputSetMinimumSpawnDistance( inputdata_t &inputdata )

	m_iMinSpawnDistance = inputdata.value.Int()

'''