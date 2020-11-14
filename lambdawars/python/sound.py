from _sound import *

# From const
SOUND_NORMAL_CLIP_DIST = 1000.0

#-----------------------------------------------------------------------------
# channels
#-----------------------------------------------------------------------------
CHAN_REPLACE = -1
CHAN_AUTO = 0
CHAN_WEAPON = 1
CHAN_VOICE = 2
CHAN_ITEM = 3
CHAN_BODY = 4
CHAN_STREAM = 5         # allocate stream channel from the static or dynamic area
CHAN_STATIC = 6         # allocate channel from the static area 
CHAN_VOICE_BASE = 7     # allocate channel for network voice data
CHAN_USER_BASE = (CHAN_VOICE_BASE+128) # Anything >= this number is allocated to game code.

#-----------------------------------------------------------------------------
# common volume values
#-----------------------------------------------------------------------------
VOL_NORM = 1.0


#-----------------------------------------------------------------------------
# common attenuation values
#-----------------------------------------------------------------------------
ATTN_NONE = 0.0
ATTN_NORM = 0.8
ATTN_IDLE = 2.0
ATTN_STATIC = 1.25
ATTN_RICOCHET = 1.5