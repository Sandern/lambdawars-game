//=========== (C) Copyright 1999 Valve, L.L.C. All rights reserved. ===========
//
// The copyright to the contents herein is the property of Valve, L.L.C.
// The contents may be used and/or copied only with the written permission of
// Valve, L.L.C., or in accordance with the terms and conditions stipulated in
// the agreement/contract under which the contents have been supplied.
//=============================================================================

// No spaces in event names, max length 32
// All strings are case sensitive
//
// valid data key types are:
//   string : a zero terminated string
//   bool   : unsigned int, 1 bit
//   byte   : unsigned int, 8 bit
//   short  : signed int, 16 bit
//   long   : signed int, 32 bit
//   float  : float, 32 bit
//   local  : any data, but not networked to clients
//
// following key names are reserved:
//   local      : if set to 1, event is not networked to clients
//   unreliable : networked, but unreliable
//   suppress   : never fire this event
//   time	: firing server time
//   eventid	: holds the event ID

"sdkevents"
{
	"player_death"
	{
		"userid"	"short"   	// user ID who died				
		"attacker"	"short"	 	// user ID who killed
		"weapon"	"string" 	// weapon name killed used
	}
	
	"player_hurt"
	{
		"userid"	"short"   	// user ID who was hurt			
		"attacker"	"short"	 	// user ID who attacked
		"weapon"	"string" 	// weapon name attacker used
	}
	
	"player_changeclass"
	{
		"userid"	"short"		// user ID who changed class
		"class"		"short"		// class that they changed to
	}

	"spec_target_updated"
	{
	}

	"nav_blocked"
	{
		"area"		"long"
		"blocked"	"bool"
	}

	"nav_generate"
	{
	}

	"player_fullyjoined"
	{
		"userid"	"short"		// user ID on server
		"name"		"string"	// player name
	}
    
	"controls_rotate_inactive"
	{
	}

	"controls_rotate_inactive_succ"
	{
	}

	"controls_zoom_inactive"
	{
	}

	"controls_zoom_inactive_success"
	{
	}

	"controls_move_inactive"
	{
	}

	"controls_move_inactive_success"
	{
	}
	
	"wars_nofortifications"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of control point
	}
	
	"wars_start_fortification_cp"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of control point
	}
	
	"wars_fortified_cp"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of control point
	}
	
	"sk_playergrabbed"
	{
		"entindex"	"short" // entindex of creature grabbed
	}
    
	"sk_playerreleased"
	{
		"entindex"	"short" // entindex of creature released
	}
	
	"sk_portal_claimed"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of portal
	}
	"sk_portal_unclaimed"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of portal
	}
    
	"player_control_unit"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of portal
	}
    
	"player_leftcontrol_unit"
	{
		"userid"	"short" // entindex of player
		"entindex"	"short" // entindex of portal
	}

	"button_area_active"
	{
		"userid"	"short"   	// player who sees the active button
		"entindex"	"long"		// trigger entindex
		"prop"		"long"		// prop entindex
		"locked"	"bool"		// does it need hacking?
	}
	
	"button_area_inactive"
	{
		"entindex"	"long"		// trigger entindex
	}
	
	"button_area_used"
	{
		"userid"	"short"		// user ID on server
		"entindex"	"long"		// item entindex
	}

	"jukebox_play_random"
	{
		"fadeintime"	"float"
		"defaulttrack"	"string"
	}
	"jukebox_stop"
	{
		"fadeouttime"	"float"
	}

	"campaign_changed"
	{
		"campaign" "string"
	}
	"swarm_state_changed"
	{
		"state" "short"
	}
}
