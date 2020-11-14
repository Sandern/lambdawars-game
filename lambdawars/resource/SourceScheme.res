///////////////////////////////////////////////////////////
// Tracker scheme resource file
//
// sections:
//		Colors			- all the colors used by the scheme
//		BaseSettings	- contains settings for app to use to draw controls
//		Fonts			- list of all the fonts used by app
//		Borders			- description of all the borders
//
///////////////////////////////////////////////////////////
Scheme
{
	//////////////////////// COLORS ///////////////////////////
	// color details
	// this is a list of all the colors used by the scheme
	Colors
	{
		// base colors
		"White"				"255 255 255 255"
		"OffWhite"			"216 216 216 255"
		"DullWhite"			"142 142 142 255"
		"Orange"			"255 155 0 255"
		"TransparentBlack"	"0 0 0 128"
		"Black"				"0 0 0 255"

		"Blank"				"0 0 0 0"
		"TestColor"			"255 0 0 255"

		// scheme-specific colors
		"OffWhite"			"216 222 211 255"
		"DullGreen"			"216 222 211 255"
		"Maize"				"196 181 80 255"

		"LightGrayBG"			"121 126 121 255"
		"GrayBG"			"73 78 73 255"
		"GrayBG2"			"82 89 78 255"

		SecBG				GrayBG2

		"ClayBG"			"70 70 70 255"
		"ClayButtonBG"			"87 88 88 255"
		"ClayEnabled"			"85 88 82 255"
		"ClayKeyFocus"			"89 92 77 255"
		"ClayMouseDown"			"85 85 85 255"
		"ClayDisabledText"		"128 134 126 255"
		"ClayLightGreen"		"173 181 168 255"	// frame button (close X) etc
		"ClayDimLightGreen"		"166 172 162 255"	// frame button and title without focus etc
		"LightClayBG"			"104 106 101 255"	// property sheet interior, active tab
		"LightClayButtonBG"		"125 128 120 255"	// buttons on property sheet interior, active tab
		"DarkClayBG"			"47 49 45 255"		// shadow
		"p_ClayMouseDown"		"94 94 94 255"
		"ClaySheetBottom"		"92 89 87 255"

		"MaizeBG"			"145 134 60 255"	// background color of any selected text or menu item

		"GreenBG"			"76 88 68 255"
		"LightGreenBG"			"90 106 80 255"		// darker background color
		"DarkGreenBG"			"62 70 55 255"		// background color of text edit panes (chat, text entries, etc.)

		"DisabledText1"			"117 128 111 255"	// disabled text
		"DisabledText2"			"40 46 34 255"		// overlay color for disabled text (to give that inset look

		"NotificationBodyText"		"White"

		// New colors
		"TransparentGray"		"64 64 64 100"
        "TransparentDarkBrown"      "60 56 53 190"
        "TransparentDarkBrown2"     "60 56 53 100"

		// button state text colors
		"Normal"			"143 146 141 255"
		"Over"				"196 181 80 255"		// same as Maize
		"Down"				"35 36 33 255"

	    // background colors
		"ControlBG"			"76 88 68 255"		// background color of controls
		"ControlDarkBG"		"90 106 80 255"		// darker background color; used for background of scrollbars
		"WindowBG"			"62 70 55 255"		// background color of text edit panes (chat, text entries, etc.)
		"SelectionBG"		"90 84 75 255"	// background color of any selected text or menu item
		"SelectionBG2"		"69 64 57 255"		// selection background in window w/o focus
		"ListBG"			"39 36 34 255"		// background of server browser, buddy list, etc.

		// titlebar colors
		"TitleDimText"			"136 145 128 255"
		"TitleBG"			"TestColor"
		"TitleDimBG"			"TestColor"

		// border colors
		"BorderBright"			"128 128 128 255"	// the lit side of a control
		"BorderDark"			"40 46 34 255"		// the dark/unlit side of a control
		"BorderSelection"		"0 0 0 255"		// the additional border color for displaying the default/selected button

		DarkGray						"37 37 37 255"

		AvatarBlue				"153 204 255 255"

		"SteamLightGreen"	"157 194 80 255"
		"AchievementsLightGrey"		"79 79 79 255"
		"AchievementsDarkGrey"		"55 55 55 255"
		"AchievementsInactiveFG"	"130 130 130 255"

		"ScrollBarGrey"		"51 51 51 255"
		"ScrollBarHilight"	"110 110 110 255"
		"ScrollBarDark"		"38 38 38 255"
	}

	///////////////////// BASE SETTINGS ////////////////////////
	//
	// default settings for all panels
	// controls use these to determine their settings
	BaseSettings
	{
		// vgui_controls color specifications
		Border.Bright					"200 200 200 196"	// the lit side of a control
		Border.Dark						"40 40 40 196"		// the dark/unlit side of a control
		Border.Selection				"0 0 0 196"			// the additional border color for displaying the default/selected button

		Button.TextColor				"White"
		Button.BgColor					"TransparentDarkBrown"
		Button.ArmedTextColor			"Maize"
		Button.ArmedBgColor				"TransparentDarkBrown"				[$WIN32]
		Button.DepressedTextColor		"White"
		Button.DepressedBgColor			"TransparentDarkBrown"
		Button.FocusBorderColor			"Maize"

		CheckButton.TextColor			"OffWhite"
		CheckButton.SelectedTextColor	"White"
		CheckButton.BgColor				"TransparentBlack"
		CheckButton.Border1  			"Border.Dark" 		// the left checkbutton border
		CheckButton.Border2  			"Border.Bright"		// the right checkbutton border
		CheckButton.Check				"White"				// color of the check itself

		ComboBoxButton.ArrowColor		"DullWhite"
		ComboBoxButton.ArmedArrowColor	"White"
		ComboBoxButton.BgColor			"Blank"
		ComboBoxButton.DisabledBgColor	"Blank"

		Frame.TitleTextInsetX			16
		Frame.ClientInsetX				8
		Frame.ClientInsetY				6
		Frame.BgColor					"TransparentDarkBrown"
		Frame.OutOfFocusBgColor			"TransparentDarkBrown2"	[$WIN32]
		Frame.FocusTransitionEffectTime	"0.3"							// time it takes for a window to fade in/out on focus/out of focus
		Frame.TransitionEffectTime		"0.3"				[$WIN32]	// time it takes for a window to fade in/out on open/close
		Frame.TransitionEffectTime		"0.2"						// time it takes for a window to fade in/out on open/close
		Frame.AutoSnapRange				"0"
		FrameGrip.Color1				"200 200 200 196"
		FrameGrip.Color2				"0 0 0 196"
		FrameTitleButton.FgColor		"200 200 200 196"
		FrameTitleButton.BgColor		"Blank"
		FrameTitleButton.DisabledFgColor	"255 255 255 192"
		FrameTitleButton.DisabledBgColor	"Blank"
		FrameSystemButton.FgColor		"Blank"
		FrameSystemButton.BgColor		"Blank"
		FrameSystemButton.Icon			""
		FrameSystemButton.DisabledIcon	""
		FrameTitleBar.Font				"UiBold"		[$WIN32]
		FrameTitleBar.Font				"DefaultLarge"	[$WIN32]
		FrameTitleBar.TextColor			"White"
		FrameTitleBar.BgColor			"Blank"
		FrameTitleBar.DisabledTextColor	"255 255 255 192"
		FrameTitleBar.DisabledBgColor	"Blank"

		GraphPanel.FgColor				"White"
		GraphPanel.BgColor				"TransparentBlack"

		Label.TextDullColor				"DullWhite"
		Label.TextColor					"OffWhite"
		Label.TextBrightColor			"White"
		Label.SelectedTextColor			"White"
		Label.BgColor					"Blank"
		Label.DisabledFgColor1			"117 117 117 255"
		Label.DisabledFgColor2			"30 30 30 255"

		ListPanel.TextColor					"OffWhite"
		ListPanel.TextBgColor				"Blank"
		ListPanel.BgColor					"TransparentBlack"
		ListPanel.SelectedTextColor			"Black"
		ListPanel.SelectedBgColor			"Orange"
		ListPanel.SelectedOutOfFocusBgColor	"255 155 0 128"
		ListPanel.EmptyListInfoTextColor	"OffWhite"

		ImagePanel.fillcolor			"Blank"
		Menu.TextColor					"White"
		Menu.BgColor					"160 160 160 64"
		Menu.ArmedTextColor				"Black"
		Menu.ArmedBgColor				"Orange"
		Menu.TextInset					"6"

		Panel.FgColor					"DullWhite"
		Panel.BgColor					"Blank"

		ProgressBar.FgColor				"White"
		ProgressBar.BgColor				"TransparentBlack"

		PropertySheet.TextColor			"OffWhite"
		PropertySheet.SelectedTextColor	"White"
		PropertySheet.TransitionEffectTime	"0.25"	// time to change from one tab to another

		RadioButton.TextColor			"DullWhite"
		RadioButton.SelectedTextColor	"White"

		RichText.TextColor				"OffWhite"
		RichText.BgColor				"DarkGray"
		RichText.SelectedTextColor		"Black"
		RichText.SelectedBgColor		"Orange"

		ScrollBar.Wide					17
	  	ScrollBarNobBorder.Outer 			"ScrollBarDark"
		ScrollBarNobBorder.Inner 			"ScrollBarGrey"
		ScrollBarNobBorderHover.Inner 			"ScrollBarGrey"
		ScrollBarNobBorderDragging.Inner 		"ScrollBarHilight"

		ScrollBarButton.FgColor				"ScrollBarHilight"
		ScrollBarButton.BgColor				"Blank"
		ScrollBarButton.ArmedFgColor		"White"
		ScrollBarButton.ArmedBgColor		"Blank"
		ScrollBarButton.DepressedFgColor	"White"
		ScrollBarButton.DepressedBgColor	"Blank"

		ScrollBarSlider.FgColor				"MaizeBG"			// nob color
		ScrollBarSlider.BgColor				"ScrollBarDark"	// slider background color
		ScrollBarSlider.NobFocusColor			"ScrollBarHilight"		// nob mouseover color
		ScrollBarSlider.NobDragColor			"ScrollBarHilight"		// nob active drag color

		SectionedListPanel.HeaderTextColor	"White"
		SectionedListPanel.HeaderBgColor	"Blank"
		SectionedListPanel.DividerColor		"Black"
		SectionedListPanel.TextColor		"DullWhite"
		SectionedListPanel.BrightTextColor	"White"
		SectionedListPanel.BgColor			"TransparentBlack"
		SectionedListPanel.SelectedTextColor			"Black"
		SectionedListPanel.SelectedBgColor				"Orange"
		SectionedListPanel.OutOfFocusSelectedTextColor	"Black"
		SectionedListPanel.OutOfFocusSelectedBgColor	"255 155 0 128"

		Slider.NobColor				"108 108 108 255"
		Slider.NobFocusColor			"200 200 200 255"
		Slider.TextColor			"180 180 180 255"
		Slider.TrackColor			"31 31 31 255"
		Slider.DisabledTextColor1	"117 117 117 255"
		Slider.DisabledTextColor2	"30 30 30 255"

		TextEntry.TextColor			"OffWhite"
		TextEntry.BgColor			"DarkGray"
		TextEntry.CursorColor		"OffWhite"
		TextEntry.DisabledTextColor	"ClayDisabledText"
		TextEntry.DisabledBgColor	"Blank"
		TextEntry.SelectedTextColor	"Black"
		TextEntry.SelectedBgColor	"Maize"
		TextEntry.OutOfFocusSelectedBgColor	"255 155 0 128"
		TextEntry.FocusEdgeColor	"0 0 0 196"

		ToggleButton.SelectedTextColor	"White"

		Tooltip.TextColor			"0 0 0 196"
		Tooltip.BgColor				"Orange"

		TreeView.BgColor			"TransparentBlack"

		WizardSubPanel.BgColor		"Blank"

		// scheme-specific colors
		MainMenu.TextColor			"White"				[$WIN32]
		MainMenu.ArmedTextColor		"200 200 200 255"	[$WIN32]
		MainMenu.DepressedTextColor	"192 186 80 255"
		MainMenu.MenuItemHeight		"30"				[$WIN32]
		MainMenu.Inset				"32"
		MainMenu.Backdrop			"0 0 0 156"

		Console.TextColor			"OffWhite"
		Console.DevTextColor		"White"

		NewGame.TextColor			"White"
		NewGame.FillColor			"0 0 0 255"
		NewGame.SelectionColor		"Orange"			[$WIN32]
		NewGame.DisabledColor		"128 128 128 196"

	//////////////////////// HYBRID BUTTON STYLES /////////////////////////////
	//
	// Custom styles for use with L4D360HybridButtons

		HybridButton.BorderColor					"GreyBlue"
		HybridButton.BlotchColor					"DarkBlueTrans"

		// These bypass all of CA's horrific style.  Look/Feel is code based
			
		// main or ingame menu only
		MainMenuButton.Style						"1"
		MainMenuButton.TextInsetY					"0"		[$WIN32]
		MainMenuButton.TextInsetY					"1"		[$X360HIDEF]
		MainMenuButton.TextInsetY					"0"		[$X360LODEF]
		
		// inside of a flyout menu only
		FlyoutMenuButton.Style						"2"
		FlyoutMenuButton.TextInsetX					"8"
		FlyoutMenuButton.TextInsetY					"2"		[$WIN32]
		FlyoutMenuButton.TextInsetY					"5"		[$X360]

		// inside a dialog, contains a RHS value, usually causes a flyout
		DropDownButton.Style						"3"
		DropDownButton.TextInsetY					"0"		[$WIN32HIDEF]
		DropDownButton.TextInsetY					"-1"	[$WIN32LODEF]
		DropDownButton.TextInsetY					"2"		[$X360HIDEF]
		DropDownButton.TextInsetY					"1"		[$X360LODEF]

		// centers within the focus
		DialogButton.Style							"4"
		DialogButton.TextInsetY						"0"		[$WIN32HIDEF]
		DialogButton.TextInsetY						"-1"	[$WIN32LODEF]
		DialogButton.TextInsetY						"2"		[$X360HIDEF]
		DialogButton.TextInsetY						"1"		[$X360LODEF]
		
		// left aligned within the focus
		DefaultButton.Style							"0"
		DefaultButton.TextInsetY					"0"		[$WIN32HIDEF]
		DefaultButton.TextInsetY					"-1"	[$WIN32LODEF]
		DefaultButton.TextInsetY					"2"		[$X360HIDEF]
		DefaultButton.TextInsetY					"1"		[$X360LODEF]
		
		// left aligned within the focus
		RedButton.Style								"5"
		RedButton.TextInsetY						"0"		[$WIN32HIDEF]
		RedButton.TextInsetY						"-1"	[$WIN32LODEF]

		// left aligned within the focus
		RedMainButton.Style							"6"
		RedMainButton.TextInsetY					"0"		[$WIN32HIDEF]
		RedMainButton.TextInsetY					"-1"	[$WIN32LODEF]
		
		// left aligned within the focus
		SmallButton.Style							"7"
		SmallButton.TextInsetY						"1"
		
		// specialized button, only appears in game mode carousel
		GameModeButton.Style						"9"
		GameModeButton.TextInsetY					"0"		[$WIN32]
		GameModeButton.TextInsetY					"1"		[$X360HIDEF]
		GameModeButton.TextInsetY					"0"		[$X360LODEF]
		
		// main or ingame menu only
		MainMenuSmallButton.Style					"10"
		
		// who invented this crazy style system anyway?
		AlienSwarmMenuButton.Style					"11"
		AlienSwarmMenuButtonSmall.Style					"12"
		AlienSwarmDefault.Style									"13"

		MediumButton.Style						"8"

	}

	//////////////////////// FONTS /////////////////////////////
	//
	// describes all the fonts
	Fonts
	{
		// fonts are used in order that they are listed
		// fonts listed later in the order will only be used if they fulfill a range not already filled
		// if a font fails to load then the subsequent fonts will replace

		"DefaultSystemUI" [$WIN32]
		{
			"1"
			{
				"name"		"Verdana" //"Neo Sans"
				"tall"		"14"
				"weight"	"100"
				"antialias"	"1"
			}
		}

		"DebugFixed"
		{
			"1"
			{
				"name"		"Courier New"
				"tall"		"10"			
				"weight"	"400"
				"antialias" "1"
			}
		}

		"DebugFixedSmall" 
		{
			"1"
			{
				"name"		"Courier New"
				"tall"		"7"
				"weight"	"400"
				"antialias" "1"
			}
		}

		"DefaultFixedOutline" 
		{
			"1"
			{
				"name"		 "Lucida Console"
				"tall"		 "10"
				"weight"	 "0"
				"outline"	 "1"
			}
		}

		"DefaultFixed" 
		{
			"1"
			{
				"name"		"Lucida Console"
				"tall"		"10"
				"weight"	"0"
			}
		}

		"DefaultFixedDropShadow" 
		{
			"1"
			{
				"name"		"Lucida Console"
				"tall"		"10"
				"weight"	"0"
				"dropshadow" "1"
			}
		}

		"Default" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"16"
				"weight"	"500"
			}
		}

		"DefaultBold" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"16"
				"weight"	"1000"
			}
		}

		"DefaultUnderline" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"16"
				"weight"	"500"
				"underline" "1"
			}
		}

		"DefaultSmall" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"0"
			}
		}

		"DefaultSmallDropShadow" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"13"
				"weight"	"0"
				"dropshadow" "1"
			}
		}

		"DefaultVerySmall" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"0"
			}
		}

		"DefaultLarge" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"18"
				"weight"	"0"
			}
		}

		"UiBold" 
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"1000"
			}
		}

		"MenuLarge" 
		{
			"1"
			{
				"name"		"Verdana"
				"tall"		"16"
				"weight"	"600"
				"antialias" "1"
			}
		}

		"AchievementTitleFont" 
		{
			"1"
			{
				"name"		"Verdana"
				"tall"		"20"
				"weight"	"1200"
				"antialias" "1"
				"outline" "1"
			}
		}

		"AchievementDescriptionFont" 
		{
			"1"
			{
				"name"		"Verdana"
				"tall"		"15"
				"weight"	"1200"
				"antialias" "1"
				"outline"	"1"
				"yres"		"0 480"
			}

			"2"
			{
				"name"		"Verdana"
				"tall"		"20"
				"weight"	"1200"
				"antialias" "1"
				"outline"	 "1"
				"yres"		"481 10000"
			}
		}

		"ConsoleText" 
		{
			"1"
			{
				"name"		"Lucida Console" 
				"tall"		"10" 
				"weight"	"500"
			}
		}

		// this is the symbol font
		"Marlett" 
		{
			"1"
			{
				"name"		"Marlett"
				"tall"		"14"
				"weight"	"0"
				"symbol"	"1"
			}
		}

		"Trebuchet24" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"24"
				"weight"	"900"
			}
		}

		"Trebuchet20" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"20"
				"weight"	"900"
			}
		}

		"Trebuchet18" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"18"
				"weight"	"900"
			}
		}

		// Friend fonts
		FriendsSmall
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"800"
			}
		}
		FriendsMedium
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"13"
				"weight"	"800"
			}
		}

		FriendsVerySmall
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"0"
			}
		}
		FriendsVerySmallUnderline
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"0"
				"underline"	"1"
			}
		}

		// HUD numbers
		// We use multiple fonts to 'pulse' them in the HUD, hence the need for many of near size
		"HUDNumber" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"40"
				"weight"	"900"
			}
		}

		"HUDNumber1" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"41"
				"weight"	"900"
			}
		}

		"HUDNumber2" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"42"
				"weight"	"900"
			}
		}

		"HUDNumber3" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"43"
				"weight"	"900"
			}
		}

		"HUDNumber4" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"44"
				"weight"	"900"
			}
		}

		"HUDNumber5" 
		{
			"1"
			{
				"name"		"Trebuchet MS"
				"tall"		"45"
				"weight"	"900"
			}
		}

		TitleFont 
		{
			"1"
			{
				"name"		"HalfLife2"
				"tall"		"72"
				"weight"	"400"
				"antialias"	"1"
				"custom"	"1"
			}
		}

		TitleFont2 
		{
			"1"
			{
				"name"		"HalfLife2"
				"tall"		"120"
				"weight"	"400"
				"antialias"	"1"
				"custom"	"1"
			}
		}

		AchievementItemTitle	
		{
			"1"
			{
				"name"			"Arial"
				"weight"		"1500"
				"tall"			"16"
				"antialias"		"1"
			}
		}

		AchievementItemDescription	
		{
			"1"
			{
				"name"			"Arial"
				"weight"		"1000"
				"tall"			"14"
				"antialias"		"1"
			}
		}
		"MenuTitle"
		{
			"1"
			{
				"name"		"Verdana Bold"
				"tall"		"20"
				"weight"	"500"
			}
		}

		"MenuTitle2"
		{
			"1"
			{
				"name"		"Verdana Bold"
				"tall"		"18"
				"weight"	"500"
			}
		}
	}

	//
	//////////////////// BORDERS //////////////////////////////
	//
	// describes all the border types
	Borders
	{
		BaseBorder		DepressedBorder
		ButtonBorder	RaisedBorder
		ComboBoxBorder	DepressedBorder
		MenuBorder		RaisedBorder
		BrowserBorder	DepressedBorder
		PropertySheetBorder	RaisedBorder

		FrameBorder
		{
			// rounded corners for frames
			"backgroundtype" "2"
		}

		DepressedBorder
		{
			"inset" "0 0 1 1"
			Left
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}
		}
		RaisedBorder
		{
			"inset" "0 0 1 1"
			Left
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 1"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}
		}

		TitleButtonBorder
		{
			"backgroundtype" "0"
		}

		TitleButtonDisabledBorder
		{
			"backgroundtype" "0"
		}

		TitleButtonDepressedBorder
		{
			"backgroundtype" "0"
		}

		ScrollBarButtonBorder
		{
			"inset" "2 2 0 0"
			Left
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}
		}

		ScrollBarButtonDepressedBorder
		{
			"inset" "2 2 0 0"
			Left
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}
		}

		ScrollBarSliderBorder
		{
			"inset" "2 2 0 0"
			Left
			{
				"1"
				{
					"color" "ScrollBarHilight"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "ScrollBarDark"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "ScrollBarHilight"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "ScrollBarDark"
					"offset" "0 0"
				}
			}
		}

		ScrollBarSliderBorderHover ScrollBarSliderBorder
		ScrollBarSliderBorderDragging ScrollBarSliderBorder

		TabBorder
		{
			"inset" "0 0 1 1"
			Left
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}

		}

		TabActiveBorder
		{
			"inset" "0 0 1 0"
			Left
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}

		}


		ToolTipBorder
		{
			"inset" "0 0 1 0"
			Left
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}
		}

		// this is the border used for default buttons (the button that gets pressed when you hit enter)
		ButtonKeyFocusBorder
		{
			"inset" "0 0 1 1"
			Left
			{
				"1"
				{
					"color" "Border.Selection"
					"offset" "0 0"
				}
				"2"
				{
					"color" "Border.Bright"
					"offset" "0 1"
				}
			}
			Top
			{
				"1"
				{
					"color" "Border.Selection"
					"offset" "0 0"
				}
				"2"
				{
					"color" "Border.Bright"
					"offset" "1 0"
				}
			}
			Right
			{
				"1"
				{
					"color" "Border.Selection"
					"offset" "0 0"
				}
				"2"
				{
					"color" "Border.Dark"
					"offset" "1 0"
				}
			}
			Bottom
			{
				"1"
				{
					"color" "Border.Selection"
					"offset" "0 0"
				}
				"2"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}
		}

		ButtonDepressedBorder
		{
			"inset" "2 1 1 1"
			Left
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Border.Dark"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Border.Bright"
					"offset" "0 0"
				}
			}
		}
	}

	//////////////////////// CUSTOM FONT FILES /////////////////////////////
	//
	// specifies all the custom (non-system) font files that need to be loaded to service the above described fonts
	CustomFontFiles
	{
		"1"		"resource/HALFLIFE2.vfont"
	}
}
