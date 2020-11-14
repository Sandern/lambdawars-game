"""
The field classes serve multiple purposes.
They define some more info about the used types. The attribute editor will use these to provide the user with easier to use options.
Fields can also be written back to file in case of class info.
In case of entities we can use them to define keyvalues or add save/restore functionality (single player).
"""
from srcbuiltins import Color
from vmath import Vector, QAngle
from core.dispatch import receiver
from core.signals import postlevelshutdown
import inspect
from readmap import StringToVector, StringToAngle, StringToColor
import copy
import weakref
import ast
from collections import defaultdict
import traceback
from networkvar import NetworkVar, NetworkArray, NetworkSet, NetworkDict, NetworkDefaultDict, SetupNetworkVarProp

from _entities import PyHandle
from _entitiesmisc import _fieldtypes as fieldtypes
if isserver:
    from _entitiesmisc import COutputEvent, variant_t

if isclient:
    from vgui import localize

# A small helper for fgd help string generation
def _escape_helpstring(helpstring):
    return helpstring.replace('"', '\'')

# List of weak refs to all fields
# Used for resetting all fields to the defaults
fields = []

# Base field types
# Note: In case function names change, also update the CBaseEntity::KeyValue function.
class BaseField(object):
    """ Base class for fields.
        All fields should derive from this class."""
    def __init__(self, value=None, 
                       keyname=None, 
                       noreset=False, 
                       networked=False, 
                       clientchangecallback=None,
                       sendproxy=None,
                       propname='',
                       displayname='',
                       helpstring='',
                       nofgd=False,
                       cppimplemented=False,
                       choices=None,
                       save=True):
        """ Initializes the field.
        
            Kwargs:
               value (object): the default value
               keyname (string): the key name used to refer to this entity in Hammer (entities only), used by fgd generation.
               noreset (bool): prevents field from being reset on map change.
               networked (bool): if this field is networked for an entity (i.e. synced to the clients).
               clientchangecallback (methodname): callback on client if networked and the value changed.
               sendproxy (object): send proxy used if networked.
               propname (string): 
               displayname (string): Display name used in Hammer.
               helpstring (string): Help string used in Hammer.
               nofgd (bool): prevents fgd entry from being generated for this field.
               cppimplemented (bool): if implemented in c++. In this case it won't set the attribute on the instances of the object.
               choices (list): List of choices to be displayed in Hammer or attribute editor. Each choice is a tuple of the value and display name.
               save (bool): Whether or not to save this field in single player
        """
        super().__init__()

        self.wrefsclasses = set()
        self.default = value
        self.keyname = keyname
        self.noreset = noreset or cppimplemented
        self.networked = networked
        self.propname = propname
        self.clientchangecallback = clientchangecallback
        self.sendproxy = sendproxy
        self.requiresinit = self.requiresinit or networked
        self.displayname = displayname
        self.helpstring = helpstring
        self.nofgd = nofgd
        self.cppimplemented = cppimplemented
        self.choices = choices
        self.save = save and not cppimplemented
        
        assert not self.propname or not self.clientchangecallback, 'Cannot mix propname and clientchangecallback'
        
    def Parse(self, cls, name):
        """ Field parser method. To be used in the Meta Class or similar place to setup the fields on a class.

            Args:
                cls (object): Class on which the parse the field.
                name (str): Name of field
        """
        global fields
        self.name = name
        fields.append(weakref.ref(self))
        
        # Store the field instance and a weak class reference
        setattr(cls, '__%s_fieldinfo' % name, self)
        self.wrefsclasses.add(weakref.ref(cls))

        # clientchangecallback is the real method, but entity code calls it by '__%s__Changed' % (name)
        if isclient and self.clientchangecallback:
            assert self.networked, 'clientchangecallback only makes sense for networked fields'
            assert not self.propname, 'clientchangecallback is not supported for propname argument'
            setattr(cls, '__%s__Changed' % name, getattr(cls, self.clientchangecallback))
        
        if not self.cppimplemented:
            # Set the default value to the class object
            self.Set(cls, self.default)
        else:
            # Implemented in c++, so just delete the field reference from the class
            # This way it should pick up the c++ implemented variable
            if name in cls.__dict__:
                delattr(cls, name)
        
    def InitField(self, inst):
        """ Called if requiresinit is True and new instance is created.
            Used to initialize dicts and lists correctly for an instance.

            Args:
                inst (object): instance of object
        """
        if self.networked:
            if self.propname:
                SetupNetworkVarProp(inst, self.name, self.propname)
            elif isserver:
                # Client does not need to be setup, only create an alias during the one time parsing for the class for the changed callback
                NetworkVar(inst, self.name, self.default, changedcallback=self.clientchangecallback, sendproxy=self.sendproxy)
                
    def GenerateFGDDefaultValue(self):
        """ Generates the default value for the fgd entry.
            The default is the value double quoted.

            Returns:
                str: default value for fgd
        """
        return '"%s"' % self.default
            
    def GenerateFGDProperty(self):
        """ Generates the fgd entry for this field.

            Returns:
                str: fgd entry
        """
        displayname = self.displayname if self.displayname else self.keyname
        if self.choices:
            entry = '%s(choices) : "%s" : %s : "%s" =\n\t[\n' % (self.keyname, displayname, self.GenerateFGDDefaultValue(), self.helpstring)
            for value, choicename in self.choices:
                value = str(int(value)) if self.fgdtype == 'integer' else '"%s"' % (value)
                entry += '\t\t%s : "%s"\n' % (value, choicename)
            entry += '\t]'
            return entry
        else:
            return '%(keyname)s(%(type)s)%(readonly)s: "%(displayname)s" : %(default)s : "%(helpstring)s"' % {
                'keyname': self.keyname,
                'type': self.fgdtype,
                'default': self.GenerateFGDDefaultValue(),
                'readonly': ' readonly' if self.fgdreadonly else '',
                'displayname': displayname,
                'helpstring': _escape_helpstring(self.helpstring),
            }
                
    def OnChangeOwnerNumber(self, inst, oldownernumber):
        pass
        
    def Reset(self):
        """ Reset value to default. 
        
            This is used in case the user changed a value with the attribute editor or
            when the game changed values during a game (like increasing hp or dmg of units).
        """
        if self.noreset:
            return
        for clswref in self.wrefsclasses:
            self.Set(clswref(), self.default)
        
    def Copy(self):
        """ Makes a copy of this field. This is used for creating fields in subclasses. """
        cpy = copy.copy(self)
        cpy.wrefsclasses = set()
        if type(cpy.choices) == list: 
            cpy.choices = list(cpy.choices)
        return cpy
        
    def Verify(self, value):
        """ Verify user input.

            Args:
                value (str): value to verify
        """
        try:
            self.ToValue(value)
        except:
            errmsg = '%s => Value "%s" is not a valid "%s":\n%s' % (self.name, value, self.__class__.__name__, traceback.format_exc())
            #errmsg = errmsg.encode('ascii', errors='ignore')
            raise ValueError(errmsg)
        
    def ToValue(self, rawvalue):
        """ Convert value to right type.
            Will return the same value if already correct.
            This method can also be used to convert the value to something else.
        """
        return rawvalue
        
    def ToString(self, value):
        """ Convert value to string representation """
        return str(value)

    def ToJSON(self, value):
        """ Converts to JSON representation. Defaults using ToString.

            Args:
                value (object): Field value to convert.
        """
        return self.ToString(value)

    def FromJSON(self, value):
        """ Converts from JSON value to field value. Defaults to using ToValue

            Args:
                value (object): JSON value to convert.
        """
        return self.ToValue(value)

    # Getters/setters for user input
    def Get(self, clsorinst, allowdefault=False):
        if allowdefault:
            return getattr(clsorinst, self.name, self.default)
        return getattr(clsorinst, self.name)
        
    def Set(self, cls_or_inst, value):
        # Keep track on which classes we make modifications.
        # These are reset between maps.
        if inspect.isclass(cls_or_inst):
            if '__%s_fieldinfo' % (self.name) not in cls_or_inst.__dict__:
                self.wrefsclasses.add(weakref.ref(cls_or_inst))
        self.Verify(value)
        setattr(cls_or_inst, self.name, self.ToValue(value))
            
    def Save(self, instance, savehelper):
        """ Saves data for single player.
        
            Args:
                instance (object): the object for which the data is being written.
                savehelper (PySaveHelper): Helper class exposing the possible save actions.
        """
        savehelper.WriteString(self.ToString(self.Get(instance)))
        
    def Restore(self, instance, restorehelper):
        """ Restores data for single player
        
            Args:
                instance (object): the object for which the data is being written.
                restorehelper (PyRestoreHelper): Helper class exposing the possible restore actions.
        """
        self.Set(instance, restorehelper.ReadString())
        
    #: The name of this field. This is also the attribute name on the class/instance of this field.
    name = None
    #: A weak references to the class objects on which this field is defined or used.
    #: Derived classes may set a different field value through the attribute error, in which case
    #: they get added to this list (sharing the same field instance).
    wrefsclasses = None
    #: Calls Init method on this field when instance on which this field is defined is created.
    requiresinit = False
    #: Do not show up in the attribute editor if True
    hidden = False 
    #: Never reset this value to the default
    noreset = False
    #: Generic option to group types of fields in a map, accessible on classes by "field_by_group"
    group = None
    #: Units only: call OnChangeOwnerNumber when an unit changes.
    callonchangeownernumber = False
    
    # fgd generation settings
    fgdtype = 'string'
    fgdreadonly = False
        
class GenericField(BaseField):
    """ Generic field which does not contain any functionality """
    def Restore(self, instance, restorehelper):
        self.Set(instance, ast.literal_eval(restorehelper.ReadString()))
    
class BooleanField(BaseField):
    """ The boolean field only accepts True or False as values (or 
        anything that evaluates to that)."""
    def __init__(self, value=False, **kwargs):
        super().__init__(value=value, **kwargs)
        
    def ToValue(self, value):
        # Hammer sends string "0" as False and "1" as True.
        # Also, in the attribute editor we might set it as "True" or "False"
        if type(value) == str:
            return bool(ast.literal_eval(value))
        # Fallback to evaluate as a boolean
        return bool(value)
        
    def Save(self, instance, savehelper):
        savehelper.WriteBoolean(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        self.Set(instance, restorehelper.ReadBoolean())
        
    def GenerateFGDProperty(self):
        return '%(keyname)s(%(type)s)%(readonly)s: "%(displayname)s" : %(default)s : "%(helpstring)s" = \n\t[\n\t\t0 : "False"\n\t\t1 : "True"\n\t]' % {
            'keyname': self.keyname,
            'type': self.fgdtype,
            'default': str(int(self.default)),
            'readonly': ' readonly' if self.fgdreadonly else '',
            'displayname': self.displayname if self.displayname else self.keyname,
            'helpstring': _escape_helpstring(self.helpstring),
        }
        
    fgdtype = 'choices'

class IntegerField(BaseField):
    """ The integer field only accepts numbers as values (or 
        anything that evaluates to that)."""
    def __init__(self, value=0, **kwargs):
        super().__init__(value=value, **kwargs)
        
    def ToValue(self, value):
        return int(value)
        
    def GenerateFGDDefaultValue(self):
         # NOTE: integers are not wrapped in ""...
        return '%d' % (self.default)
        
    def Save(self, instance, savehelper):
        savehelper.WriteInteger(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        self.Set(instance, restorehelper.ReadInteger())
        
    fgdtype = 'integer'

class FloatField(BaseField):
    """ Float field """
    def __init__(self, value=0.0, **kwargs):
        super().__init__(value=value, **kwargs)
        
    def ToValue(self, value):
        return float(value)
        
    def Save(self, instance, savehelper):
        savehelper.WriteFloat(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        self.Set(instance, restorehelper.ReadFloat())
        
    fgdtype = 'float'

class StringField(BaseField):
    """ String field """
    def __init__(self, value='', **kwargs):
        super().__init__(value=value, **kwargs)
        
    def ToValue(self, value):
        return str(value)
        
    fgdtype = 'string'

class LocalizedStringField(StringField):
    """ Localizes the string value.
        Note: localized value is unicode by default!
              Use the encoding argument to change it if needed (i.e. encoding='ascii')
    """
    def __init__(self, value='', encoding=None, **kwargs):
        super().__init__(value=value, **kwargs)
        
        self.encoding = encoding
        
    def ToValue(self, rawvalue):
        """ Convert string to value.
            Will return the same value if already correct. """
        # Localize value on client
        # On server return the unmodified string value
        try:
            localizedvalue = str(rawvalue)
        except UnicodeEncodeError:
            localizedvalue = str(rawvalue)
            
        if isclient and rawvalue and rawvalue[0] == '#':
            localizedvalue = localize.Find(rawvalue)
            if localizedvalue != None:
                pass
                #if self.encoding:
                #    localizedvalue = localizedvalue.encode(self.encoding)
            else:
                localizedvalue = ''
        return localizedvalue if localizedvalue != None else ''

class EHandleField(BaseField):
    def Save(self, instance, savehelper):
        savehelper.WriteEHandle(PyHandle(getattr(instance, self.name)))
        
    def Restore(self, instance, restorehelper):
        self.Set(instance, restorehelper.ReadEHandle())

class TargetSrcField(StringField):
    fgdtype = 'target_source'

class TargetDestField(StringField):
    fgdtype = 'target_destination'

class FilterField(StringField):
    fgdtype = 'filterclass'

class ModelField(StringField):
    fgdtype = 'studio'

class VectorField(BaseField):
    """ Vector field.
    
        Special Note: entity instances will make a copy of the default Vector value
                      on initialization, so you can safely modify the attributes of
                      the Vector.
    """
    def __init__(self, value=None, invalidate=False, **kwargs):
        if not value:
            value = Vector()
            invalidate = True
        if invalidate:
            value.Invalidate()
    
        super().__init__(value=value, **kwargs)
    
    def ToValue(self, value):
        if type(value) is Vector:
            return Vector(value)
        return StringToVector(value)
        
    def Save(self, instance, savehelper):
        savehelper.WriteVector(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        self.Set(instance, restorehelper.ReadVector())
        
    def InitField(self, inst):
        if self.networked and isserver:
            assert not self.propname, 'VectorField does not support propname argument'
            NetworkVar(inst, self.name, Vector(self.default), 
                    changedcallback=self.clientchangecallback, sendproxy=self.sendproxy)
        else:
            setattr(inst, self.name, Vector(self.default))
            
    def ToString(self, value):
        return '%f %f %f' % (value[0], value[1], value[2])
        
    def GenerateFGDDefaultValue(self):
        return '"%f %f %f"' % (self.default[0], self.default[1], self.default[2])
        
    requiresinit = True
    fgdtype = 'vector'

class QAngleField(BaseField):
    """ QAngle field.
    
        Special Note: entity instances will make a copy of the default QAngle value
                      on initialization, so you can safely modify the attributes of
                      the QAngle.
    """
    def __init__(self, value=None, invalidate=False, **kwargs):
        if not value:
            value = Vector()
            invalidate = True
        if invalidate:
            value.Invalidate()
    
        super().__init__(value=value, **kwargs)
    
    def ToValue(self, value):
        if type(value) is QAngle:
            return QAngle(value)
        return StringToAngle(value)
        
    def InitField(self, inst):
        if self.networked and isserver:
            assert not self.propname, 'QAngleField does not support propname argument'
            NetworkVar(inst, self.name, QAngle(self.default)
                    , changedcallback=self.clientchangecallback, sendproxy=self.sendproxy)
        else:
            setattr(inst, self.name, QAngle(self.default))
            
    def ToString(self, value):
        return '%f %f %f' % (value[0], value[1], value[2])
        
    def GenerateFGDDefaultValue(self):
        return '"%f %f %f"' % (self.default[0], self.default[1], self.default[2])
        
    requiresinit = True
    fgdtype = 'angle'

class ColorField(BaseField):
    """ Color field """
    def ToValue(self, value):
        if type(value) is Color:
            return Color(value.r(), value.g(), value.b(), value.a())
        return StringToColor(value)
        
    def ToString(self, value):
        return '%d %d %d %d' % (value.r(), value.g(), value.b(), value.a())
        
    fgdtype = 'color255'
    
class SetField(BaseField):
    def __init__(self, value=set(), **kwargs):
        super().__init__(value=set(value), **kwargs)
        
    def InitField(self, inst):
        if self.networked and isserver:
            assert not self.propname, 'SetField does not support propname argument'
            NetworkSet(inst, self.name, set(self.default)
                    , changedcallback=self.clientchangecallback, sendproxy=self.sendproxy)
        else:
            setattr(inst, self.name, set(self.default))
        
    def ToString(self, value):
        """ Convert value to string representation. 
        
            Set is represented as a list string, so ToValue can convert it back. 
        """
        return str(list(value))
        
    def ToValue(self, rawvalue):
        """ Convert string to value.
            Will return the same value if already correct. """
        if type(rawvalue) == str:
            return set(ast.literal_eval(rawvalue))
        return set(rawvalue) # Create a copy of the set
        
    requiresinit = True


class ListField(BaseField):
    """ List field.
    
        NOTE: networked list fields do not implement all list methods!
    """
    def __init__(self, value=list(), restrict_type=None, **kwargs):
        super().__init__(value=list(value), **kwargs)

        self.restrict_type = restrict_type
        
    def InitField(self, inst):
        if self.networked and isserver:
            assert not self.propname, 'ListField does not support propname argument'
            NetworkArray(inst, self.name, list(self.default),
                         changedcallback=self.clientchangecallback, sendproxy=self.sendproxy)
        else:
            setattr(inst, self.name, list(self.default))
            
    def ToValue(self, rawvalue):
        """ Convert string to value.
            Will return the same value if already correct. """
        if type(rawvalue) == str:
            return ast.literal_eval(rawvalue)
        return list(rawvalue)  # Create a copy of the list

    def ToJSON(self, value):
        if not self.restrict_type:
            return value
        out_list = []
        for v in value:
            data = {}
            fields = GetAllFields(v.__class__)
            for f in fields:
                data[f.name] = f.ToJSON(f.Get(v))
            out_list.append(data)
        return out_list

    def FromJSON(self, value):
        if not self.restrict_type:
            return value
        out_list = []
        for v in value:
            obj = self.restrict_type()
            obj_fields = GetAllFields(self.restrict_type)
            for f in obj_fields:
                setattr(obj, f.name, f.FromJSON(v[f.name]))
            out_list.append(obj)
        return out_list
            
    # Take special care of networked lists, should only update the data!
    def Save(self, instance, savehelper):
        if not self.networked:
            super().Save(instance, savehelper)
            return
        savehelper.WriteString(self.ToString(getattr(instance, self.name).data))

    def Restore(self, instance, restorehelper):
        data = self.ToValue(restorehelper.ReadString())
        getattr(instance, self.name)[:] = data
            
    requiresinit = True


class DictField(BaseField):
    """ Dictionary field.
    
        NOTE: networked dictionary fields do not implement all dict methods!
    """
    def __init__(self, value=dict(), default=None, **kwargs):
        super().__init__(value=value, **kwargs)
        self.defaultvalue = default
        
    def InitField(self, inst):
        if self.networked and isserver:
            assert not self.propname, 'DictField does not support propname argument'
            if self.defaultvalue is None:
                NetworkDict(inst, self.name, dict(self.default),
                        changedcallback=self.clientchangecallback, sendproxy=self.sendproxy) 
            else:
                NetworkDefaultDict(inst, self.name, dict(self.default),
                        default=self.defaultvalue, changedcallback=self.clientchangecallback, sendproxy=self.sendproxy) 
        else:
            setattr(inst, self.name, dict(self.default))

    def ToValue(self, rawvalue):
        """ Convert string to value.
            Will return the same value if already correct. """
        if type(rawvalue) == str:
            return ast.literal_eval(rawvalue)
        return dict(rawvalue) # Create a copy of the dictionary

    def ToJSON(self, value):
        return value

    # Take special care of networked dicts, should only update the data!
    def Save(self, instance, savehelper):
        if not self.networked:
            super().Save(instance, savehelper)
            return
        data = dict(getattr(instance, self.name).data) # Create a copy as regular dict
        savehelper.WriteString(self.ToString(data))

    def Restore(self, instance, restorehelper):
        data = self.ToValue(restorehelper.ReadString())
        getattr(instance, self.name).update(data)
            
    requiresinit = True


class FlagsField(BaseField):
    def __init__(self, value=0, flags=[], *args, **kwargs):
        self.flags = flags
        for flaginfo in self.flags:
            if len(flaginfo) == 3:
                cppflagname, value, defaultvalue = flaginfo
            else:
                cppflagname, value, defaultvalue, flagname = flaginfo
                
            value |= defaultvalue
            setattr(self, cppflagname, value)
        super().__init__(value=value, *args, **kwargs)

    def Parse(self, cls, name):
        super().Parse(cls, name)
        
        # Add flag names to cls
        for flaginfo in self.flags: 
            if len(flaginfo) == 3:
                cppflagname, value, defaultvalue = flaginfo
            else:
                cppflagname, value, defaultvalue, flagname = flaginfo
            setattr(cls, cppflagname, value)
        
    def GenerateFGDProperty(self):
        entry = '%s(flags) = \n\t[\n' % (self.keyname)
        for flaginfo in self.flags:
            if len(flaginfo) == 3:
                flagname, value, defaultvalue = flaginfo
            else:
                cppflagname, value, defaultvalue, flagname = flaginfo
            entry += '\t\t%d : "%s" : %d\n' % (value, flagname, 1 if defaultvalue else 0)
        entry += '\t]'
        return entry


class ObjectField(BaseField):
    """ Defines an embedded object inside the object. This object can have fields again.
        Mainly used for save/restoring objects.
    """
    def __init__(self, objectcls, *objectargs, **objectkwargs):
        super().__init__(nofgd=True)
        
        self.objectcls = objectcls
        self.objectargs = objectargs
        self.objectkwargs = objectkwargs
        
    def Parse(self, cls, name):
        super().Parse(cls, name)
    
        SetupClassFields(self.objectcls)
        
    def InitField(self, inst):
        setattr(inst, self.name, self.objectcls(*self.objectargs, **self.objectkwargs))
        
    def Save(self, instance, savehelper):
        """ Saves data for single player. """
        savehelper.WriteFields(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        """ Restores data for single player """
        restorehelper.ReadFields(getattr(instance, self.name))
        
    requiresinit = True


class ActivityField(BaseField):
    """ Defines an activity field, which can either be defined by the string name or by the Activity enum.

        Activity variables should use these fields so they get reset between levels. This is important for
        activities defined by string name, because the activity index may change between map changes.
    """
    group = 'activity'

# Entity class only fields
if isserver:
    class OutputEvent(COutputEvent):
        def __init__(self, fieldtype):
            super().__init__()
            self.fieldtype = fieldtype
            self.value = variant_t()
            
        variant_setters = {
            fieldtypes.FIELD_VOID: lambda self, value: value,
            fieldtypes.FIELD_INTEGER: variant_t.SetInt,
            fieldtypes.FIELD_FLOAT: variant_t.SetFloat,
            fieldtypes.FIELD_STRING: variant_t.SetString,
            fieldtypes.FIELD_BOOLEAN: variant_t.SetBool,
            fieldtypes.FIELD_VECTOR: variant_t.SetVector3D,
            fieldtypes.FIELD_POSITION_VECTOR: variant_t.SetPositionVector3D,
            fieldtypes.FIELD_EHANDLE: variant_t.SetEntity,
        }
            
        def Set(self, value, activator=None, caller=None):
            try:
                self.variant_setters[self.fieldtype](self.value, value)
            except KeyError:
                PrintWarning("Unknown fieldtype %s in output field %s\n" % (self.fieldtype, self))
            self.FireOutput(self.value, activator, caller)
            
output_fgdtypes = {
    fieldtypes.FIELD_VOID : 'void',
    fieldtypes.FIELD_INTEGER : 'integer',
    fieldtypes.FIELD_FLOAT : 'float',
    fieldtypes.FIELD_STRING : 'string',
    fieldtypes.FIELD_BOOLEAN : 'bool',
    fieldtypes.FIELD_VECTOR : 'vector',
    fieldtypes.FIELD_POSITION_VECTOR : 'void', # not used anywhere ?
    fieldtypes.FIELD_EHANDLE : 'target_destination',
}


class OutputField(BaseField):
    """ Output field (entity only)"""
    def __init__(self, keyname, fieldtype=fieldtypes.FIELD_VOID, *args, **kwargs):
        super().__init__(keyname=keyname, noreset=True, *args, **kwargs)
        self.fieldtype = fieldtype

    def Save(self, instance, savehelper):
        """ Saves data for single player. """
        savehelper.WriteOutputEvent(getattr(instance, self.name))
        
    def Restore(self, instance, restorehelper):
        """ Restores data for single player """
        restorehelper.ReadOutputEvent(getattr(instance, self.name))
        
    if isserver:
        def InitField(self, inst):
            oe = OutputEvent(self.fieldtype)
            setattr(inst, self.name, oe)
            
        def Set(self, clsorinst, value):
            if inspect.isclass(clsorinst):
                # Doing this is only valid on entity instances
                # On the class itself, just clear the field reference (still available as "__field_%name%")
                setattr(clsorinst, self.name, None)
                return 
            oe = getattr(clsorinst, self.name)
            eventdata = '%s,%s' % (value, self.keyname)
            oe.ParseEventAction(eventdata)
    else:
        def Set(self, clsorinst, value):
            # Noop on the client
            # On the class itself, just clear the field reference (still available as "__field_%name%")
            setattr(clsorinst, self.name, None)

    def GenerateFGDProperty(self):
        return 'output %(keyname)s(%(outputtype)s) : "%(helpstring)s"' % {
            'keyname' : self.keyname,
            'outputtype' : output_fgdtypes[self.fieldtype],
            'helpstring' : _escape_helpstring(self.helpstring),
        }
            
    hidden = True
    requiresinit = True


# Wars Game specific fields
class UpgradeField(GenericField):
    """ Upgrade field (unit only)"""
    def __init__(self, abilityname, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.abilityname = abilityname
    
    def InitField(self, unit):
        # Sucky confusing upgrade/tech upgrade code
        unitinfo = unit.unitinfo
        
        # Get ability info + prev
        abiinfo, prevabiinfo = unitinfo.GetAbilityInfoAndPrev(self.abilityname, unit.GetOwnerNumber())
        if abiinfo:
            technode = abiinfo.GetTechNode(abiinfo.name, unit.GetOwnerNumber())
            if technode.techenabled:
                if self.networked and isserver:
                    NetworkVar(unit, self.name, technode.upgradevalue, changedcallback=self.clientchangecallback, sendproxy=self.sendproxy).NetworkStateChanged()
                else:
                    setattr(unit, self.name, technode.upgradevalue)
            elif prevabiinfo:
                technode = prevabiinfo.GetTechNode(prevabiinfo.name, unit.GetOwnerNumber())
                if self.networked and isserver:
                    NetworkVar(unit, self.name, technode.upgradevalue, changedcallback=self.clientchangecallback, sendproxy=self.sendproxy).NetworkStateChanged()
                else:
                    setattr(unit, self.name, technode.upgradevalue)
        elif prevabiinfo:
            technode = prevabiinfo.GetTechNode(prevabiinfo.name, unit.GetOwnerNumber())
            if self.networked and isserver:
                NetworkVar(unit, self.name, technode.upgradevalue, changedcallback=self.clientchangecallback, sendproxy=self.sendproxy).NetworkStateChanged()
            else:
                setattr(unit, self.name, technode.upgradevalue)
        else:
            # Fallback to default if none of the abilities are available
            super().InitField(unit)
            
    def OnChangeOwnerNumber(self, unit, oldownernumber):
        self.InitField(unit)
    
    requiresinit = True
    callonchangeownernumber = True
    hidden = True  # Edit related ability instead


class PlayerField(IntegerField):
    playerchoices = [
        (0, 'Neutral'),
        (1, 'Enemy'),
        (2, 'Player_0'),
        (3, 'Player_1'),
        (4, 'Player_2'),
        (5, 'Player_3'),
        (6, 'Player_4'),
        (7, 'Player_5'),
        (8, 'Player_6'),
        (9, 'Player_7'),
    ]

    def __init__(self, value=2, **kwargs):
        super().__init__(value=value, choices=self.playerchoices, **kwargs)


@receiver(postlevelshutdown)
def ResetFields(sender, **kwargs):
    global fields
    fields = list([f for f in fields if bool(f())])  # Remove None fields
    for f in fields:
        try:
            f().Reset()
        except ValueError:
            traceback.print_exc()


# Setup methods for fields
def GetField(obj, name):
    return getattr(obj, '__%s_fieldinfo' % (name))


def ObjSetField(obj, name, field):
    setattr(obj, '__%s_fieldinfo' % (name), field)


def HasField(obj, name):
    return hasattr(obj, '__%s_fieldinfo' % (name))


def BuildFieldsMap(obj, fieldmap, includebases=True):
    for name, field in obj.__dict__.items():
        if not isinstance(field, BaseField):
            continue
        if name not in fieldmap.keys():
            fieldmap[name] = field
    if includebases:
        for b in obj.__bases__:
            BuildFieldsMap(b, fieldmap)


def GetAllFields(obj, includebases=True):
    fieldmap = {}
    BuildFieldsMap(obj, fieldmap, includebases=includebases)
    return list(fieldmap.values())


class KeyValueLookupDict(dict):
    def get(self, key, default=None):
        key = key.lower()
        return dict.get(self, key, default)


def SetupClassFields(cls, done=None):
    """ Searches for all fields.
        Recursive parses base classes that are not parsed yet.
        This is needed because Entity classes don't support metaclasses.
        Otherwise it could have been solved in a nicer way."""
    # Might already be parsed
    # NOTE: we use cls.__dict__ here because we don't want 
    # to check __fieldsparsed from the bases. We want to know
    # if THIS class is parsed yet.
    if cls.__dict__.get('__fieldsparsed', False):
        return
        
    # Set attribute to False
    # If we cannot do that, it is a builtin object
    try:
        setattr(cls, '__fieldsparsed', False)
    except TypeError:
        return

    done = done or set()
        
    # Ensure fields of base classes are all setup.
    for base_cls in cls.__bases__:
        if base_cls not in done:
            done.add(base_cls)
            SetupClassFields(base_cls, done)

    # Build map of fields to parse, consisting of:
    # 1. New fields in class
    # 2. Other attributes overriding the default of the base class field. A copy is made of this field.
    # 3. The remaining fields in base classes, which are also copied.
    fields_to_parse = {}

    for name, f in list(cls.__dict__.items()):
        if isinstance(f, BaseField):
            fields_to_parse[name] = f
        elif HasField(cls, name):
            # Maybe the attribute is a field in the baseclass?
            # Then copy the field and use the attribute from this
            # class as the default for the copied field.
            fields_to_parse[name] = GetField(cls, name).Copy()
            fields_to_parse[name].default = f

    for basecls in cls.__bases__:
        for name, field in getattr(basecls, 'fields', {}).items():
            if name not in fields_to_parse:
                fields_to_parse[name] = field.Copy()
    
    # Setup all fields
    #: Note about keyfields: store all keys lower case and do all lookups lower case (KeyValueLookupDict)
    fields = {}
    key_fields = {}
    init_fields = {}
    ownernumberchangefields = {}
    cls_fields_by_group = defaultdict(dict)
    for name, field in fields_to_parse.items():
        try:
            field.Parse(cls, name)
        except:
            PrintWarning('Failed to parse field %s of class %s:\n' % (name, str(cls)))
            traceback.print_exc()
            continue

        fields[name] = field
        if field.keyname:
            key_fields[field.keyname.lower()] = field
        if field.requiresinit:
            init_fields[field.name] = field
        if field.callonchangeownernumber:
            ownernumberchangefields[field.name] = field

        if field.group:
            cls_fields_by_group[field.group][field.name] = field
         
    # Bind list of fields to the class
    cls.fields = fields
    
    # Setup keyvalues map
    keyvaluemap = KeyValueLookupDict()
    for basecls in cls.__bases__:
        basekeyvaluemap = getattr(basecls, 'keyvaluemap', None)
        if not basekeyvaluemap:
            continue

        keyvaluemap.update(KeyValueLookupDict(basekeyvaluemap))

    keyvaluemap.update(key_fields)
    keyvaluemap = KeyValueLookupDict([x for x in list(keyvaluemap.items()) if not x[1].cppimplemented])
    cls.keyvaluemap = keyvaluemap
    
    # Setup init map (entity only)
    fieldinitmap = {}
    for basecls in cls.__bases__:
        fieldinitmap.update(getattr(basecls, 'fieldinitmap', {}))
    fieldinitmap.update(init_fields)
    cls.fieldinitmap = fieldinitmap

    # Setup fields by group map
    fields_by_group = defaultdict(dict)
    for basecls in cls.__bases__:
        base_fields_by_group = getattr(basecls, 'fields_by_group', {})
        for key, value in base_fields_by_group.items():
            fields_by_group[key].update(value)
    for key, value in cls_fields_by_group.items():
        fields_by_group[key].update(value)
    cls.fields_by_group = fields_by_group
    
    # Setup ownernumber change map (unit only)
    ownernumberchangemap = {}
    for basecls in cls.__bases__:
        ownernumberchangemap.update(getattr(basecls, 'ownernumberchangemap', {}))
    ownernumberchangemap.update(ownernumberchangefields)
    cls.ownernumberchangemap = ownernumberchangemap
    
    # Mark this class as parsed
    setattr(cls, '__fieldsparsed', True)


# Input system
def input(inputname, helpstring='', fieldtype=fieldtypes.FIELD_VOID):
    """ Use this decorator to turn a method into an input function.
    
        The method must take a single argument as input (data).
        You can then fire this method using the input/output system of source engine.
        Example: ent_fire entityname inputname.
        
        Currently the method name will not appear in the auto complete list of the ent_fire command.
    """
    def fnwrapper(fn):
        fn.inputname = inputname
        fn.helpstring = helpstring
        fn.fieldtype = fieldtype
        
        fn.fgdinputentry = 'input %(keyname)s(%(outputtype)s) : "%(helpstring)s"' % {
                'keyname': fn.inputname,
                'outputtype': output_fgdtypes[fn.fieldtype],
                'helpstring': _escape_helpstring(fn.helpstring)}
        return fn
    return fnwrapper


def SetupInputMethods(cls):
    if cls.__dict__.get('__inputmethodsparsed', False):
        return
        
    # Set attribute to False
    # If we cannot do that, it is a builtin object
    try: 
        setattr(cls, '__inputmethodsparsed', False)
    except: 
        return
        
    # Recursive parse base classes
    for basecls in cls.__bases__:
        SetupInputMethods(basecls)
        
    # Grab base inputmap. Create new one if there is no inputmap yet.
    inputmap = dict(getattr(cls, 'inputmap', {}))
    
    for name, f in cls.__dict__.items():
        # TODO: Verify is function?
        # if type(f) is not MethodType and type(f) is not FunctionType:
            # continue

        try: 
            f.inputname
        except AttributeError:
            continue

        inputmap[f.inputname] = f
            
    cls.inputmap = inputmap
    
    # Mark this class as parsed
    setattr(cls, '__inputmethodsparsed', True)


class SerializableObjectMetaclass(type):
    def __new__(cls, name, bases, dct):
        # Create the new cls
        new_cls = type.__new__(cls, name, bases, dct)

        # Parse all fields instances defined on the object
        SetupClassFields(new_cls)

        return new_cls


class SerializableObject(object, metaclass=SerializableObjectMetaclass):
    """ Defines a basic object with fields.
        These fields are parsed one time through the metaclass. """
    pass
