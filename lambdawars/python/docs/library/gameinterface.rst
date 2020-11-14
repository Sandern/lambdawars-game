:mod:`gameinterface` --- Gameinterface module
==========================================

.. module:: gameinterface
   :synopsis: Gameinterface module.

.. automodule:: _gameinterface
   :members:


-----------------------
Constants
-----------------------

The following constants are flags for :class:`gameinterface.ConVar`. and :class:`gameinterface.ConCommand`.

.. data:: FCVAR_NONE

   The default, no flags at all.
   
.. data:: FCVAR_UNREGISTERED

   If this is set, don't add to linked list, etc.
   
.. data:: FCVAR_DEVELOPMENTONLY

   Hidden in released products. Flag is removed automatically if ALLOW_DEVELOPMENT_CVARS is defined.
   
.. data:: FCVAR_GAMEDLL

   Defined by the game DLL
   
.. data:: FCVAR_CLIENTDLL

   Defined by the client DLL
   
.. data:: FCVAR_HIDDEN

   Hidden. Doesn't appear in find or autocomplete. Like DEVELOPMENTONLY, but can't be compiled out.
   
.. data:: FCVAR_PROTECTED

    It's a server cvar, but we don't send the data since it's a password, etc.  Sends 1 if it's not bland/zero, 0 otherwise as value

.. data:: FCVAR_SPONLY
    
    This cvar cannot be changed by clients connected to a multiplayer server.

.. data:: FCVAR_ARCHIVE
    
    Set to cause it to be saved to vars.rc

.. data:: FCVAR_NOTIFY

    Notifies players when changed

.. data:: FCVAR_USERINFO

    Changes the client's info string

.. data:: FCVAR_CHEAT

    Only useable in singleplayer / debug / multiplayer & sv_cheats

.. data:: FCVAR_PRINTABLEONLY

    This cvar's string cannot contain unprintable characters ( e.g., used for player name etc ).
    
.. data:: FCVAR_UNLOGGED

    If this is a FCVAR_SERVER, don't log changes to the log file / console if we are creating a log
    
.. data:: FCVAR_NEVER_AS_STRING

    Never try to print that cvar

.. data:: FCVAR_REPLICATED

    Server setting enforced on clients, TODO rename to FCAR_SERVER at some time

.. data:: FCVAR_DEMO

    Record this cvar when starting a demo file

.. data:: FCVAR_DONTRECORD

    Don't record these command in demofiles

.. data:: FCVAR_NOT_CONNECTED

    cvar cannot be changed by a client that is connected to a server

.. data:: FCVAR_ARCHIVE_XBOX

    cvar written to config.cfg on the Xbox

.. data:: FCVAR_SERVER_CAN_EXECUTE

    The server is allowed to execute this command on clients via ClientCommand/NET_StringCmd/CBaseClientState::ProcessStringCmd.

.. data:: FCVAR_SERVER_CANNOT_QUERY

    If this is set, then the server is not allowed to query this cvar's value (via IServerPluginHelpers::StartQueryCvarValue).

.. data:: FCVAR_CLIENTCMD_CAN_EXECUTE

    IVEngineClient::ClientCmd is allowed to execute this command. 

The following constants are flags for :function:`gameinterface.HasApp`. and :function:`gameinterface.GetAppStatus`.

.. data:: APP_EP2

    Episode two.
    
.. data:: APP_EP1

    Episode one.

.. data:: APP_TF2

    Team Fortress 2.

.. data:: APP_PORTAL

    Portal

.. data:: APP_CSS

    Counter-Strike: Source

.. data:: APP_HL1

    Half-Life 1.

.. data:: APP_DODS

    Day of Defeat: Source.

.. data:: APP_L4D1

    Left 4 Dead 1.

.. data:: APP_L4D2

    Left 4 Dead 2.
    
.. data:: APP_PORTAL2

    Portal 2.
    
.. data:: NUM_APPS

    Number of app ids.
    
-----------------------
Data
-----------------------
.. data:: engine

   Reference to instance of :class:`gameinterface.VEngineServer`.
   
.. data:: modelinfo

   Reference to instance of :class:`gameinterface.VModelInfo`.
   
-----------------------
CCommand
-----------------------
.. autoclass:: gameinterface.CCommand
    :members:
    
-----------------------
concommand decorator
-----------------------
.. autofunction:: gameinterface.concommand

Example usage::

    @concommand('myconsolecommand')
    def MyConsoleCommand(args):
        print('Called myconsolecommand, arguments: %s' % (args.ArgS()))

-----------------------
AutoCompletion
-----------------------
.. autoclass:: gameinterface.AutoCompletion
    :members:

-----------------------
VEngineServer
-----------------------
.. autoclass:: gameinterface.VEngineServer
    :members:
    
-----------------------
VModelInfo
-----------------------
.. autoclass:: gameinterface.VModelInfo
    :members:
    
-----------------------
GameEventListener
-----------------------
.. autoclass:: gameinterface.GameEventListener
    :members:

-----------------------
GameEvent
-----------------------
.. autoclass:: gameinterface.GameEvent
    :members: