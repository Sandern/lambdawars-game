from srcbase import KeyValues
from steam import CSteamID, steamapicontext, EUniverse, k_EAccountTypeIndividual
from gameinterface import engine, PlayerInfo
from utils import ScreenWidth, ScreenHeight
from input import MOUSE_LEFT
from vgui import surface
from vgui.controls import AvatarImage
from .imagepanel import ImagePanel
from entities import C_BasePlayer
    
class AvatarImagePanel(ImagePanel):
    def __init__(self, parent, name):
        super(AvatarImagePanel, self).__init__(parent, name)
        
        self.scaleimage = False
        self.image = AvatarImage()
        self.sizedirty = True
        self.clickable = False

    def SetPlayer(self, player, avatarSize):
        ''' Set the avatar by C_BasePlayer pointer, or
            set the avatar by entity number, or 
            set the avatar by SteamID '''
        if isinstance(player, C_BasePlayer):
            if player:
                iIndex = player.entindex()
                SetPlayer(iIndex, avatarSize)
            else:
                self.image.ClearAvatarSteamID()
        elif type(player) == int:
            entindex = player
            
            self.image.ClearAvatarSteamID()

            pi = PlayerInfo()
            if engine.GetPlayerInfo(entindex, pi):
                if pi.friendsID != 0 and steamapicontext.SteamUtils():
                    steamIDForPlayer = CSteamID( pi.friendsID, 1, steamapicontext.SteamUtils().GetConnectedUniverse(), k_EAccountTypeIndividual )
                    self.SetPlayer(steamIDForPlayer, avatarSize)
                else:
                    self.image.ClearAvatarSteamID()
        else:
            steamIDForPlayer = player
            
            self.image.ClearAvatarSteamID()

            if steamIDForPlayer.GetAccountID() != 0:
                self.image.SetAvatarSteamID( steamIDForPlayer, avatarSize )

    def PaintBackground(self):
        if self.sizedirty:
            self.UpdateSize()

        self.image.Paint()

    def ClearAvatar(self):
        self.image.ClearAvatarSteamID()

    def SetDefaultAvatar(self, pDefaultAvatar):
        self.image.SetDefaultImage(pDefaultAvatar)

    def SetAvatarSize(self, width, height):
        if self.scaleimage:
            assert False, 'panel is charge of image size - setting avatar size this way not allowed'
            return
        else:
            self.image.SetAvatarSize(width, height)
            self.sizedirty = True

    def OnSizeChanged(self, newWide, newTall):
        super(AvatarImagePanel, self).OnSizeChanged(newWide, newTall)
        self.sizedirty = True

    def OnMousePressed(self, code):
        if not self.clickable or code != MOUSE_LEFT:
            return

        self.PostActionSignal(KeyValues("AvatarMousePressed"))

        # audible feedback
        soundFilename = "ui/buttonclick.wav"

        surface().PlaySound(soundFilename)

    def SetShouldScaleImage(self, bScaleImage):
        self.scaleimage = bScaleImage
        self.sizedirty = True

    def SetShouldDrawFriendIcon(self, bDrawFriend):
        self.image.SetDrawFriend(bDrawFriend)
        self.sizedirty = True

    def UpdateSize(self):
        if self.scaleimage:
            # the panel is in charge of the image size
            self.image.SetAvatarSize(self.GetWide(), self.GetTall())
        else:
            # the image is in charge of the panel size
            self.SetSize(self.image.GetAvatarWide(), self.image.GetAvatarTall())
            
        self.sizedirty = False

    def ApplySettings(self, inResourceData):
        self.scaleimage = inResourceData.GetInt("scaleImage", 0)

        super(AvatarImagePanel, self).ApplySettings(inResourceData)
    
