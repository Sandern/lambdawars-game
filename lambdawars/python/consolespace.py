'''
Module space used in the "spy" and "cpy" console commands.

Import anything here you want to be available by default in these commands.
'''
import os
import sys
from vmath import *
from gameinterface import engine, ConVarRef
from imp import reload

from core.dispatch import receiver
from core.signals import playerspawned
import entities
from entities import entlist, CBasePlayer
from utils import *
if isclient:
    from entities import ClientEntityList
    from gameui import GetMainMenu
from gamerules import GameRules, gamerules
from steam import steamapicontext

# Set variables
@receiver(playerspawned)
def __PlayerSpawned(sender, **kwargs):
    global player
    client = kwargs.pop('player')
    if client.entindex() == 1:
        player = client
