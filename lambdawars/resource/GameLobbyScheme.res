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
		"TransparentBlack"		"0 0 0 128"
		"Black"				"0 0 0 255"
		"Blank"				"1 1 1 0"
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
		
		// button state text colors
		"Normal"			"143 146 141 255"
		"Over"				"196 181 80 255"		// same as Maize
		"Down"				"35 36 33 255"

		// background colors

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
		Button.BgColor					"LightClayBG"
		Button.ArmedTextColor			"Maize"
		Button.ArmedBgColor				"LightClayBG"				[$WIN32]
		Button.ArmedBgColor				"190 115 0 255"		[$X360]
		Button.DepressedTextColor		"Maize"
		Button.DepressedBgColor			"LightClayBG"
		Button.FocusBorderColor			"Black"
		
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

		Frame.ClientInsetX				10
		Frame.ClientInsetY				35
		Frame.BgColor					"ClayBG"
		Frame.OutOfFocusBgColor				"63 70 57 255"
		Frame.FocusTransitionEffectTime			"0"			// time it takes for a window to fade in/out on focus/out of focus
		Frame.TransitionEffectTime			"0.25"			// time it takes for a window to fade in/out on open/close
		Frame.OnDragAlphaDelayTime			"0.15"			// time it takes after clicking the title bar of a window before the alpha multiplier kicks in
		Frame.OnDragAlphaMultiplier			"1.0"			// multiplier applied to alpha while dragging a frame
		Frame.AutoSnapRange				"6"
		Frame.UsesAlphaBlending				1
		FrameSystemButton.Icon				"skins/Flat_Steam/resource/icon_steam"
		FrameSystemButton.DisabledIcon			"skins/Flat_Steam/resource/icon_steam_disabled"

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

		RichText.TextColor				"White"
		RichText.BgColor				"DarkGray"
		RichText.SelectedTextColor		"Black"
		RichText.SelectedBgColor		"Orange"

		ScrollBar.Wide					17

		ScrollBarButton.FgColor				"White"
		ScrollBarButton.BgColor				"Blank"
		ScrollBarButton.ArmedFgColor		"White"
		ScrollBarButton.ArmedBgColor		"Blank"
		ScrollBarButton.DepressedFgColor	"White"
		ScrollBarButton.DepressedBgColor	"Blank"

		ScrollBarSlider.FgColor				"Blank"			// nob color
		ScrollBarSlider.BgColor				"255 255 255 64"	// slider background color

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
		Slider.TextColor			"180 180 180 255"
		Slider.TrackColor			"31 31 31 255"
		Slider.DisabledTextColor1	"117 117 117 255"
		Slider.DisabledTextColor2	"30 30 30 255"

		TextEntry.TextColor			"White"
		TextEntry.BgColor			"DarkGray"
		TextEntry.CursorColor		"White"
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
		MainMenu.TextColor			"200 200 200 255"	[$X360]
		MainMenu.ArmedTextColor		"200 200 200 255"	[$WIN32]
		MainMenu.ArmedTextColor		"White"				[$X360]
		MainMenu.DepressedTextColor	"192 186 80 255"
		MainMenu.MenuItemHeight		"30"				[$WIN32]
		MainMenu.MenuItemHeight			"22"				[$X360]
		MainMenu.MenuItemHeight_hidef	"32"				[$X360]
		MainMenu.Inset				"32"
		MainMenu.Backdrop			"0 0 0 156"

		Console.TextColor			"OffWhite"
		Console.DevTextColor		"White"

		NewGame.TextColor			"White"
		NewGame.FillColor			"0 0 0 255"
		NewGame.SelectionColor		"Orange"			[$WIN32]
		NewGame.SelectionColor		"0 0 0 255"			[$X360]
		NewGame.DisabledColor		"128 128 128 196"

		MessageDialog.MatchmakingBG			"46 43 42 255"	[$X360]
		MessageDialog.MatchmakingBGBlack			"22 22 22 255"	[$X360]
		
		MatchmakingMenuItemTitleColor			"200 184 151 255"	[$X360]
		MatchmakingMenuItemDescriptionColor		"200 184 151 255"	[$X360]
	}

	//////////////////////// BITMAP FONT FILES /////////////////////////////
	//
	// Bitmap Fonts are ****VERY*** expensive static memory resources so they are purposely sparse
	BitmapFontFiles
	{
		// UI buttons, custom font, (256x64)
		"Buttons"		"materials/vgui/fonts/buttons_32.vbf"
	}

	//////////////////////// FONTS /////////////////////////////
	//
	// describes all the fonts
	Fonts
	{
		// fonts are used in order that they are listed
		// fonts listed later in the order will only be used if they fulfill a range not already filled
		// if a font fails to load then the subsequent fonts will replace
		// fonts are used in order that they are listed
		"Default"
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"13"
				"weight"	"0"
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
				"tall"		"13"
				"weight"	"800"
				"underline" "1"
			}
		}
		"DefaultSmall"
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"11"
				"weight"	"800"
			}
		}
		ListSmall
		{
			1
			{
				name		Tahoma
				tall		12
				weight		0
			}
		}
		"DefaultVerySmall"
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"12"
				"weight"	"800"
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
				"tall"		"14"
				"weight"	"1000"
			}
		}
		"HeadlineLarge"
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"22"
				"weight"	"1000"
				"antialias" "1"
			}
		}
		"UiHeadline"
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"13"
				"weight"	"0"
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
		MarlettLarge
		{
			"1"
			{
				"name"		"Marlett"
				"tall"		"16"
				"weight"	"0"
				"symbol"	"1"
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
		OverlayTaskbarFont
		{
			"1"
			{
				"name"		"Tahoma"
				"tall"		"16"
				"weight"	"1000"
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
		//ButtonBorder	ButtonBorder
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
			inset				"4 0 4 0"
			Left
			{
				"1"
				{
					"color" "Black"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Black"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}
		}
		
		AvatarBorder
		{
			inset				"100 0 100 0"
			Left
			{
				"1"
				{
					"color" "AvatarBlue"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "AvatarBlue"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "AvatarBlue"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "AvatarBlue"
					"offset" "0 0"
				}
			}
		}
		
		ButtonBorder
		{
			inset				"4 3 4 4"
			Left
			{
				"1"
				{
					"color" "ClayEnabled"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "ClayEnabled"
					"offset" "0 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "ClayEnabled"
					"offset" "0 1"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "ClayEnabled"
					"offset" "0 0"
				}
			}
		}
		
		RaisedBorder
		{
			inset				"4 0 4 0"
			Left
			{
				"1"
				{
					"color" "Black"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Black"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Black"
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
			inset				"4 0 4 0"
			Left
			{
				"1"
				{
					"color" "Black"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Black"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}
		}

		ButtonDepressedBorder
		{
			inset				"4 0 4 0"
			Left
			{
				"1"
				{
					"color" "Black"
					"offset" "0 1"
				}
			}

			Right
			{
				"1"
				{
					"color" "Black"
					"offset" "1 0"
				}
			}

			Top
			{
				"1"
				{
					"color" "Black"
					"offset" "0 0"
				}
			}

			Bottom
			{
				"1"
				{
					"color" "Black"
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
		"1"		"resource/HALFLIFE2.ttf"
		"2"		"resource/HL2EP2.ttf"		
	}
}
