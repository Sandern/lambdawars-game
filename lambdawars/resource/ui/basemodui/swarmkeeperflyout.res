"Resource/UI/OptionsFlyout.res"
{
	"PnlBackground"
	{
		"ControlName"		"Panel"
		"fieldName"			"PnlBackground"
		"xpos"				"0"
		"ypos"				"0"
		"zpos"				"-1"
		"wide"				"156"
		"tall"				"65" [$X360]
		"tall"				"145" [$WIN32]
		"visible"			"1"
		"enabled"			"1"
		"paintbackground"	"1"
		"paintborder"		"1"
	}
	
	"BtnDK1Level"	[$WIN32]
	{
		"ControlName"			"BaseModHybridButton"
		"fieldName"				"BtnDK1Level"
		"xpos"					"0"
		"ypos"					"0"
		"wide"					"150"
		"tall"					"20"
		"autoResize"			"1"
		"pinCorner"				"0"
		"visible"				"1"
		"enabled"				"1"
		"tabPosition"			"0"
		//"navUp"					"BtnCloud"
		//"navDown"				"BtnBrightness"
		"tooltiptext"			"#L4D_video_tip"
		"labelText"				"Dungeon Keeper Level 1"
		"style"					"FlyoutMenuButton"
		"command"				"#sk_loadmap #map00001"
	}
    
	"TestMap1"	[$WIN32]
	{
		"ControlName"			"BaseModHybridButton"
		"fieldName"				"TestMap1"
		"xpos"					"0"
		"ypos"					"22"
		"wide"					"150"
		"tall"					"20"
		"autoResize"			"1"
		"pinCorner"				"0"
		"visible"				"1"
		"enabled"				"1"
		"tabPosition"			"0"
		"navUp"					"BtnDK1Level"
		"navDown"				"TestMap2"
		"tooltiptext"			"#L4D_video_tip"
		"labelText"				"Test Map 1"
		"style"					"FlyoutMenuButton"
		"command"				"#sk_loadmap testmap1"
	}
    
	"TestMap2"	[$WIN32]
	{
		"ControlName"			"BaseModHybridButton"
		"fieldName"				"TestMap2"
		"xpos"					"0"
		"ypos"					"44"
		"wide"					"150"
		"tall"					"20"
		"autoResize"			"1"
		"pinCorner"				"0"
		"visible"				"1"
		"enabled"				"1"
		"tabPosition"			"0"
		"navUp"					"TestMap1"
		"navDown"				"BtnDK1Level"
		"tooltiptext"			"#L4D_video_tip"
		"labelText"				"Test Map 2"
		"style"					"FlyoutMenuButton"
		"command"				"#sk_loadmap testmap2"
	}
    
}