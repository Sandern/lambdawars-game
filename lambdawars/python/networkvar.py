from collections import defaultdict
import types

def SetupNetworkVar(cls, name, networkvarname):
    """ Creates a property with the given name 
        Calls the setter of the network class which actually
        contains the data. """
    # Skip if the property is already setup
    try:
        p = getattr(cls, name)
        if type(p) == property:
            return
    except AttributeError:
        pass
        
    # Define the property
    getter = lambda self: getattr(self, networkvarname).Get()
    def setter(self, value):
        getattr(self, networkvarname).Set(value)
    p = property(getter, setter, None, '%s networkvar property' % (name))
    setattr(cls, name, p)

# SERVER
if isserver:
    from _entitiesmisc import NetworkVarInternal, NetworkArrayInternal, NetworkDictInternal

    class NetworkVar(NetworkVarInternal):
        def __init__(self, ent, name, data, changedcallback=None, sendproxy=None):
            super().__init__(ent, name, data, changedcallback=bool(changedcallback), sendproxy=sendproxy)
            networkvarname = '_networkvar_%s' % (name)
            setattr(ent, networkvarname, self)
            SetupNetworkVar(ent.__class__, name, networkvarname)
            
    class NetworkArray(NetworkArrayInternal):
        def __init__(self, ent, name, data=None, changedcallback=None, sendproxy=None):
            if data is None:
                data = list()
            super().__init__(ent, name, data, changedcallback=bool(changedcallback), sendproxy=sendproxy)
            setattr(ent, name, self)
            self.data = data
            
        def append(self, item):
            self.data.append(item)
            self.NetworkStateChanged()
        def remove(self, item):
            self.data.remove(item)
            self.NetworkStateChanged()
            
        # List methods
        def __contains__(self, item):
            return self.data.__contains__(item)
        def __len__(self):
            return self.data.__len__()
        def __iter__(self):
            return self.data.__iter__()
        def __concat__(self, other):
            return self.data.__concat__(other)
        def __add__(self, other):
            return self.data.__add__(other)
        def __sub__(self, other):
            return self.data.__sub__(other)
        def copy(self):
            return self.data.copy()
            
    class NetworkSet(NetworkVarInternal):
        def __init__(self, ent, name, data=None, changedcallback=None, sendproxy=None):
            if data is None:
                data = set()
            super().__init__(ent, name, data, changedcallback=bool(changedcallback), sendproxy=sendproxy)
            setattr(ent, name, self)
            self.data = data
            
        def add(self, item):
            self.data.add(item)
            self.NetworkStateChanged()
        def remove(self, item):
            self.data.remove(item)
            self.NetworkStateChanged()
        def discard(self, item):
            self.data.discard(item)
            self.NetworkStateChanged()
        def pop(self):
            item = self.data.pop()
            self.NetworkStateChanged()
            return item
        def clear(self):
            self.data.clear()
            self.NetworkStateChanged()
            
        def update(self, *args, **kwargs):
            self.data.update(*args, **kwargs)
            self.NetworkStateChanged()
        def intersection_update(self, *args, **kwargs):
            self.data.intersection_update(*args, **kwargs)
            self.NetworkStateChanged()
        def difference_update(self, *args, **kwargs):
            self.data.difference_update(*args, **kwargs)
            self.NetworkStateChanged()
        def symmetric_difference_update(self, *args, **kwargs):
            self.data.symmetric_difference_update(*args, **kwargs)
            self.NetworkStateChanged()
            
        # Set methods
        def __contains__(self, item):
            return self.data.__contains__(item)
        def __len__(self):
            return self.data.__len__()
        def __iter__(self):
            return self.data.__iter__()
        def __concat__(self, other):
            return self.data.__concat__(other)
        def __add__(self, other):
            return self.data.__add__(other)
        def __sub__(self, other):
            return self.data.__sub__(other)
        def copy(self):
            return self.data.copy()
            
            
    class NetworkDict(NetworkDictInternal):
        def __init__(self, ent, name, data=None, changedcallback=None, sendproxy=None):
            if data is None:
                data = dict()
            super().__init__(ent, name, data, changedcallback=bool(changedcallback), sendproxy=sendproxy)
            setattr(ent, name, self)
            self.data = data
            
        # TODO: missing dict methods?
        def __contains__(self, item):
            return self.data.__contains__(item)
        def __len__(self):
            return self.data.__len__()
        def __iter__(self):
            return self.data.__iter__()
            
        def keys(self):
            return self.data.keys()
        def values(self):
            return self.data.values()
        def items(self):
            return self.data.items()
        def has_key(self, key):
            return key in self.data
        def get(self, key, default=None):
            return self.data.get(key, default)
        def clear(self):
            return self.data.clear()
        def setdefault(self, key, default=None):
            return self.data.setdefault(key, default)
        def pop(self, key, default=None):
            return self.data.pop(key, default)
        def popitem(self):
            return self.data.popitem()
        def copy(self):
            return self.data.copy()
        def update(self, other=None):
            return self.data.update(other)
            
    class NetworkDefaultDict(NetworkDict):
        def __init__(self, ent, name, data=None, changedcallback=None, sendproxy=None, default=None):
            if type(default) != types.FunctionType:
                defaultvalue = default # Must rename!
                default = lambda: defaultvalue
            if data is None:
                data = defaultdict(default)
            elif type(data) != defaultdict:
                origdata = data
                data = defaultdict(default)
                data.update(origdata)
                
            super().__init__(ent, name, data, changedcallback=changedcallback, sendproxy=sendproxy)

# CLIENT
else:
    # NetworkVar has two purposes on the client:
    # 1. Initialize the default value
    # 2. Install the changed callback
    NetworkVar = None
    NetworkArray = None
    NetworkSet = None
    NetworkDict = None
    NetworkDefaultDict = None
        

def SetupNetworkVarProp(ent, name, propname):
    """ Creates a property for a propname networked variable. Basically an alias
        around a variable statically defined in C++.

        Args:
            ent (entity): instance of entity
            name (str): name of field
            propname (str): internal name of variable
    """
    cls = ent.__class__

    # Skip if the property is already setup
    try:
        p = getattr(cls, name)
        if type(p) == property:
            return
    except AttributeError:
        pass

    # Define the property
    getter = lambda self: getattr(self, propname)
    def setter(self, value):
        setattr(self, propname, value)
    p = property(getter, setter, None, '%s networkvar_prop property' % name)
    setattr(cls, name, p)
