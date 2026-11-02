"""Client-side unit team-color glow manager.

Culls expensive studio outline glows for FOW / off-screen units, and when many
units are on screen swaps occluded studio glows for cheap screen-space markers.
"""
from srcbase import Color, MASK_SOLID_BRUSHONLY, COLLISION_GROUP_NONE
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from gameinterface import ConVar, FCVAR_ARCHIVE
from utils import (GetVectorInScreenSpace, ScreenWidth, ScreenHeight, MainViewOrigin,
                   UTIL_TraceLine, trace_t)
from materials import glowobjectmanager
from core.dispatch import receiver
from core.signals import postlevelshutdown

cl_unit_glow_max_studio = ConVar(
    'cl_unit_glow_max_studio', '40', FCVAR_ARCHIVE,
    'Max on-screen units that keep studio outline glow; above this, occluded units use cheap sprites.')
cl_unit_glow_cull = ConVar(
    'cl_unit_glow_cull', '1', FCVAR_ARCHIVE,
    'Cull unit team-color glow for fog-of-war and off-screen units.')
cl_unit_glow_update = ConVar(
    'cl_unit_glow_update', '0.1', FCVAR_ARCHIVE,
    'Seconds between unit glow visibility updates.')

GLOW_MODE_NONE = 0
GLOW_MODE_STUDIO = 1
GLOW_MODE_SPRITE = 2

_wanted = set()
_sprite_units = []
_trace = trace_t()


def _UnitAlive(unit):
    return bool(unit) and unit.IsAlive() and not unit.IsDormant()


def _ClearStudioGlow(unit):
    if getattr(unit, 'glowidx', None) is not None:
        glowobjectmanager.UnregisterGlowObject(unit.glowidx)
        unit.glowidx = None


def _SetStudioGlow(unit, enable):
    _ClearStudioGlow(unit)
    if enable:
        unit.glowidx = glowobjectmanager.RegisterGlowObject(
            unit, unit.GetTeamColor(), 0.7, True, True, -1)


def _IsOnScreen(unit):
    origin = unit.WorldSpaceCenter()
    success, x, y = GetVectorInScreenSpace(origin)
    if not success:
        return False
    margin = 48
    return (-margin <= x <= ScreenWidth() + margin and
            -margin <= y <= ScreenHeight() + margin)


def _IsOccluded(unit):
    origin = unit.WorldSpaceCenter()
    UTIL_TraceLine(MainViewOrigin(), origin, MASK_SOLID_BRUSHONLY, unit, COLLISION_GROUP_NONE, _trace)
    return _trace.fraction < 1.0


def _ApplyMode(unit, mode):
    prev = getattr(unit, '_unitglow_mode', GLOW_MODE_NONE)
    if prev == mode:
        if mode == GLOW_MODE_STUDIO and unit.glowidx is not None:
            glowobjectmanager.SetColor(unit.glowidx, unit.GetTeamColor())
        return

    if prev == GLOW_MODE_STUDIO:
        _ClearStudioGlow(unit)

    unit._unitglow_mode = mode

    if mode == GLOW_MODE_STUDIO:
        _SetStudioGlow(unit, True)


def SetWanted(unit, wanted):
    """Register or unregister a unit that wants team-color glow."""
    handle = unit.GetHandle()
    if wanted:
        _wanted.add(handle)
        unit._unitglow_wanted = True
        _EnsureTick()
        # Provisional studio glow until the next cull tick (avoids O(n^2) on mass spawn).
        if (not cl_unit_glow_cull.GetBool() or
                len(_wanted) <= cl_unit_glow_max_studio.GetInt()):
            _ApplyMode(unit, GLOW_MODE_STUDIO)
    else:
        _wanted.discard(handle)
        unit._unitglow_wanted = False
        _ApplyMode(unit, GLOW_MODE_NONE)
        if unit in _sprite_units:
            _sprite_units.remove(unit)
        if not _wanted and IsTickMethodRegistered(UpdateGlowVisibility):
            UnregisterTickMethod(UpdateGlowVisibility)


def _EnsureTick():
    _EnsureHud()
    if not IsTickMethodRegistered(UpdateGlowVisibility):
        interval = max(0.05, cl_unit_glow_update.GetFloat())
        RegisterTickMethod(UpdateGlowVisibility, interval)


def UpdateGlowVisibility():
    global _sprite_units

    if not cl_unit_glow_cull.GetBool():
        # Pass-through: always studio glow when cull is disabled.
        for handle in list(_wanted):
            unit = handle
            if not _UnitAlive(unit) or not getattr(unit, '_unitglow_wanted', False):
                _wanted.discard(handle)
                if unit:
                    _ApplyMode(unit, GLOW_MODE_NONE)
                continue
            _ApplyMode(unit, GLOW_MODE_STUDIO)
        _sprite_units = []
        return

    candidates = []
    for handle in list(_wanted):
        unit = handle
        if not _UnitAlive(unit) or not getattr(unit, '_unitglow_wanted', False):
            _wanted.discard(handle)
            if unit:
                _ApplyMode(unit, GLOW_MODE_NONE)
            continue

        try:
            in_fow = unit.IsInFOW()
        except Exception:
            in_fow = False

        if in_fow or not _IsOnScreen(unit):
            _ApplyMode(unit, GLOW_MODE_NONE)
            continue

        candidates.append(unit)

    max_studio = max(0, cl_unit_glow_max_studio.GetInt())
    use_sprites = len(candidates) > max_studio
    sprites = []

    if use_sprites:
        for unit in candidates:
            if _IsOccluded(unit):
                _ApplyMode(unit, GLOW_MODE_SPRITE)
                sprites.append(unit)
            else:
                _ApplyMode(unit, GLOW_MODE_NONE)
    else:
        for unit in candidates:
            _ApplyMode(unit, GLOW_MODE_STUDIO)

    _sprite_units = sprites

    if not _wanted and IsTickMethodRegistered(UpdateGlowVisibility):
        UnregisterTickMethod(UpdateGlowVisibility)


_hud_helper = None


def _EnsureHud():
    """Create silhouette HUD after the client viewport exists (units load early)."""
    global _hud_helper
    if _hud_helper is not None:
        return

    try:
        from vgui import surface, GetClientMode, CHudElement, CHudElementHelper
        from vgui.controls import Panel

        if not GetClientMode() or not GetClientMode().GetViewport():
            return

        class HudUnitGlowSilhouettes(CHudElement, Panel):
            """Cheap through-wall team markers used when studio glow is over budget."""

            def __init__(self):
                CHudElement.__init__(self, 'HudUnitGlowSilhouettes')
                Panel.__init__(self, GetClientMode().GetViewport(), 'HudUnitGlowSilhouettes')
                self.SetPaintEnabled(True)
                self.SetKeyBoardInputEnabled(False)
                self.SetMouseInputEnabled(False)
                self.SetPaintBackgroundEnabled(False)

            def LevelInit(self):
                global _sprite_units
                _sprite_units = []

            def PerformLayout(self):
                super().PerformLayout()
                self.SetSize(ScreenWidth(), ScreenHeight())

            def Paint(self):
                if not _sprite_units:
                    return

                s = surface()
                for unit in _sprite_units:
                    if not _UnitAlive(unit):
                        continue

                    origin = unit.WorldSpaceCenter()
                    success, x, y = GetVectorInScreenSpace(origin)
                    if not success:
                        continue

                    color = unit.GetTeamColor()
                    r = int(color.x * 255)
                    g = int(color.y * 255)
                    b = int(color.z * 255)

                    # Soft outer marker + brighter core (through-wall silhouette).
                    radius = max(4, int(unit.CollisionProp().BoundingRadius2D() * 0.08))
                    radius = min(radius, 14)
                    cx, cy = int(x), int(y)

                    s.DrawSetColor(Color(r, g, b, 70))
                    s.DrawFilledRect(cx - radius, cy - radius, cx + radius, cy + radius)
                    s.DrawSetColor(Color(r, g, b, 200))
                    core = max(2, radius // 2)
                    s.DrawFilledRect(cx - core, cy - core, cx + core, cy + core)

        _hud_helper = CHudElementHelper(HudUnitGlowSilhouettes())
    except Exception:
        # Viewport may not exist yet; retry on the next glow update.
        _hud_helper = None


@receiver(postlevelshutdown)
def _OnLevelShutdown(**kwargs):
    global _sprite_units
    if IsTickMethodRegistered(UpdateGlowVisibility):
        UnregisterTickMethod(UpdateGlowVisibility)
    for handle in list(_wanted):
        unit = handle
        if unit:
            _ApplyMode(unit, GLOW_MODE_NONE)
        _wanted.discard(handle)
    _sprite_units = []
