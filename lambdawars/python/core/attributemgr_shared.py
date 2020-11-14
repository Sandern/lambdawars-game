import types

# List of known types
knowntypes = [bool, int, float, str, types.FunctionType]
specialattr = ['__name__', '__module__', '__doc__', '__dict__', '__class__']

# Flags can be used in combination with the *_requestall commands
class ReqAttrFilterFlags:
    pass
    
# Filter function
def IsAttributeFiltered(key, value, filterflags):
    if value.hidden:
        return True
    return False