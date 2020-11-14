"Resource/UI/DropDownConfig.res"
{
	"PnlBackground"
	{
		"ControlName"			"Panel"
		"fieldName"				"PnlBackground"
		"xpos"					"0"
		"ypos"					"0"
		"zpos"					"-1"
		"wide"					"156"
		"tall"					"65"
		"visible"				"1"
		"enabled"				"1"
		"paintbackground"		"1"
		"paintborder"			"1"
	}

	"BtnRTS"
	{
		"ControlName"			"BaseModHybridButton"
		"fieldName"				"BtnRTS"
		"xpos"					"0"
		"ypos"					"0"
		"wide"					"150"
		"tall"					"20"
		"autoResize"			"1"
		"pinCorner"				"0"
		"visible"				"1"
		"enabled"				"1"
		"tabPosition"			"0"
		"wrap"					"1"
		"navUp"					"BtnFPS"
		"navDown"				"BtnFPS"
		"labelText"				"#GameUI_RTS"
		"tooltiptext"			"#GameUI_RTS"
		"disabled_tooltiptext"	"#GameUI_RTS"
		"style"					"FlyoutMenuButton"
		"command"				"#GameUI_RTS"
		"OnlyActiveUser"		"1"
	}
	
	"BtnFPS"
	{
		"ControlName"			"BaseModHybridButton"
		"fieldName"				"BtnFPS"
		"xpos"					"0"
		"ypos"					"20"
		"wide"					"150"
		"tall"					"20"
		"autoResize"			"1"
		"pinCorner"				"0"
		"visible"				"1"
		"enabled"				"1"
		"tabPosition"			"0"
		"wrap"					"1"
		"navUp"					"BtnRTS"
		"navDown"				"BtnRTS"
		"labelText"				"#GameUI_FPS"
		"tooltiptext"			"#GameUI_FPS"
		"disabled_tooltiptext"	"#GameUI_FPS"
		"style"					"FlyoutMenuButton"
		"command"				"#GameUI_FPS"
		"OnlyActiveUser"		"1"
	}
}
