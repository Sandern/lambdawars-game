from vmath import Vector, QAngle
import random
if isserver:
    from entities import CreateEntityByName, DispatchSpawn
from gameinterface import engine
import ndebugoverlay

# Temp
DEFLIGHT_ENABLED = ( 1 << 0 )
DEFLIGHT_SHADOW_ENABLED = ( 1 << 1 )
DEFLIGHT_COOKIE_ENABLED = ( 1 << 2 )
DEFLIGHT_VOLUMETRICS_ENABLED = ( 1 << 3 )
DEFLIGHT_LIGHTSTYLE_ENABLED = ( 1 << 4 )

DEFLIGHT_DIRTY_XFORMS = ( 1 << 6 )
DEFLIGHT_DIRTY_RENDERMESH = ( 1 << 7 )

def CreateDungeonLight(origin, yaw=0, pitch=70):
    angles = QAngle(pitch, yaw, 0)
    
    # Assume sp for now. In the other case we should make a new light entity that support both modes
    try:
        deferredlighting = bool(int(engine.GetClientConVarValue(1, 'deferred_lighting_enabled')))
    except:
        deferredlighting = False

    if deferredlighting:
        pitch = 50
    
        light = CreateEntityByName('light_deferred')
        
        light.SetName('dungeonlight')
        
        light.KeyValue('diffuse', '171 67 37 512')
        light.KeyValue('ambient', '0 0 0 0')
        light.KeyValue('radius', '1024')
        light.KeyValue('power', '1.0')
        light.KeyValue('spot_cone_inner', '10.0')
        light.KeyValue('spot_cone_outer', '100.0')
        light.KeyValue('vis_dist', '1024')
        light.KeyValue('vis_range', '512')
        light.KeyValue('shadow_dist', '1024')
        light.KeyValue('shadow_range', '512')
        light.KeyValue('light_type', '1') # 0 (Point) or 1 (Spot)
        light.KeyValue('cookietex', '0')
        light.KeyValue('style_amt', str(random.uniform(0.05, 0.25)))
        light.KeyValue('style_speed', '35')
        light.KeyValue('style_smooth', str(random.uniform(0.1, 0.3)))
        light.KeyValue('style_random', str(random.random()))
        light.KeyValue('style_seed', '-1')

        light.KeyValue('spawnFlags', str(DEFLIGHT_ENABLED|DEFLIGHT_SHADOW_ENABLED|DEFLIGHT_LIGHTSTYLE_ENABLED|DEFLIGHT_VOLUMETRICS_ENABLED))

        light.KeyValue('ambient_low', '0')
        light.KeyValue('ambient_high', '0')
        
        light.SetAbsOrigin(origin)
        light.SetAbsAngles(angles)
        
        DispatchSpawn(light)
        light.Activate()
        
        return [light]
    else:
        # Create projected texture
        pt = CreateEntityByName('env_projectedtexture')
        
        pt.KeyValue('brightnessscale', '80')
        pt.KeyValue('cameraspace', '0')
        pt.KeyValue('colortransitiontime', '0.5')
        pt.KeyValue('enableshadows', '1')
        pt.KeyValue('farz', '192')
        #pt.KeyValue('lightcolor', '234 219 166 200')
        pt.KeyValue('lightcolor', '203 132 67 200')
        pt.KeyValue('lightfov', '80')
        pt.KeyValue('lightworld', '1')
        pt.KeyValue('nearz', '4.0')
        pt.KeyValue('shadowquality', '1')
        pt.KeyValue('simpleprojection', '0')
        pt.KeyValue('spawnflags', '1')
        pt.KeyValue('texturename', 'effects/flashlight001')
        
        pt.SetAbsOrigin(origin)
        pt.SetAbsAngles(angles)
        
        DispatchSpawn(pt)
        pt.Activate()
        
        # Create sprite
        sprite = CreateEntityByName('env_sprite')
        
        sprite.KeyValue('framerate', '6')
        sprite.KeyValue('brightnessscale', '10.0')
        sprite.KeyValue('GlowProxySize', '16')
        sprite.KeyValue('HDRColorScale', '1.0')
        sprite.KeyValue('model', 'materials/sprites/light_glow03.vmt')
        sprite.KeyValue('renderamt', '255')
        sprite.KeyValue('rendercolor', '199 216 213')
        sprite.KeyValue('rendermode', '9')
        sprite.KeyValue('scale', '.5')

        sprite.SetAbsOrigin(origin)
        
        DispatchSpawn(sprite)
        sprite.Activate()
        
        return [pt, sprite]
    