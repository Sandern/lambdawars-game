.. _tut-gamerules:

**********************************
Gamerules
**********************************
The gamerules decide the winning and losing conditions of a game.

Make a new file mygamerules.py inside the tutorial gamerules folder and add the following code::

    from core.gamerules import GamerulesInfo, WarsBaseGameRules
    
    class ExampleGameRules(WarsBaseGameRules):
        # Called when your gamerules are activated. Initialize your gamemode here.
        def InitGamerules(self):
            super(ExampleGameRules, self).InitGamerules()
        
        # Called when the gamerules are shutdown (level shutdown or the gamerules changed)
        def ShutdownGamerules(self):
            super(ExampleGameRules, self).ShutdownGamerules()
            
        # The OnThink method is called per frame
        # Put all your game logic here
        # For example the Annihilation gamemode checks the number of buildings
        # for each player to see if there is a winner
        # The Overrun gamemode on the other hand only does this to check if the players lost
        # and furthermore checks if a new wave needs to be spawned.
        # Also see wars_game.gamerules for examples
        def OnThink(self):
            pass

    # Registers our gamerules within the game package
    # The gamelobby will use this info to display the gamerules information
    class ExampleInfo(GamerulesInfo):
        name = 'tutorial' # Internal name
        displayname = 'Tutorial Gamerules' # Name shown in the gamelobby (and possible other locations)
        description = 'Tutorial Gamerules description.' # Description used in the gamelobby
        cls = ExampleGameRules # The class that is created when this gamerules is activated
        useteams = False # Whether teams are allowed
        
Save the file and enter the following commands in the console::

    reload_gamepackage tutorial; wars_setgamerules tutorial

This will reload the code and activate your new gamerules.