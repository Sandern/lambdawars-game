""" Game Notifications.

    A small system for registering notifications.
    A notificaton can be a text message in the hud, a sound or a signal on 
    the minimap for example (or all combined).
    
    This system also serves as an history to the most recent events.
    The player can use this to jump to the most recent event using the space bar.
"""
import gamemgr
from srcbuiltins import Color
from fields import GetField, StringField, BooleanField, FloatField, ColorField, LocalizedStringField
from core.abilities import GetAbilityInfo
from core.usermessages import usermessage
from core.factions import PlayFactionSound
from gameinterface import concommand, CRecipientFilter
from core.dispatch import receiver
from core.signals import prelevelinit
from utils import UTIL_ListForOwnerNumberWithDisp
from entities import Disposition_t
if isclient:
    from core.hud import DoInsertMessage, minimapflash
    from core.signals import FireSignalRobust
    from vgui import images
    from entities import C_HL2WarsPlayer
    
    from collections import deque
else:
    from utils import UTIL_PlayerByIndex
    
# Notifications db
dbid = 'notifications'
dbnotifications = gamemgr.dblist[dbid]

if isclient:
    notificationhistory = deque(maxlen=50)


class NotificationInfoMetaClass(gamemgr.BaseInfoMetaclass):
    def __new__(mcs, name, bases, dct):
        newcls = gamemgr.BaseInfoMetaclass.__new__(mcs, name, bases, dct)
        
        if isclient:
            # Get icon if any
            if newcls.iconname:
                newcls.icon = images.GetImage(newcls.iconname)
            
        return newcls


class NotificationInfo(gamemgr.BaseInfo, metaclass=NotificationInfoMetaClass):
    donotregister = False
    id = dbid
    
    #: Message displayed in notification hud (leave empty for no message)
    message = LocalizedStringField(value='', encoding='ascii')
    #: Color of message (default yellow)
    messagecolor = ColorField(value=Color(255, 255, 0, 255))
    #: Icon used by notification hud
    iconname = StringField(value='')
    #: Icon instance
    icon = None
    #: Faction sound played by notification
    factionsound = StringField(value='')
    #: Suppresses subsequent played faction sounds to prevent sound spam
    factionsounddelay = FloatField(value=4.0)
    #: Flashes the entity on the minimap
    minimapflashent = BooleanField(value=False)
    # Duration of flash
    minimapflashduration = FloatField(value=5.0)
    
    playedfactionsound = False
    
    def __init__(self, position=None, ent=None, abi=None, message=None):
        super().__init__()
        
        self.position = position
        self.ent = ent
        self.abi = abi
        if message:
            # TODO: Must do this automatically for localized fields using a property
            GetField(self, 'message').Set(self, message)
        
    @classmethod
    def FindLastOfType(cls, notinfo):
        for notification in notificationhistory:
            if type(notification) == notinfo:
                return notification
        return None
        
    @classmethod
    def FindLastFactionSoundOfType(cls, notinfo):
        for notification in notificationhistory:
            if type(notification) == notinfo and notification.playedfactionsound:
                return notification
        return None
    
    def DoNotification(self):
        self.timestamp = gpGlobals.curtime
        
        if self.message:
            DoInsertMessage(self, self.message, icon=self.icon, color=self.messagecolor)
            
        notinfo = self.FindLastFactionSoundOfType(type(self))
        if self.factionsound and (not notinfo or (gpGlobals.curtime - notinfo.timestamp > self.factionsounddelay)):
            PlayFactionSound(self.factionsound)
            self.playedfactionsound = True
            
        if self.position:
            pass
            
        if self.ent:
            if self.minimapflashent:
                FireSignalRobust(minimapflash, ent=self.ent, duration=self.minimapflashduration)
            
        # Insert in notification history
        notificationhistory.appendleft(self)
        
    def JumpToNotication(self, player):
        """ Snaps the player camera to the notifcation.
            Returns True on success, False if this is
            not possible for this notification.
        """
        if self.position:
            player.SnapCameraTo(self.position)
            return True
            
        if self.ent:
            player.SnapCameraTo(self.ent.GetAbsOrigin())
            return True
            
        return False
       
    def IsSameJump(self, notification):
        """ Tests if this notification jumps to the same location. """
        return self.position == notification.position and self.ent == notification.ent


def DoNotificationInternal(notification_name, **kwargs):
    notification_info = dbnotifications.get(notification_name, None)
    if not notification_info:
        PrintWarning('DoNotification: no notification %s!\n' % notification_name)
        return
        
    notinst = notification_info(**kwargs)
    notinst.DoNotification()


# Methods for usage
@usermessage(messagename='notification')
def DoNotification(notification_name, **kwargs):
    DoNotificationInternal(notification_name)


@usermessage(messagename='notificationpos')
def DoNotificationPos(notification_name, position, **kwargs):
    DoNotificationInternal(notification_name, position=position)


@usermessage(messagename='notificationent')
def DoNotificationEnt(notification_name, ent, **kwargs):
    DoNotificationInternal(notification_name, ent=ent)


@usermessage(messagename='notificationentabi')
def DoNotificationEntAbi(notification_name, ent, ability_name, **kwargs):
    DoNotificationInternal(notification_name, ent=ent, abi=GetAbilityInfo(ability_name))


@usermessage(messagename='notificationabi')
def DoNotificationAbi(notification_name, ability_name, message, **kwargs):
    DoNotificationInternal(notification_name, abi=GetAbilityInfo(ability_name), message=message)


if isclient:
    historyindex = 0
    lastjumptime = 0
    lastjumpnotification = None

    # Command for jumping to the most recent event
    @concommand('wars_jumptolastnotification')
    def CCJumpToLastNotification(args):
        global lastjumptime, historyindex, lastjumpnotification
        if not notificationhistory:
            return
            
        player = C_HL2WarsPlayer.GetLocalHL2WarsPlayer()
        if not player:
            return
            
        # Reset historyindex to the start if it was a while ago since the last jump
        if gpGlobals.curtime - lastjumptime > 2.5:
            historyindex = 0
            lastjumpnotification = None
            
        # Go through history until we find a notification to which we can jump
        for i in range(0, len(notificationhistory)):
            notification = notificationhistory[historyindex]
            
            historyindex += 1
            if historyindex >= len(notificationhistory):
                historyindex = 0
                
            # Skip this notification if it jumps to the last jump notification
            if lastjumpnotification and lastjumpnotification.IsSameJump(notification):
                continue
                
            # Try to jump to this notification
            # On Failure, continue to look for a valid jump
            if notification.JumpToNotication(player):
                lastjumptime = gpGlobals.curtime
                lastjumpnotification = notification
                break
                
    # Reset variables on level init
    @receiver(prelevelinit)
    def LevelInit(sender, **kwargs):
        global lastjumptime, historyindex, lastjumpnotification
        historyindex = 0
        lastjumptime = 0
        lastjumpnotification = None
        notificationhistory.clear()


# Helper to get target players for notifcation
def GetNotificationPlayersForOwner(owner):
    players = []
    for i in range(1, gpGlobals.maxClients+1):
        player = UTIL_PlayerByIndex(i)
        if player == None or not player.IsConnected():
            continue
        if player.IsObserver():
            continue
        if player.GetOwnerNumber() != owner:
            continue
        players.append(player)
    return players


def GetNotifcationFilterForOwner(owner):
    players = GetNotificationPlayersForOwner(owner)
    filter = CRecipientFilter()
    filter.MakeReliable()
    [filter.AddRecipient(p) for p in players]
    return filter


def GetNotifcationFilterForOwnerAndAllies(owner):
    players = UTIL_ListForOwnerNumberWithDisp(owner, d=Disposition_t.D_LI)
    filter = CRecipientFilter()
    filter.MakeReliable()
    [filter.AddRecipient(p) for p in players]
    return filter


# Core notifications
class NotificationAbilityCompleted(NotificationInfo):
    """ An ability was produced at a building (e.g. unit, upgrade). """
    name = 'ability_completed'
    message = '#Ability_Completed'
    
    def DoNotification(self):
        # Set variables based on ability
        if self.abi:
            self.factionsound = self.abi.producedfactionsound
            self.icon = self.abi.image
        
        # Do the actual notification
        super().DoNotification()


class NotificationNotEnoughPopulation(NotificationInfo):
    name = 'not_enough_population'
    message = '#Ability_NotEnoughPopulation'
    iconname = 'VGUI/icons/icon_population'
    factionsound = 'announcer_more_population_required'


class NotificationNotEnoughResources(NotificationInfo):
    name = 'not_enough_resources'
    message = '#Ability_NotEnoughResources'
    factionsound = 'announcer_combine_more_resources_required'


class NotificationInvalidMoveOrder(NotificationInfo):
    name = 'invalid_move_order'
    message = 'Order_InvalidMovePosition'
    iconname = 'VGUI/icons/icon_population'


class NotificationAbility(NotificationInfo):
    """ An ability was produced at a building (e.g. unit, upgrade). """
    name = 'ability'
    
    def DoNotification(self):
        # Set variables based on ability
        if self.abi:
            self.icon = self.abi.image
        
        # Do the actual notification
        super().DoNotification()
