from srcbase import KeyValues
from cef import viewport, CefPanel
from vgui import GetClientMode, scheme, DataType_t, ipanel
from vgui.controls import Frame, Button, Label, TextEntry, ListPanel, ComboBox, PropertySheet, TreeView
from gameinterface import engine, concommand
from input import ButtonCode

from core.units import GetUnitInfo
from core.abilities import GetAbilityInfo
from core.dispatch import receiver
from core.signals import gamepackageloaded, gamepackageunloaded

import playermgr
from fields import BaseField

from core.attributemgr_shared import IsAttributeFiltered, ReqAttrFilterFlags

import random
from operator import itemgetter

# Helper
def ShowTool(tool, show):
    if not show:
        tool.SetVisible(False)
        tool.SetEnabled(False)  
    else:
        tool.SetVisible(True)
        tool.SetEnabled(True)   
        tool.RequestFocus()
        tool.MoveToFront()
        
@receiver(gamepackageloaded)
@receiver(gamepackageunloaded)
def OnGamePackageChanged(sender, packagename, **kwargs):
    unitpanel.OnGamePackageChanged(packagename)
    abilitypanel.OnGamePackageChanged(packagename)
    attributemodifiertool.OnGamePackageChanged(packagename)
    
# 
# New CEF panels
#
class CefUnitPanel(CefPanel):
    htmlfile = 'ui/viewport/tools/unitpanel.html'
    cssfiles = CefPanel.cssfiles + ['tools/tools.css']
    classidentifier = 'viewport/editor/UnitPanel'
    
    def SetupFunctions(self):
        super(CefUnitPanel, self).SetupFunctions()
        
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super(CefUnitPanel, self).GetConfig()
        config['units'] = self.BuildUnitList()
        return config
        
    def OnGamePackageChanged(self, package_name):
        if not self.isloaded:
            return
        self.LoadUnits()
    
    def SetEnabled(self, enabled):
        pass
    def RequestFocus(self):
        pass
    def MoveToFront(self):
        pass
        
    def BuildUnitList(self):
        from core.units.info import dbunits
        return [ unit.name for unit in dbunits.values() if not unit.hidden ]
        
    def LoadUnits(self):
        self.Invoke("clearList", [])
        units = self.BuildUnitList()
        self.Invoke("addUnits", [units])
        
    def KeyInput(self, down, keynum, currentbinding):
        if keynum == ButtonCode.KEY_SPACE:
            if down:
                self.Invoke("onSpacePressed", [])
                self.RegisterTickSignal(0.08)
                self.startrepeattime = gpGlobals.curtime + 0.4
            else:
                self.UnregisterTickSignal()
            return 0
        return 1
        
    def OnTick(self):
        if self.startrepeattime > gpGlobals.curtime:
            return
        # Tick method only used for spawning when holding down the key
        self.Invoke("onSpacePressed", [])
        
    startrepeattime = 0
    
unitpanel = CefUnitPanel(viewport, 'unitpanel')

@concommand('unitpanel', 'Show up a panel to create units (cheats)', 0)
def cc_show_unitpanel(args):
    unitpanel.visible = not unitpanel.visible
    
class CefAbilityPanel(CefPanel):
    htmlfile = 'ui/viewport/tools/abilitypanel.html'
    cssfiles = CefPanel.cssfiles + ['tools/tools.css']
    classidentifier = 'viewport/editor/AbilityPanel'
    
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super(CefAbilityPanel, self).GetConfig()
        config['abilities'] = self.BuildAbilitiesList()
        return config

    def OnGamePackageChanged(self, package_name):
        if not self.isloaded:
            return
        self.LoadAbilities()
    
    def BuildAbilitiesList(self):
        from core.abilities.info import dbabilities
        return [ abi.name for abi in dbabilities.values() if not abi.hidden ]
        
    def LoadAbilities(self):
        self.viewport.Invoke(self.element, "clearList", [])
        abilities = self.BuildAbilitiesList()
        self.viewport.Invoke(self.element, "addAbilities", [abilities])
        
    def KeyInput(self, down, keynum, currentbinding):
        if keynum == ButtonCode.KEY_SPACE:
            if down:
                self.viewport.Invoke(self.element, "onSpacePressed", [])
                self.RegisterTickSignal(0.08)
                self.startrepeattime = gpGlobals.curtime + 0.4
            else:
                self.UnregisterTickSignal()
            return 0
        return 1
        
    def OnTick(self):
        if self.startrepeattime > gpGlobals.curtime:
            return
        # Tick method only used for spawning when holding down the key
        self.viewport.Invoke(self.element, "onSpacePressed", [])
        
    startrepeattime = 0
    
abilitypanel = CefAbilityPanel(viewport, 'abilitypanel')

@concommand('abilitypanel', 'Show up a panel to create abilities (cheats)', 0)
def cc_show_abilitypanel(args):
    abilitypanel.visible = not abilitypanel.visible
    
class CefAttributePanel(CefPanel):
    htmlfile = 'ui/viewport/tools/attributepanel.html'
    cssfiles = CefPanel.cssfiles + ['tools/tools.css']
    classidentifier = 'viewport/editor/AttributePanel'

    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = super(CefAttributePanel, self).GetConfig()
        config['abilities'] = self.BuildAbilitiesList()
        return config
        
    def OnGamePackageChanged(self, package_name):
        if not self.isloaded:
            return
        self.LoadAbilities()
        
    def SetupFunctions(self):
        super(CefAttributePanel, self).SetupFunctions()
        
        self.CreateFunction('getAttributes', True)
        
    def BuildAbilitiesList(self):
        from core.abilities.info import dbabilities
        data = []
        for abi in dbabilities.values():
            data.append({
                'name' : abi.name,
            })
        data.sort(key=itemgetter('name'))
        return data
        
    def LoadAbilities(self):
        self.viewport.Invoke(self.element, "clearList", [])
        abilities = self.BuildAbilitiesList()
        self.viewport.Invoke(self.element, "addAbilities", [abilities])
        
    def ClearAttributes(self, tabname):
        self.viewport.Invoke(self.element, "clearAttrList", [tabname])
        
    def SetAttribute(self, tabname, fieldname, value):
        self.viewport.Invoke(self.element, "addAttribute", [tabname, {
            'attribute' : fieldname, 
            'value' : str(value)
        }])
        
    def LoadAttributesFromObject(self, object, filterflags=0):
        attributes =[]
        for k, v in object.__dict__.iteritems():
            if not isinstance(v, BaseField):
                continue
            if IsAttributeFiltered(k, v, filterflags):
                continue
            attributes.append({
                'attribute' : v.name,
                'value' : str(v.Get(object, allowdefault=True)),
            })
        return attributes
        
    def getAttributes(self, methodargs, callbackid):
        abiname = methodargs[0]
        abiinfo = GetAbilityInfo(abiname)
        if not abiinfo:
            return []
        
        return self.LoadAttributesFromObject(abiinfo)
        
attributemodifiertool = CefAttributePanel(viewport, 'attributepanel')

@concommand('attributemodifiertool', 'Show a panel to modify attributes of an unit class or instance', 0)
def show_attributemodifiertool(args):
    attributemodifiertool.visible = not attributemodifiertool.visible
