"""Decorators for client/server-side code execution control.

Provides decorators to mark functions that should only execute on the
client or server side. This is essential for Source Engine games where
code runs on both server and client, but certain operations should only
happen on one side.

Decorators include:
- clientonly: Silently does nothing on server
- clientonly_assert: Asserts if called on server
- serveronly: Silently does nothing on client
- serveronly_assert: Asserts if called on client
"""

def clientonly(fn):
    ''' Methods with this decorator are only executed on the client.
        On the server, the method will do nothing. '''
    if not isclient:
        def StubMethod(*args, **kwargs): pass
        return StubMethod
    return fn
    
def clientonly_assert(fn):
    ''' Methods with this decorator can only be executed on the client.
        On the server, the method will result in an assert. '''
    if not isclient:
        def StubMethod(*args, **kwargs): assert isclient, 'method can only be called on the client!'
        return StubMethod
    return fn
    
def serveronly(fn):
    ''' Methods with this decorator are only executed on the server.
        On the client, the method will do nothing. '''
    if not isserver:
        def StubMethod(*args, **kwargs): pass
        return StubMethod
    return fn
    
def serveronly_assert(fn):
    ''' Methods with this decorator can only be executed on the server.
        On the client, the method will result in an assert. '''
    if not isserver:
        def StubMethod(*args, **kwargs): assert isserver, 'method can only be called on the server!'
        return StubMethod
    return fn