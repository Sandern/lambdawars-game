- Use the Alien Swarm SDK to create maps. To setup hammer do the following:
    1. Go to the tools tab and start Alien Swarm - SDK
    2. Click "Edit game configurations"
    3. Click "add"
    4. Make up a name (e.g. Lambda Wars)
    5. Enter the path to the Lambda Wars mod folder (e.g. d:\steam\steamapps\SourceMods\lambdawars)
    6. Start Hammer and go to tools -> Options. Then in "Game Data files" press Add.
    7. Navigate to the hl2wars root folder and select "hl2wars.fgd".
    
- For example maps see the mapsrc in the Half-Life 2: Wars mod folder.
    
- Run pakfiles.bat in the lambdawars folder in case you are using the dev version. This will pack up a few files in a vpk, like detailsprites.vtf. Otherwise some of the Alien Swarm files will override our mod file (TODO: Can we run hammer with -override_vpk?).
    
- Compiling: see compile.bat (or just use hammer)
