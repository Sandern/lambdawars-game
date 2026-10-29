"""Shared attribute manager utilities.

Provides shared functionality for the attribute management system used
in Sandbox mode for editing class attributes.
"""
import types

# List of known types
knowntypes = [bool, int, float, str, types.FunctionType]
specialattr = ['__name__', '__module__', '__doc__', '__dict__', '__class__']

# Flags can be used in combination with the *_requestall commands
class ReqAttrFilterFlags:
    """Filter flags for attribute request commands.
    
    Used in combination with the *_requestall commands to filter which
    attributes are returned.
    """
    pass
    
# Filter function
def IsAttributeFiltered(key, value, filterflags):
    """Check if an attribute should be filtered out.
    
    Args:
        key (str): Attribute name.
        value: Attribute value (should be a field instance).
        filterflags (int): Filter flags to apply.
        
    Returns:
        bool: True if the attribute should be filtered, False otherwise.
    """
    if value.hidden:
        return True
    return False