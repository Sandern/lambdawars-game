from srcbase import Color
from vmath import Vector2D, Vector
from vgui import cursors, GetClientMode, surface, FontVertex_t, vgui_input, scheme
from vgui.baseminimap import BaseMinimap
from input import ButtonCode_t
from entities import C_HL2WarsPlayer, MouseTraceData, GetMapBoundaryList
from gameinterface import ConVarRef, engine
from sound import soundengine
from fow import FogOfWarMgr

from core.units import unitlist
from core.signals import Signal, firedping, unitspawned, unitremoved, minimapupdateunit, playerchangedownernumber

from profiler import profile

# FOW
sv_fogofwar = ConVarRef('sv_fogofwar')

# Need to grab these from somewhere else
FOW_SIZE = 32768
FOW_TILESIZE = 64

minimapflash = Signal(providing_args=['ent', 'duration'])

class BaseHudMinimap(BaseMinimap):
    def __init__(self, parent):
        # Vars
        self.backgroundtextureid = -1
        self.maptextureid = -1    
    
        super().__init__(GetClientMode().GetViewport(), "BaseHudMinimap")
    
        self.SetProportional( True )
        self.SetPaintBackgroundEnabled( False )
        self.SetKeyBoardInputEnabled( False )
        self.SetMouseInputEnabled( True )
        
        self.SetZPos(-1)

        self.mapobjects = []
        self.mapunits = []
        self.pings = [] # Contains lists of the format: [starttime, x, y, color]

        self.nextupdatetime = gpGlobals.curtime
        
        self.directmove = False
            
        firedping.connect(self.OnPing)
        minimapflash.connect(self.OnMinimapFlash)
        unitspawned.connect(self.OnUnitSpawned)
        unitremoved.connect(self.OnUnitRemoved)
        minimapupdateunit.connect(self.OnMinimapUpdateUnit)
        playerchangedownernumber.connect(self.OnPlayerChangedOwnernumber)
        
        # Minimap might be created after the first units are spawned
        # Parse the existing list of units
        self.FullUnitUpdate()
        
    def UpdateOnDelete(self):
        firedping.disconnect(self.OnPing)
        minimapflash.disconnect(self.OnMinimapFlash)
        unitspawned.disconnect(self.OnUnitSpawned)
        unitremoved.disconnect(self.OnUnitRemoved)
        minimapupdateunit.disconnect(self.OnMinimapUpdateUnit)
        playerchangedownernumber.disconnect(self.OnPlayerChangedOwnernumber)
        
    def ApplySchemeSettings(self, scheme_obj):
        super().ApplySchemeSettings(scheme_obj)
        
        self.SetBgColor(Color(0,0,0,128))
        self.SetPaintBackgroundEnabled(False)
        
        if self.backgroundtexture:
            # load background texture
            self.backgroundtextureid = surface().CreateNewTextureID()
            surface().DrawSetTextureFile(self.backgroundtextureid, self.backgroundtexture, True, False)
            
        # load fow texture
        self.fowtextureid = surface().CreateNewTextureID()
        surface().DrawSetTextureFile(self.fowtextureid, 'fow/fow' , True, False)
        self.fowsize = FogOfWarMgr().GetGridSize() #FOW_SIZE / FOW_TILESIZE
        self.fowsizeworldhalf = (FogOfWarMgr().GetGridSize() * FogOfWarMgr().GetTileSize()) / 2.0
        
    def PerformLayout(self):
        super().PerformLayout()

        # Setup points
        self.drawpoints = [
            FontVertex_t(self.MapToPanel(Vector2D(0,0) ), Vector2D(0,0)),
            FontVertex_t(self.MapToPanel(Vector2D(self.OVERVIEW_MAP_SIZE-1,0) ), Vector2D(1,0)),
            FontVertex_t(self.MapToPanel(Vector2D(self.OVERVIEW_MAP_SIZE-1,self.OVERVIEW_MAP_SIZE-1)), Vector2D(1,1)),
            FontVertex_t(self.MapToPanel(Vector2D(0,self.OVERVIEW_MAP_SIZE-1)), Vector2D(0,1))        
        ]
    
    #@profile('Minimap.OnThink')
    def OnThink(self):    
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        self.viewangle = player.EyeAngles().y    
        
        if self.directmove:
            self.UpdateToMinimapPosition()
            
        self.UpdateCursor()
    
    def Reset(self):
        pass
        
    def SetMap(self, mapname):   
        super().SetMap(mapname)
        
        if self.minimap_material == None:
            return
            
        # TODO: release old texture ?    
        self.maptextureid = surface().CreateNewTextureID()     
            
        surface().DrawSetTextureFile( self.maptextureid, self.minimap_material, True, False)
        wide, tall = surface().DrawGetTextureSize( self.maptextureid )

        if wide != tall:
            PrintWarning( "Error! hud_old_minimap.HudMinimap.SetMap: map image must be a square.\n" )
            self.maptextureid = -1
            return
            
    def FullUnitUpdate(self):
        for owner, l in unitlist.items():
            for unit in l:
                if not unit.handlesactive:
                    continue
                self.OnUnitSpawned(unit)
            
    def OnUnitSpawned(self, unit, **kwargs):
        info = unit.unitinfo
        if not info.minimaphalfwide or not unit.ShowOnMinimap():
            return
        self.InsertEntityObject(unit, info.minimapicon, info.minimaphalfwide, info.minimaphalftall, True, True, info.minimaplayer)
        
    def OnUnitRemoved(self, unit, **kwargs):
        self.RemoveEntityObject(unit) # Noop in case the unit is not on the minimap
        
    def OnMinimapUpdateUnit(self, unit, **kwargs):
        self.OnUnitRemoved(unit)
        self.OnUnitSpawned(unit)
        
    def OnPlayerChangedOwnernumber(self, player, oldownernumber, **kwargs):
        self.RemoveAllEntityObjects(unitsonly=True)
        self.FullUnitUpdate()
        
    def OnPing(self, pos, color, **kwargs):
        self.Ping(color, pos=pos)
        
    def OnMinimapFlash(self, ent, duration, **kwargs):
        self.FlashEntity(ent, duration)
            
    def Ping(self, color, pos=None, mappos=None):
        if not mappos:
            mappos = self.MapToPanel(self.WorldToMap(pos))
        self.pings.append([
            gpGlobals.curtime,
            int(mappos.x),
            int(mappos.y),
            color
        ])
        
        soundengine.EmitAmbientSound('ambient/alarms/warningbell1.wav', 0.8)
   
    # Paint methods
    @profile('Minimap.Paint')
    def Paint(self):
        self.DrawMapTexture(self.drawpoints)
        self.DrawFOW(self.drawpoints)
        self.DrawEntityObjects()
        self.DrawPlayerView()
        self.DrawMapBoundaries()
        self.DrawPings()
        
        super().Paint()
        
    def DrawBackground(self):
        """ Draw that thing behind the minimap """
        if self.backgroundtextureid < 0:
            return

        surface().DrawSetColor(255,255,255, 255)
        surface().DrawSetTexture(self.backgroundtextureid)
        surface().DrawTexturedRect(0, 0, self.GetWide(), self.GetTall())
        
    def DrawPings(self):
        scale = scheme().GetProportionalScaledValueEx(self.GetScheme(), 16)
        for i in range(len(self.pings)-1, -1, -1):
            p = self.pings[i]
            alive = gpGlobals.curtime - p[0]
            if alive > 1.8:
                del self.pings[i]
                continue
            surface().DrawSetColor(p[3][0], p[3][1], p[3][2], 220)
            surface().DrawOutlinedCircle(p[1], p[2], int(alive * scale), 128)
            
    def DrawFOW(self, points):
        if not sv_fogofwar.GetBool():
            return

        if self.fowtextureid < 0:
            return

        surface().DrawSetTexture(self.fowtextureid)
        surface().DrawSetColor(255, 255, 255, 255)

        points_coords = [
            # upper left 0,0
            FontVertex_t( points[0].m_Position, Vector2D( 
                    ((self.MapToWorld( Vector2D( 0,0 ) ).x + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize, 
                    ((self.MapToWorld( Vector2D( 0,0 ) ).y + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize
                    ) ),

            # UPPER RIGHT 1023, 0
            FontVertex_t( points[1].m_Position, Vector2D(  
                    ((self.MapToWorld( Vector2D(self.OVERVIEW_MAP_SIZE-1,0) ).x + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize,
                    ((self.MapToWorld( Vector2D(self.OVERVIEW_MAP_SIZE-1,0) ).y + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize 
                    ) ),

            # LOWER LEFT 1023, 1
            FontVertex_t( points[2].m_Position, Vector2D(  
                    ((self.MapToWorld( Vector2D(self.OVERVIEW_MAP_SIZE-1,self.OVERVIEW_MAP_SIZE-1) ).x + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize,
                    ((self.MapToWorld( Vector2D(self.OVERVIEW_MAP_SIZE-1,self.OVERVIEW_MAP_SIZE-1) ).y + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize 
                    ) ), 

            FontVertex_t( points[3].m_Position, Vector2D(  
                    ((self.MapToWorld( Vector2D(0,self.OVERVIEW_MAP_SIZE-1) ).x + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize,
                    ((self.MapToWorld( Vector2D(0,self.OVERVIEW_MAP_SIZE-1) ).y + self.fowsizeworldhalf ) / FOW_TILESIZE) / self.fowsize 
                    ) ), 
        ]

        surface().DrawTexturedPolygon( points_coords )

    def DrawMapTexture(self, points):
        """ Draw the map """
        if self.maptextureid < 0:
            self.DrawBackground()
            return

        alpha = 255
        
        surface().DrawSetColor(255,255,255, alpha)
        surface().DrawSetTexture(self.maptextureid)
        surface().DrawTexturedPolygon(points)  

    # def DrawPlayerView(self):
        # player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        # if player == None:
            # return
            
        # point2D1 = Vector2D()
        # point2D2 = Vector2D()
        # point2D3 = Vector2D()
        # point2D4 = Vector2D()
        # tr = trace_t()
        
        # origin = player.GetAbsOrigin()
        
        # # Find the two lowest points
        # forward1 = UTIL_GetMouseAim(player, 0, 0)
        # UTIL_TraceLine(player.Weapon_ShootPosition(),player.Weapon_ShootPosition() + (forward1 *  8192), MASK_SOLID, player, 0,tr)
        # point1 = tr.endpos
        
        # forward2 = UTIL_GetMouseAim(player, ScreenWidth(), 0)
        # UTIL_TraceLine(player.Weapon_ShootPosition(),player.Weapon_ShootPosition() + (forward2 *  8192), MASK_SOLID, player, 0,tr)
        # point2 = tr.endpos

        # if (player.Weapon_ShootPosition() - point1).Length() > (player.Weapon_ShootPosition() - point2).Length():
            # point2D1 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward1 * (player.Weapon_ShootPosition() - point1).Length() ) )
            # point2D2 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward2 * (player.Weapon_ShootPosition() - point1).Length() ) )
        # else:
            # point2D1 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward1 * (player.Weapon_ShootPosition() - point2).Length() ) )
            # point2D2 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward2 * (player.Weapon_ShootPosition() - point2).Length() ) )

        # # Find the two highest points
        # forward1 = UTIL_GetMouseAim(player, ScreenWidth(), ScreenHeight() )
        # UTIL_TraceLine(player.Weapon_ShootPosition(),player.Weapon_ShootPosition() + (forward1 *  8192), MASK_SOLID, player, 0,tr)
        # point1 = tr.endpos

        # forward2 = UTIL_GetMouseAim(player, 0, ScreenHeight()  )
        # UTIL_TraceLine(player.Weapon_ShootPosition(),player.Weapon_ShootPosition() + (forward2 *  8192), MASK_SOLID, player, 0,tr)
        # point2 = tr.endpos

        # if (player.Weapon_ShootPosition() - point1).Length() > (player.Weapon_ShootPosition() - point2).Length():
            # point2D3 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward1 * (player.Weapon_ShootPosition() - point1).Length() ) )
            # point2D4 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward2 * (player.Weapon_ShootPosition() - point1).Length() ) )
        # else:
            # point2D3 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward1 * (player.Weapon_ShootPosition() - point2).Length() ) )
            # point2D4 = self.MapToPanel( self.WorldToMap( player.Weapon_ShootPosition() + forward2 * (player.Weapon_ShootPosition() - point2).Length() ) )

        # # Draw them
        # surface().DrawSetColor( Color(255, 0, 0, 255) )
        # surface().DrawLine( int(point2D1.x), int(point2D1.y), int(point2D2.x), int(point2D2.y) )
        # surface().DrawLine( int(point2D2.x), int(point2D2.y), int(point2D3.x), int(point2D3.y) )
        # surface().DrawLine( int(point2D3.x), int(point2D3.y), int(point2D4.x), int(point2D4.y) )
        # surface().DrawLine( int(point2D4.x), int(point2D4.y), int(point2D1.x), int(point2D1.y) )
        
    def DrawMapBoundaries(self):
        surface().DrawSetColor(0, 0, 255, 200)
        
        boundary = GetMapBoundaryList()
        while boundary:
            point1 = Vector()
            point2 = Vector()
            point3 = Vector()
            point4 = Vector()
            mins = Vector()
            maxs = Vector()
            boundary.CollisionProp().WorldSpaceAABB(mins, maxs)

            point1[0] = mins[0]
            point1[1] = mins[1]
            point2[0] = mins[0]
            point2[1] = maxs[1]
            point3[0] = maxs[0]
            point3[1] = maxs[1]
            point4[0] = maxs[0]
            point4[1] = mins[1]

            point2d1 = self.MapToPanel(self.WorldToMap(point1))
            point2d2 = self.MapToPanel(self.WorldToMap(point2))
            point2d3 = self.MapToPanel(self.WorldToMap(point3))
            point2d4 = self.MapToPanel(self.WorldToMap(point4))

            surface().DrawLine(int(point2d1.x), int(point2d1.y), 
                int(point2d2.x), int(point2d2.y))
            surface().DrawLine(int(point2d2.x), int(point2d2.y),
                int(point2d3.x), int(point2d3.y))
            surface().DrawLine(int(point2d3.x), int(point2d3.y), 
                int(point2d4.x), int(point2d4.y))
            surface().DrawLine(int(point2d4.x), int(point2d4.y), 
                int(point2d1.x), int(point2d1.y))
                
            boundary = boundary.GetNext()
        
    def GetMouseDataAt(self):
        from core.ents import FuncMapBoundary # FIXME
        
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        
        # Convert cursor to world
        x, y = vgui_input().GetCursorPos()
        x, y = self.ScreenToLocal(x, y)
        click = Vector2D(x, y)        
        world2d = self.MapToWorld(self.PanelToMap(click))
        start = Vector()
        start[0] = world2d[0]
        start[1] = world2d[1]
        start.z = player.GetAbsOrigin().z
        
        mins = player.GetPlayerMins()
        maxs = player.GetPlayerMaxs()
        
        # Get z at map boundary minimum height
        FuncMapBoundary.SnapToNearestBoundary(start, mins, maxs, False)
        
        # Get z at map boundary maximum height
        camoffset = Vector(start)
        FuncMapBoundary.SnapToNearestBoundary(camoffset, mins, maxs, True)
        camoffset -= start
        
        # Get mouse data
        mousedata = MouseTraceData()
        player.CalculateMouseData(Vector(0, 0, -1), start, camoffset, mousedata)
        return mousedata
    
    def OnMousePressed(self, code):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return

        if code == ButtonCode_t.MOUSE_LEFT:
            vgui_input().SetMouseCaptureEx(self.GetVPanel(), code) 
            
            if not player.GetSingleActiveAbility():
                if vgui_input().IsKeyDown(ButtonCode_t.KEY_LCONTROL) or vgui_input().IsKeyDown(ButtonCode_t.KEY_RCONTROL):
                    x, y = vgui_input().GetCursorPos()
                    x, y = self.ScreenToLocal(x, y)
                    click = Vector2D(x, y)        
                    world2d = self.MapToWorld(self.PanelToMap(click))
                    engine.ServerCommand('wars_ping %f %f %f' % (world2d.x, world2d.y, 0.0))
                else:
                    self.directmove = True
                    self.UpdateToMinimapPosition()
            else:
                player.MinimapClick(self.GetMouseDataAt())
            
        elif code == ButtonCode_t.MOUSE_RIGHT:
            if player.GetSingleActiveAbility():
                # When having an active ability, the right mouse will act as moving on the minimap
                self.directmove = True
                self.UpdateToMinimapPosition()
            vgui_input().SetMouseCaptureEx(self.GetVPanel(), code)

    def OnMouseReleased(self, code):
        self.UpdateCursor()
    
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
        
        vgui_input().SetMouseCapture( 0 )
        if code == ButtonCode_t.MOUSE_LEFT:
            if not player.GetSingleActiveAbility():
                self.directmove = False
                player.StopDirectMove()
        elif code == ButtonCode_t.MOUSE_RIGHT:
            if player.GetSingleActiveAbility():
                # When having an active ability, the right mouse will act as moving on the minimap
                self.directmove = False
                player.StopDirectMove()
            else:
                player.SimulateOrderUnits(self.GetMouseDataAt())
                
    def OnCursorMoved(self, x, y):
        super().OnCursorMoved(x, y)
        
        self.UpdateCursor()
            
    def UpdateCursor(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        if player.GetSingleActiveAbility():
            self.SetCursor(cursors.GetCursor("resource/arrows/ability_cursor.ani"))
        else:
            self.SetCursor(cursors.GetCursor("resource/arrows/default_cursor.cur"))
                
    def UpdateToMinimapPosition(self):
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        x, y = vgui_input().GetCursorPos()
        x, y = self.ScreenToLocal(x, y)
        click = Vector2D(x, y)        
        world2d = self.MapToWorld(self.PanelToMap(click))
        destination = Vector()
        destination[0] = world2d[0]
        destination[1] = world2d[1]
        destination[2] = player.GetAbsOrigin().z    
        
        player.SnapCameraTo(destination)
        
    backgroundtexture = 'VGUI/radar'
    