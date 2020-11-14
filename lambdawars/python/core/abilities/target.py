from srcbase import Color, EF_NOSHADOW
from vmath import Vector, vec3_angle, vec3_origin, matrix3x4_t, AngleMatrix, VectorRotate
from .base import StopInit, AbilityBase
from utils import UTIL_CalculateDirection
from gameinterface import engine
from entities import Activity
from particles import *
from fields import BooleanField, FloatField

if isclient:
    from vgui import cursors
    from entities import CBaseAnimating

if __debug__:
    import mem_debug


class AbilityTarget(AbilityBase):
    """ Base class for abilities that require the player to target an entity or position.
    
        It releases mouse input on left mouse release. The ability is canceled if you right
        click before left clicking or when mouse input is lost.
        The default option is to operate on a single unit. Use AbilityTargetGroup if you want
        to operate on the complete player unit selection.
    """
    @classmethod           
    def Precache(info):
        super().Precache()
        
        for particleeffect in info.infoparticles:
            PrecacheParticleSystem(particleeffect)
                
    def Init(self):
        """ Initializes the ability. 
        
            Creates visuals, adds the ability to the players active ability list for
            mouse input and calls StartAbility.
        """
        if self.allowmultipleability:
            self.player.AddActiveAbility(self)
        else:
            self.player.SetSingleActiveAbility(self)
        
        # Can't start this type of ability while having left pressed
        if self.player.IsLeftPressed():
            self.player.ClearMouse()
        
        if not self.ischeat and self.requireunits:
            if not self.SelectUnits():
                self.Cancel(debugmsg='No units while ability requires selected units')
                raise StopInit
                
        if isclient:
            self.CreateVisuals()
                
        self.StartAbility()
                
        super().Init()
        
    def DebugPrint(self):
        return super().DebugPrint() + '\tunits: %s\n' % (str(self.units))
    
    def StartAbility(self): 
        """ Start/do the ability directly when the player activates the ability."""
        pass
        
    def ComputeUnitCost(self, unit):
        if self.targetpos == vec3_origin:
            return 0
        return (unit.GetAbsOrigin() - self.targetpos).Length2D()
        
    def SelectUnits(self): 
        return self.SelectSingleUnit()
    
    if isserver:
        def OnAllUnitsCleared(self):
            if self.cancelonunitscleared:
                self.Cancel(debugmsg='all units cleared')
                
    def GetTargetPos(self, mousedata):
        return mousedata.groundendpos if self.targetatgroundonly else mousedata.endpos
        
    # Mouse methods      
    def OnLeftMouseButtonPressed(self):
        """ Implements ability target left mouse pressed behavior. """
        assert(not self.stopped)
        
        self.leftpressedonce = True
        curmousedata = self.player.GetMouseData()
        if self.requirerotation:
            if not self.isrotating:
                self.mousedata = curmousedata
                self.rotatepoint = self.GetTargetPos(self.mousedata)
                if isclient:
                    self.CreateArrow()
                return True
            else:
                # Busy rotating, so mouse data is already stored.
                # Just want to know the rotation
                self.targetangle = UTIL_CalculateDirection(self.GetTargetPos(self.mousedata), self.GetTargetPos(curmousedata))
        else:
            self.mousedata = curmousedata

        self.player.ClearMouse() # Prevent the "released" mouse function to be called. Otherwise the units of the player are deselected.
        self.DoAbilityInternal()
        return True
        
    def OnLeftMouseButtonReleased(self):
        """ Implements ability target left mouse released behavior. """
        assert(not self.stopped)
        
        if not self.leftpressedonce:
            return
        # This can happen if you go into the main menu. Pressing the resume
        # button will send the pressed code to the main menu, and send the 
        # released code to the game.
        if not self.mousedata:
            return

        curmousedata = self.player.GetMouseData()
        targetpos = self.GetTargetPos(self.mousedata)
        curmousepos = self.GetTargetPos(curmousedata)
        dist = curmousepos.DistTo(targetpos)
        if dist < self.rotation_drag_tolerance:
            # Ability requires rotation, but the player didn't specified a direction yet
            # Give a moment to specify the direction
            self.isrotating = True
            return True
        
        # Directly dragged into the desired direction, so rotation is specified in one click
        self.targetangle = UTIL_CalculateDirection(targetpos, curmousepos)
        
        self.DoAbilityInternal()
        return True
        
    def DoAbilityInternal(self):
        # Copy the target position and angle
        self.targetpos = self.GetTargetPos(self.mousedata)
    
        # Try selecting units again, might have changed
        if not self.ischeat and self.requireunits:
            if not self.SelectUnits():
                self.Cancel(debugmsg='Unable to select units at point of ability execution')
                return
        
        # Cleanup
        self.cancelonmouselost = False
        self.ClearMouse()
        if isclient:
            self.DestroyArrow()
            if self.clearvisualsonmouselost:
                self.ClearVisuals()
            else:
                if self.cleartempmodonmouselost:
                    self.ClearTempModel()
        
        # Do the actual ability
        self.PlayActivateSound()
        self.DoAbility()
        
        # The client mouse interaction with this ability is done. 
        # Check to see if we should recast this ability (e.g. holding shift or hotkey)
        self.TestContinueAbility()
        
    def OnRightMouseButtonPressed(self):
        """ Returns True to prevent default right mouse pressed behavior. """
        return True    
 
    def OnRightMouseButtonReleased(self):
        """ Cancels the ability if cancelonrightrelease is True/ """
        if isserver and self.cancelonrightrelease:
            self.Cancel(debugmsg='right mouse button released')
        return True  
        
    def OnMouseLost(self):        
        """ Lost mouse input because something cleared it. """
        if isserver and self.cancelonmouselost:
            self.Cancel(debugmsg='mouse lost')
            
    def OnMinimapClick(self, mousedata):
        """ Called when left clicking the minimap. """
        self.mousedata = mousedata
        self.DoAbilityInternal()

    def OnPortraitClick(self, mousedata):
        """ Called on left clicking a unit portrait. """
        self.mousedata = mousedata
        self.DoAbilityInternal()

    # Methods for doing something
    if isserver:
        def DoAbility(self):
            """ Do the ability. In case requirerotation is True this is called on mouse release. 
                In case it does not require rotation this is called when the mouse is pressed. """
            PrintWarning('Ability %s is not implemented\n' % (self.info.name))
            self.Cancel(debugmsg='ability not implemented')   
    else:
        def DoAbility(self):
            # TODO: The client implementation is by default completed on do ability
            #self.Completed()
            pass
            
    def TransformOffset(self, offset, angles):
        mat = matrix3x4_t()
        AngleMatrix(angles, mat)
        rs = Vector()
        VectorRotate(offset, mat, rs)
        return rs
            
    # Visuals
    if isclient:
        def GetPreviewPosition(self, groundpos):
            return groundpos
            
        def PreCreateVisuals(self):
            """ Modify info models, make unique copy. """
            self.infomodels = list(self.infomodels)
        
        def CreateVisuals(self):
            """ Creates visuals using the infoprojtextures and infomodels dictionaries. """
            self.particleinstances = []
            
            self.PreCreateVisuals()
            
            self.cursor = cursors.GetCursor(self.cursoricon)
            
            data = self.player.GetMouseData()
            
            # Create projected textures and temp models
            targetpos = self.GetTargetPos(data)
            self.CreateTempModel(targetpos)
            self.CreateParticleEffects(targetpos)
                
        def CreateArrow(self):
            """ Creates an arrow for rotation. """
            # TODO: Reimplement using particle system
            #self.arrow = ProjectedTexture(
            #        'decals/arrow', 
            #        Vector(-8, -16, 0), 
            #        Vector(80, 16, 50), 
            #        self.rotatepoint,
            #    )
                
        def DestroyArrow(self):
            """ Clears the arrow used for rotation. """
            #if self.arrow:
            #    self.arrow.Shutdown()
            #    self.arrow = None
                
        def CreateTempModel(self, initpos):
            """ Creates a "temporary" model entity, client side.
                For ability preview purposes.

                Args:
                    initpos (Vector): Initial position.
            """
            self.infomodelsinst = []
            for m in self.infomodels:
                engine.LoadModel(m['modelname'])
                inst = CBaseAnimating()

                if __debug__:
                    mem_debug.CheckRefDebug(inst)

                inst.SetAbsOrigin(self.GetPreviewPosition(initpos)+m.get('offset', vec3_origin))
                inst.SetAbsAngles(m.get('angle', vec3_angle))
                inst.SetModelScale(m.get('scale', 1))
                #inst.ForcedMaterialOverride('effects/placeobject_preview')
                inst.AddEffects(EF_NOSHADOW)

                if inst.InitializeAsClientEntity(m['modelname'], False):
                    color = m.get('color', self.defaultrendercolor)
                    inst.SetRenderColor(color.r(), color.g(), color.b())
                    inst.SetRenderAlpha(color.a())
                    
                    if 'activity' in m:
                        act = Activity(inst.LookupActivity(m['activity']))
                        inst.SetCycle(0.0)
                        inst.ResetSequence(inst.SelectWeightedSequence(act))
                    
                    self.infomodelsinst.append(inst)
                    
        def CreateParticleEffects(self, initpos):
            for particleeffect in self.infoparticles:
                inst = CNewParticleEffect.Create(None, particleeffect)
                self.particleinstances.append(inst)
                self.UpdateParticleEffects(inst, initpos)
                
        def ClearParticleEffects(self):
            for inst in self.particleinstances:
                #inst.SetDormant(True)
                inst.StopEmission(False, True, False, True)
            self.particleinstances = []
                
        def UpdateParticleEffects(self, inst, targetpos):
            inst.SetControlPoint(0, targetpos + self.particleoffset)
            inst.SetControlPoint(1, self.unit.GetTeamColor() if self.unit else Vector(0, 1, 0))
            inst.SetControlPoint(2, Vector(self.particleradius, 0, 0))
                
        def ClearTempModel(self):
            """ Clears all active preview models. """
            for m in self.infomodelsinst:
                if not m:
                    continue
                m.Remove()
            self.infomodelsinst = []
                
        def ClearVisuals(self):
            """ Responsible for clearing visuals created for previewing the ability.

                Think of models and particles.
            """
            self.ClearTempModel()
            self.ClearParticleEffects()
            self.DestroyArrow()
                
        def Frame(self):
            if self.stopupdating:
                return
                
            data = self.player.GetMouseData()
            if self.requirerotation and self.rotatepoint:
                angle = UTIL_CalculateDirection(self.rotatepoint, self.GetTargetPos(data))
                origin = self.rotatepoint
            else:
                angle = vec3_angle
                origin = self.GetTargetPos(data)
            self.targetangle = angle
                
            for i, m in enumerate(self.infomodelsinst):
                if not m:
                    continue
                info = self.infomodels[i]
                m.SetAbsOrigin(self.GetPreviewPosition(origin)+self.TransformOffset(info.get('offset', vec3_origin), angle))  
                m.SetAbsAngles(info.get('angle', vec3_angle)+angle)
                
            for inst in self.particleinstances:
                self.UpdateParticleEffects(inst, origin)
                
            if self.arrow:
                self.arrow.Update(origin, angle)
                
        def Cleanup(self):
            super().Cleanup()
            
            # Ensure all visuals are cleared
            self.ClearVisuals()
            
        def GetCursor(self):
            return self.cursor

        cursor = None
        cursoricon = 'resource/arrows/ability_cursor.ani'
        defaultrendercolor = Color(255, 255, 255, 255)
        stopupdating = False
        arrow = None
        infomodelsinst = []
        particleinstances = []

        # List of dictionaries describing projected textures
        # Keys:
        # texture
        # offset
        # mins
        # maxs
        infoprojtextures = []
        
        # List of dictionaries describing temp models
        # Keys:
        # modelname
        # offset
        # rendercolor
        infomodels = []
        
    rotatepoint = None
    isrotating = False
    mousedata = None
    leftpressedonce = False
        
    #: List of particle effects created, with the first control point set to the mouse position
    infoparticles = []
    #: Radius of particle (if used)
    particleradius = 512.0
    #: Particle offset position from target ability position
    particleoffset = vec3_origin
        
    # Target position and angle when doing the ability
    targetpos = vec3_origin
    targetangle = vec3_angle
    
    #: Default behavior of this ability is to require selected units (except if executed as a cheat).
    requireunits = True
    #: Whether or not to cancel the ability when all units are cleared
    cancelonunitscleared = True

    # Mouse related settings
    #: Whether this ability requires rotation when placing
    #: If not the ability will directly be executed on left mouse pressed
    #: Otherwise it will give the player a moment to rotate around the target location.
    requirerotation = BooleanField(value=False)

    #: Drag distance at which you specify the rotation of a building in one click (press, hold and drag, release).
    rotation_drag_tolerance = FloatField(value=48.0)
    
    #: Ignore tracing with props and entities (mainly needed by buildings).
    targetatgroundonly = BooleanField(value=False)
    
    #: If True this ability can receive mouse input at the same time with other active abilities.
    #: If False it will clear all active abilities of the player (triggering OnMouseLost for those abilities) and
    #: set this ability as active for the player.
    allowmultipleability = BooleanField(value=False)
    
    #: If True the ability will be canceled when it loses mouse input.
    cancelonmouselost = True
    
    #: If True the ability will be canceled on right mouse button release
    cancelonrightrelease = True
    
    #: Calls ClearVisuals on mouse lost if True
    clearvisualsonmouselost = True
    
    #: Calls ClearTempModel on mouse lost if True
    cleartempmodonmouselost = False
    
    # By default, test for auto restart ability
    allowcontinueability = False

class AbilityTargetGroup(AbilityTarget):
    """ Same as AbilityTarget, except operates on the whole player unit selection. """
    def SelectUnits(self): 
        return self.SelectGroupUnits()
        
    # Test auto restart ability is undesired for groups usually
    allowcontinueability = False
