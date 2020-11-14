from _cef import *
from srcbuiltins import RegisterTickMethod, UnregisterTickMethod, IsTickMethodRegistered
from vgui import surface, vgui_system
from gameinterface import concommand, ConVarRef, engine, CommandLine
from kvdict import LoadFileIntoDictionaries

import os
import traceback
import inspect

def jsbind(objname=None, hascallback=False, manuallycallback=False):
    """ Binds a Python method to a javascript object.
    
        Args:
            objname (str): name of global javascript object to bind to

        Kwargs:
            hascallback (bool): Made callback to js method with returned parameters
            manuallycallback (bool): Indicates binding has callback, but is not automatically called.
                                     Can be used to delay the call.
    """
    def dojsbind(fn):
        setattr(fn, 'jsbound', True)
        fn.objname = objname
        fn.hascallback = hascallback
        fn.manuallycallback = manuallycallback
        return fn
    return dojsbind
    
class WebViewComponent(object):
    """ Component for web views, allowing js bindings to be moved out of the main
        web view class. """
    #: Default global javascript object for binding js methods
    defaultobjectname = None
    
    def __init__(self, webview):
        super().__init__()
        
        self.webview = webview
        
    def InitializeObjects(self):
        pass
    def OnInitializedBindings(self):
        pass
        
    def OnDestroy(self):
        pass
        
    def CreateGlobalObject(self, *args, **kwargs):
        self.webview.CreateGlobalObject(*args, **kwargs)

    def CreateFunction(self, *args, **kwargs):
        self.webview.CreateFunction(*args, **kwargs)

    def SendCallback(self, *args, **kwargs):
        self.webview.SendCallback(*args, **kwargs)

    def ExecuteJavaScript(self, *args, **kwargs):
        self.webview.ExecuteJavaScript(*args, **kwargs)

    def ExecuteJavaScriptWithResult(self, *args, **kwargs):
        self.webview.ExecuteJavaScriptWithResult(*args, **kwargs)

    def Invoke(self, *args, **kwargs):
        self.webview.Invoke(*args, **kwargs)

    def InvokeWithResult(self, *args, **kwargs):
        self.webview.InvokeWithResult(*args, **kwargs)


def GetUILanguage():
    engine_language = engine.GetUILanguage()
    if CommandLine().CheckParm('-language'):
        return CommandLine().ParmValue('-language', engine_language)
    success, language = vgui_system().GetRegistryString('HKEY_CURRENT_USER\\Software\\Valve\\Steam\\Language')
    if success:
        return language
    return engine_language


# This class should be merged into WebView and Viewport should use WebView class
# However this also requires updating/checking the different hud elements making use of it.
class WebViewShared(SrcCefBrowser):
    def GetGameUITranslations(self):
        language = GetUILanguage()
        translations_file = os.path.join('resource', 'lambdawars_ui_%s.txt' % language)
        translations = LoadFileIntoDictionaries(translations_file, default={})
        if not translations:
            english_translations_file = os.path.join('resource', 'lambdawars_ui_english.txt')
            translations = LoadFileIntoDictionaries(english_translations_file, default={})
        return translations.get('Tokens', {})


class WebView(WebViewShared):
    """ Generic web view for displaying a web page. """
    #: Default global javascript object for binding js methods
    defaultobjectname = None
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.jsglobals = {}
        self.jsmethods = {}
        self.components = []
        
    def OnLoadStart(self, frame):
        super().OnLoadStart(frame)
        
        if not frame.IsMain():
            return
        
    def OnLoadEnd(self, frame, httpStatusCode):
        super().OnLoadEnd(frame, httpStatusCode)

        if not frame.IsMain():
            return
            
        # Don't clear these variables until load ended, in case it's a "fake" load (e.g. due routers)
        self.jsglobals = {}
        self.jsmethods = {}
        
        self.InitializeBindings(frame)
        
    def OnDestroy(self):
        ''' Called when the web view is completely destroyed. '''
        super().OnDestroy()
        
        for obj in self.components:
            obj.OnDestroy()
        
    def InitializeObjects(self):
        pass
        
    def InitializeBindings(self, frame):
        # Only want to do this for the main frame
        if not frame.IsMain():
            return
    
        # Already initialized?
        if self.jsmethods:
            return
            
        self.InitializeObjects() # Create global js objects
        [comp.InitializeObjects() for comp in self.components]
            
        for obj in [self] + self.components:
            for name, fn in inspect.getmembers(obj, predicate=inspect.ismethod):
                if not getattr(fn, 'jsbound', False):
                    continue
                    
                # Find to which global object this method should be bound
                objname = fn.objname if fn.objname != None else obj.defaultobjectname
                assert objname != None, 'js binding %s has no object to bind to' % (name)
                
                # Auto create it if it does not exists yet
                if objname not in self.jsglobals:
                    self.CreateGlobalObject(objname)
                    
                # Create and bind the method
                obj.CreateFunction(fn, self.jsglobals[objname], callback=fn.hascallback,
                            manuallycallback=fn.manuallycallback)
                        
        self.OnInitializedBindings()
        [comp.OnInitializedBindings() for comp in self.components]
        
    def OnInitializedBindings(self):
        pass
        
    def CreateGlobalObject(self, name, *args, **kwargs):
        obj = super().CreateGlobalObject(name, *args, **kwargs)
        self.jsglobals[name] = obj
        return obj
        
    def CreateFunction(self, fn, obj, callback=False, manuallycallback=False):
        jsfn = super().CreateFunction(fn.__name__, obj, callback)
        jsfn.fn = fn
        jsfn.manuallycallback = manuallycallback
        self.jsmethods[jsfn.identifier] = jsfn
        return jsfn
        
    def OnMethodCall(self, identifier, methodargs, callbackid):
        jsobj = self.jsmethods.get(identifier, None)
        if jsobj:
            fn = jsobj.fn
            if fn.manuallycallback:
                fn(methodargs, callbackid)
            elif callbackid != None:
                callbackargs = fn(methodargs)
                self.SendCallback(callbackid, [callbackargs] if type(callbackargs) != list else callbackargs)
            else:
                fn(methodargs)
            return True
        PrintWarning('WebView.OnMethodCall: Could not find method with identifier %s\n' % (identifier))
        return False

class Viewport(WebViewShared):
    htmlfile = 'local://localhost/ui/viewport/viewport.html'

    gameui_obj_name = 'interface'

    def __init__(self, *args, **kwargs):
        wide, tall = surface().GetScreenSize()
        
        super().__init__('CefViewPort', self.htmlfile, wide=wide, tall=tall)
        
        self.SetIgnoreTabKey(True)
        self.SetPassMouseTruIfAlphaZero(True)
        
        self.panels = []
        self.objects = {}
        
        self.delayedelements = []

    def Load(self):
        self.LoadURL(self.htmlfile)
        
    def OnSizeChanged(self, newwidth, newtall):
        self.ReloadViewport()

    def PerformLayout(self):
        w, h = surface().GetScreenSize()
        self.SetSize(w, h)
        
    def OnLoadStart(self, frame):
        super().OnLoadStart(frame)
        
        if not frame.IsMain():
            return
    
        self.ready = False
        
        # Move any existing panel over to the list of to be initialized panels, so they will
        # get added again to the viewport
        self.delayedelements.extend(list(self.panels))
        self.panels = []
        
    def OnLoadEnd(self, frame, httpStatusCode):
        super().OnLoadEnd(frame, httpStatusCode)
    
        if not frame.IsMain():
            return
    
        self.SetMouseInputEnabled(True)
        self.SetGameInputEnabled(True)
        self.SetUseMouseCapture(True)
        self.SetZPos(-10)
        self.Focus()
        
        self.ready = True
        
        # Create default functions
        self.objpanel = self.CreateGlobalObject('panel')
        self.CreateFunction('close', self.objpanel, False)
        self.CreateFunction('setVisible', self.objpanel, False)
        
        self.objinterface = self.CreateGlobalObject(self.gameui_obj_name)
        self.clientCommand = self.CreateFunction('clientCommand', self.objinterface, False)
        self.serverCommand = self.CreateFunction('serverCommand', self.objinterface, False)
        self.gettranslations = self.CreateFunction('gettranslations', self.objinterface, True)
        self.retrieveConVarValue = self.CreateFunction('retrieveConVarValue', self.objinterface, True)
        
        self.setCefFocus = self.CreateFunction('setCefFocus', self.objinterface, False)
        self.reloadElements = self.CreateFunction('reloadElements', self.objinterface, False)

        self.Invoke(None, 'init_viewport', [self.GetGameUITranslations()])
        
        for e in self.delayedelements:
            self.AddElement(e)
        self.delayedelements = []
        
    def KeyInput(self, down, keynum, currentbinding):
        #print('Down: %s, keynum: %s, binding: %s' % (down, keynum, currentbinding))
        ret = 1
        for e in self.panels:
            if not e.visible:
                continue
            ret = e.KeyInput(down, keynum, currentbinding)
            if ret == 0:
                break
        return ret
        
    def OnMethodCall(self, identifier, methodargs, callbackid):
        for p in self.panels:
            if identifier in p.jsmethods:
                jsobj = p.jsmethods[identifier]
                fn = getattr(p, jsobj.name)
                if callbackid != None:
                    callbackargs = fn(methodargs, callbackid)
                    self.SendCallback(callbackid, [callbackargs])
                else:
                    fn(methodargs, callbackid)
                return True
                
        if self.serverCommand.identifier == identifier:
            engine.ServerCommand(methodargs[0])
            return True
        elif self.clientCommand.identifier == identifier:
            engine.ClientCommand(methodargs[0])
            return True
        elif self.gettranslations.identifier == identifier:
            if callbackid != None:
                self.SendCallback(callbackid, [self.GetGameUITranslations()])
            return True
        elif self.retrieveConVarValue.identifier == identifier:
            if callbackid != None:
                ref = ConVarRef(methodargs[0])
                self.SendCallback(callbackid, [ref.GetString()])
            return True
        elif self.setCefFocus.identifier == identifier:
            CEFSystem().SetFocus(methodargs[0])
            return True
        elif self.reloadElements.identifier == identifier:
            print('Reload viewport elements requested')
            return True
            
        return super().OnMethodCall(identifier, methodargs, callbackid)
        

    def ReloadViewport(self):
        self.ReloadIgnoreCache()
        
    def AddElement(self, e):
        # Don't add elements until the context is created
        if not self.ready:
            self.delayedelements.append(e)
            return
            
        if not e.name:
            PrintWarning('Discarding panel "%s". Name is required.\n' % (e))
            return
            
        DevMsg(1, 'Adding element %s\n' % (str(e.name)))
        
        # Reset in case we are being reloaded
        e.isloaded = False
        
        e.LoadCode()
    
        # Setup default methods
        e.obj = self.CreateGlobalObject('%s_obj' % (e.name))
        e.CreateFunction('retrieveCSSFiles', True)
        e.CreateFunction('onElementCreated', False)
        e.CreateFunction('onFinishedLoading')
        e.CreateFunction('onSetVisible', False)
        
        e.SetupFunctions()
        
        self.objects[e.obj.identifier] = e
        
        self.panels.append(e)
        
        # Insert and setup
        try:
            self.InvokeWithResult(None, 'insertElement', [e.classidentifier, e.name, e.GetConfig()])
        except ValueError:
            traceback.print_exc()
            return

        # Finalize
        e.visible = False # Always start invisible

    def RemoveElement(self, e):
        assert(e.element)
        
        self.panels.remove(e)
        self.ExecuteJavaScript("removeElement('%s');" % (e.name), '')
        
    def InsertCSSFile(self, filename):
        self.ExecuteJavaScript("insertCss('%s');" % (filename), '')
        
    ready = False
    nextid = 0

class CefPanel(object):
    name = ''
    htmlfile = ''
    cssfiles = []
    element = None
    obj = None
    selfref = None
    _visible = False
    
    #: Indicates the panel is loaded in the viewport
    isloaded = False
    #: Dojo class identifier
    classidentifier = ''
    #: Configuration passed to javascript for initialization
    defaultconfig = {
        'visible' : False,
    }
    
    def __init__(self, viewport, name='', htmlfile=None):
        super().__init__()

        if htmlfile: 
            self.htmlfile = htmlfile
        
        if name:
            self.name = name
        self.viewport = viewport
        
        self.jsmethods = {}

        viewport.AddElement(self)
        
        self.selfref = self
        
    def GetConfig(self):
        ''' Dictionary passed as config to javascript, used for initializing. '''
        config = dict(self.defaultconfig)
        config['visible'] = self.visible # In case reloaded, restore the visible state by default
        config['htmlcode'] = self.htmlcode
        return config

    def Remove(self):
        self.OnRemove()
    
        self.UnregisterTickSignal()
        viewport.RemoveElement(self)
        self.selfref = None
        
    def OnRemove(self):
        pass
        
    def LoadCode(self):
        try:
            fp = open(self.htmlfile, 'rt')
            self.htmlcode = fp.read()
            fp.close()
        except IOError:
            PrintWarning('%s: invalid html file specified (%s)\n' % (self.name, self.htmlfile))
            self.htmlcode = ''
            
    def SetupFunctions(self):
        pass
            
    def CreateFunction(self, methodname, callback=False):
        fn = self.viewport.CreateFunction(methodname, self.obj, callback)
        self.jsmethods[fn.identifier] = fn
        
    def OnLoaded(self):
        pass
        
    def Invoke(self, *args, **kwargs):
        self.viewport.Invoke(self.element, *args, **kwargs)
        
    def InvokeWithResult(self, *args, **kwargs):
        return self.viewport.InvokeWithResult(self.element, *args, **kwargs)
        
    @property
    def visible(self):
        return self._visible
    
    @visible.setter
    def visible(self, visible):
        if self.isloaded:
            self.Invoke('setVisible', [visible])
        self._visible = visible
        
    def KeyInput(self, down, keynum, currentbinding):
        return 1
        
    def ReplaceContent(self, htmlcode):
        self.Invoke('replaceContent', [htmlcode])
        
    # Convenient tick method
    def OnTick(self):
        pass
       
    def RegisterTickSignal(self, interval):
        if not IsTickMethodRegistered(self.OnTick):
            RegisterTickMethod(self.OnTick, interval)
        
    def UnregisterTickSignal(self):
        if IsTickMethodRegistered(self.OnTick):
            UnregisterTickMethod(self.OnTick)
        
    # JS Methods
    cssid = 0
    def retrieveCSSFiles(self, methodargs, callbackid):
        CefPanel.cssid += 1 # Hack to force load (for developing)
        return list(map(lambda f: f + '?x=%d' % (CefPanel.cssid), self.cssfiles))
        
    jsid = 0
    def retrieveJSFiles(self, methodargs, callbackid):
        CefPanel.jsid += 1 # Hack to force load (for developing)
        return list(map(lambda f: os.path.abspath(f) + '?x=%d' % (CefPanel.jsid), self.jsfiles))
        
    def onElementCreated(self, methodargs, callbackid):
        element = methodargs[0]
        name = methodargs[1]
        # TODO: Support passing a js object identifier by argument from javascript
        # For now, just call another method to get the actual argument as return value
        self.element = self.viewport.InvokeWithResult(None, 'getElement', [self.name])
        #print('Element created %s: %s' % (name, self.element))
        
    def onFinishedLoading(self, methodargs, callbackid):
        self.isloaded = True
        self.OnLoaded()
        
    def onSetVisible(self, methodargs, callbackid):
        self._visible = methodargs[0]


class CefHudPanel(CefPanel):
    def __init__(self, name=''):
        if not name and not self.name:
            name = self.__class__.__name__
        super().__init__(viewport, name)


# Create the default viewport
viewport = Viewport()

@concommand('viewport_reload')
def CCReloadViewport(args):
    viewport.ReloadViewport()
    
@concommand('viewport_show_devtools')
def CCViewPortShowDevTools(args):
    viewport.ShowDevTools()
    
@concommand('viewport_debuginfo')
def CCViewportDebugInfo(args):
    for i, e in enumerate(viewport.panels):
        print('%d Panel %s' % (i, e.name))
        
@concommand('viewport_run')
def CCViewportRun(args):
    viewport.ExecuteJavaScript(args.ArgS(), '')
    
@concommand('cef_open_window')
def CCCefOpenWindow(args):
    command = args.ArgS()
    print('command: %s' % (command))
    viewport.ExecuteJavaScript('window.open("%s");' % (command), '')
