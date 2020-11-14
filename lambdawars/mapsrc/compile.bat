rem @echo off

@rem Get steam dir
Set Reg.Key=HKEY_CURRENT_USER\Software\Valve\Steam
Set Reg.Val=SteamPath

For /F "Tokens=2*" %%A In ('Reg Query "%Reg.Key%" /v "%Reg.Val%" ^| Find /I "%Reg.Val%"' ) Do Call Set steamdir=%%B
echo %steamdir%

@rem setlocal makes all of these 'set' calls temporary.setlocal@rem replace with your path to whichever one of the tools you want to run.
set sdkdir=%steamdir%\steamapps\common\alien swarm

@rem replace with the path to your specific mod., this overrides VPROJECT.
set gamedir=%steamdir%\steamapps\Common\Lambda Wars\lambdawarsdev

@rem replace with the path to your specific map
set mapsrc=%steamdir%\steamapps\Common\Lambda Wars\lambdawarsdev\mapsrc\
set mapname=%~n1

@rem Additional arguments
@rem Number of threads the compile tools may use 
rem set args=-threads 6
set args=

cd /d "%sdkdir%"

@rem VBSP
@rem bin\vbsp.exe -game "%gamedir%" -onlyents "%mapsrc%%mapname%"
bin\vbsp.exe -game "%gamedir%" %args% "%mapsrc%%mapname%"

@rem VVIS
@rem bin\vvis.exe -radius_override 2000 -game "%gamedir%" %args% "%mapsrc%%mapname%"
@rem bin\vvis.exe -radius_override 5000 -game "%gamedir%" %args% "%mapsrc%%mapname%"
bin\vvis.exe -game "%gamedir%" %args% "%mapsrc%%mapname%"

@rem VRAD
rem bin\vrad.exe -game "%gamedir%" -both -final %args% "%mapsrc%%mapname%"
@rem bin\vrad.exe -game "%gamedir%" -nodetaillight -noextra -nossprops -fast %args% "%mapsrc%%mapname%"
bin\vrad.exe -game "%gamedir%" -both -StaticPropLighting -StaticPropPolys -TextureShadows -final %args% "%mapsrc%%mapname%"
@rem bin\vrad.exe -game "%gamedir%" -final %args% "%mapsrc%%mapname%"

@rem Copy to game maps folder
copy "%mapsrc%%mapname%.bsp" "%gamedir%\maps\%mapname%.bsp"

@pause