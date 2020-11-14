from collections import defaultdict
from . dispatch import Signal

from gameinterface import CSingleUserRecipientFilter, CReliableBroadcastRecipientFilter, \
                              CBroadcastRecipientFilter, CPASFilter, CPASAttenuationFilter, CPVSFilter

if isserver:
    from gameinterface import SendUserMessage, CRecipientFilter
else:
    from gameinterface import C_RecipientFilter as CRecipientFilter

# Reliable version of CSingleUserRecipientFilter
class CReliableSingleUserRecipientFilter(CSingleUserRecipientFilter):
    def __init__(self, *args, **kwargs):
        super(CReliableSingleUserRecipientFilter, self).__init__(*args, **kwargs)
        self.MakeReliable()
        
if isclient:
    # Client stub method
    def SendUserMessage(*args, **kwargs): pass

# Dictionary containing signals for each message handler
messagesignals = defaultdict(lambda : Signal())
    
def _DispatchMessage(messagename, msg):
    #print('Message name: %s -> %s (receivers: %s)' % (messagename, str(msg), messagesignals[messagename].receivers))
    responses = messagesignals[messagename].send_robust(None, msg=msg)
    if responses:
        for r in responses:
            if isinstance(r[1], Exception):
                PrintWarning('%s (contents: %s): Error in receiver %s (module: %s): \n%s' % 
                    (messagename, str(msg), r[0], r[0].__module__, r[2]))
    else:
        PrintWarning('_DispatchMessage: no responses for user message %s!\n' % (messagename))
            
def _MakeUserMessageName(func):
    return '%s__%s' % (func.__module__, func.__name__)

def usermessage(messagename=None, usesteamp2p=False, **kwargs):
    """ Register an usermessage.
    
        Kwargs:
        
            messagename (str): Name of the usermessage. If None, it will automatically
                               create a messagename from the method and module name.
            usesteamp2p (bool): Use Steam P2P instead of Source Engine netchannel.
                                Limit of message size is larger for this option 
                                (but not tested as much).
    """
    if isserver:
        def _decorator(func):
            name = messagename
            if not name: name = _MakeUserMessageName(func)
            def _sendmessage(*msg, **sendkwargs):
                filter = sendkwargs['filter'] if 'filter' in sendkwargs else CReliableBroadcastRecipientFilter()
                SendUserMessage(filter, name, list(msg), usesteamp2p=usesteamp2p)
            return _sendmessage
    else:
        def _decorator(func):
            name = messagename
            if not name: name = _MakeUserMessageName(func)
            def recvfunc(msg, **recvkwargs):
                func(*msg, **recvkwargs)
            try:
                setattr(func.__self__, 'recv_%s' % (name), recvfunc)
            except:
                func.recvfunc = recvfunc
            messagesignals[name].disconnect(dispatch_uid=name) # Disconnect old if any!
            messagesignals[name].connect(recvfunc, dispatch_uid=name, **kwargs)
            return func
    return _decorator
    
def usermessage_shared(messagename=None, usesteamp2p=False, **kwargs):
    """ Register an usermessage. 
    
        Shared differs from the normal one in that it also executes
        the method on the server. It also always first calls the server
        method before sending the message to client.
        
    
        Kwargs:
        
            messagename (str): Name of the usermessage. If None, it will automatically
                               create a messagename from the method and module name.
            usesteamp2p (bool): Use Steam P2P instead of Source Engine netchannel.
                                Limit of message size is larger for this option 
                                (but not tested as much).
    """
    if isserver:
        def _decorator(func):
            name = messagename
            if not name: name = _MakeUserMessageName(func)
            def _sendmessage(*msg,**kwargs):
                rv = func(*msg, **kwargs)
                filter = kwargs['filter'] if 'filter' in kwargs else CReliableBroadcastRecipientFilter()
                SendUserMessage(filter, name, list(msg), usesteamp2p=usesteamp2p)
                return rv
            try:
                setattr(func.__self__, 'sendmsg_%s' % (name), _sendmessage)
            except:
                func._sendmessage = _sendmessage
            messagesignals[name].disconnect(dispatch_uid=name) # Disconnect old if any!
            messagesignals[name].connect(_sendmessage, dispatch_uid=name, **kwargs)
            return _sendmessage
    else:
        def _decorator(func):
            name = messagename
            if not name: name = _MakeUserMessageName(func)
            def recvfunc(msg, **recvkwargs):
                func(*msg, **recvkwargs)
            try:
                setattr(func.__self__, 'recv_%s' % (name), recvfunc)
            except:
                func.recvfunc = recvfunc
            messagesignals[name].disconnect(dispatch_uid=name) # Disconnect old if any!
            messagesignals[name].connect(recvfunc, dispatch_uid=name, **kwargs)
            return func
    return _decorator
    
'''
# Example:
# Calling testfunc on the server results in it being called on the client.
@usermessage()
def testfunc(arg1, arg2, **kwargs):
    print 'isserver: %s, msg: %s %s' % (isserver, arg1, arg2)

# Calling this function on the server will result in it being both called on the client and server
@usermessage_shared()
def testfunc2(arg1, arg2, **kwargs):
    print 'isserver: %s, msg: %s %s' % (isserver, arg1, arg2)
    
if isserver:
    from utils import UTIL_PlayerByIndex
    from gameinterface import CSingleUserRecipientFilter
    
    # Without args. Defaults to reliable broadcast
    print('Calling function')
    testfunc('5', '10')
    
    # With custom filter. Send to specific user. In this case the first player in the array
    # The message arguments are always formal arguments, while keyword arguments are used for 
    # configuring the message
    print('Calling function with custom filter')
    filter = CSingleUserRecipientFilter(UTIL_PlayerByIndex(1))
    filter.MakeReliable()
    testfunc('42', '22', filter=filter)
    
    # Shared function called on both server and client
    #print('Calling shared function')
    testfunc2('666', '45')

'''