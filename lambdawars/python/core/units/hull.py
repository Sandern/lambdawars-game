from vmath import Vector, vec3_origin

# Format for each type: mins maxs smallmins smallmaxs
hull = {
    None : (vec3_origin, vec3_origin, vec3_origin, vec3_origin),
    'HULL_HUMAN' : ( Vector(-13,-13,   0), Vector(13, 13, 72), 
                     Vector(-8,-8,   0), Vector( 8,  8, 72) ), # Combine, Stalker, Zombie...
    'HULL_SMALL_CENTERED' : ( Vector(-20,-20, -20), Vector(20, 20, 20), 
                              Vector(-12,-12,-12), Vector(12, 12, 12) ), # Scanner
    'HULL_WIDE_HUMAN' : ( Vector(-15,-15,   0), Vector(15, 15, 72), 
                          Vector(-10,-10, 0), Vector(10, 10, 72) ), # Vortigaunt
    'HULL_TINY' : ( Vector(-12,-12,   0), Vector(12, 12, 24), 
                    Vector(-12,-12, 0), Vector(12, 12, 24) ), # Headcrab
    'HULL_WIDE_SHORT' : ( Vector(-35,-35,   0), Vector(35, 35, 32), 
                          Vector(-20,-20, 0), Vector(20, 20, 32) ), # Bullsquid
    'HULL_MEDIUM' : ( Vector(-16,-16,   0), Vector(16, 16, 64), 
                      Vector(-8,-8, 0), Vector(8, 8, 64) ), # Cremator
    'HULL_TINY_CENTERED' : ( Vector(-8,	-8,  -4), Vector(8, 8,  4), 
                             Vector(-8,-8, -4), Vector( 8, 8, 4) ), # Manhack 
    'HULL_LARGE' : ( Vector(-40,-40,   0), Vector(40, 40, 100), 
                     Vector(-40,-40, 0), Vector(40, 40, 100) ), # Antlion Guard
    'HULL_LARGE_CENTERED' : ( Vector(-38,-38, -38), Vector(38, 38, 38), 
                              Vector(-30,-30,-30), Vector(30, 30, 30) ), # Mortar Synth
    'HULL_MEDIUM_TALL' : ( Vector(-18,-18,   0), Vector(18, 18, 80), 
                           Vector(-12,-12, 0), Vector(12, 12, 80) ), # Hunter
    'HULL_TINY_FLUID' : ( Vector(-8,-8,   0), Vector(8, 8, 16),
                          Vector(-8,-8, 0), Vector(8, 8, 16) ), # Blob?
    'HULL_MEDIUMBIG' : ( Vector(-20,-20,   0), Vector(20, 20, 69),
                         Vector(-20,-20, 0), Vector(20, 20, 69) ), # Drones
                         
    # Dota 2
    'HULL_HERO_LARGE' : ( Vector(-50,-50,   0), Vector(50, 50, 72),
                         Vector(-50,-50, 0), Vector(50, 50, 72) ),
    'DOTA_HULL_SIZE_HERO' : ( Vector(-24,-24,   0), Vector(24, 24, 72),
                         Vector(-24,-24, 0), Vector(24, 24, 72) ),  
    'DOTA_HULL_SIZE_REGULAR' : ( Vector(-16,-16,   0), Vector(16, 16, 72),
                                 Vector(-16,-16, 0), Vector(16, 16, 72) ),
    'DOTA_HULL_SIZE_SIEGE' : ( Vector(-16,-16,   0), Vector(16, 16, 48),
                                 Vector(-16,-16, 0), Vector(16, 16, 48) ),
    'DOTA_HULL_SIZE_SMALL' : ( Vector(-8,-8,   0), Vector(8, 8, 8),
                                 Vector(-8,-8, 0), Vector(8, 8, 8) ),
                                 
    'DOTA_HULL_SIZE_FILLER' : ( Vector(-96,-96,   0), Vector(96, 96, 96),
                                 Vector(-96,-96, 0), Vector(96, 96, 96) ),
    'DOTA_HULL_SIZE_HUGE' : ( Vector(-80,-80,   0), Vector(80, 80, 80),
                         Vector(-80,-80, 0), Vector(80, 80, 80) ), 

    'DOTA_HULL_SIZE_BUILDING' : ( Vector(-96,-96,   0), Vector(96, 96, 72),
                                 Vector(-96,-96, 0), Vector(96, 96, 72) ),
    'DOTA_HULL_SIZE_TOWER' : ( Vector(-144,-144,   0), Vector(144, 144, 72),
                                 Vector(-144,-144, 0), Vector(144, 144, 72) ),
    'DOTA_HULL_SIZE_BARRACKS': ( Vector(-144,-144,   0), Vector(144, 144, 72),
                                 Vector(-144,-144, 0), Vector(144, 144, 72) ),
}

def Mins(id):
    return hull[id][0]

def Maxs(id):
    return hull[id][1]

def SmallMins(id):
    return hull[id][2]

def SmallMaxs(id):
    return hull[id][3]

def Length(id):
    return (hull[id][1].x - hull[id][0].x) 

def Width(id):
    return (hull[id][1].y - hull[id][0].y)

def Height(id):
    return (hull[id][1].z - hull[id][0].z)
