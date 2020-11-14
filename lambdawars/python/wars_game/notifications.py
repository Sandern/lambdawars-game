from srcbase import Color
from core.notifications import NotificationInfo

class NotificationControlPointCaptured(NotificationInfo):
    name = 'cp_captured'
    message = '#Noti_CPCaptured'
    messagecolor = Color(0, 255, 0, 255)
    iconname = 'VGUI/icons/icon_control_point_captured'
    factionsound = 'announcer_cp_captured'
    minimapflashent = True
    
class NotificationControlPointLost(NotificationInfo):
    name = 'cp_lost'
    message = '#Noti_CPLost'
    messagecolor = Color(255, 0, 0, 255)
    iconname = 'VGUI/icons/icon_control_point_lost'
    factionsound = 'announcer_cp_lost'
    minimapflashent = True
    
class NotificationControlPointUnderAttack(NotificationInfo):
    name = 'cp_underattack'
    message = '#Noti_CPUnderAttack'
    messagecolor = Color(255, 0, 0, 255)
    iconname = 'VGUI/icons/icon_control_point_lost'
    factionsound = 'announcer_cp_under_attack'
    minimapflashent = True