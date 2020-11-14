import sys

originalexcepthook = None
exceptionoccurred = False
def CustomExceptHook(type, value, traceback):
    global exceptionoccurred
    exceptionoccurred = True
    return originalexcepthook(type, value, traceback)

def InstallCustomExceptHook():
    global exceptionoccurred, originalexcepthook
    if sys.excepthook != CustomExceptHook:
        originalexcepthook = sys.excepthook
        sys.excepthook = CustomExceptHook
    exceptionoccurred = False

def UninstallCustomExceptHook():
    global originalexcepthook
    if sys.excepthook == CustomExceptHook:
        sys.excepthook = originalexcepthook
        originalexcepthook = None
    ClearExceptionOcurred()

def CheckExceptionOcurred():
    global exceptionoccurred
    return exceptionoccurred

def ClearExceptionOcurred():
    global exceptionoccurred
    exceptionoccurred = None
