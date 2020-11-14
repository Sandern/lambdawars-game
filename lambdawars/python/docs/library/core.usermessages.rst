:mod:`core`: Usermessages
------------------------------------

.. module:: core.usermessages
   :synopsis: Provides methods for sending messages from server to client.

The :mod:`core.usermessages` module provides methods for sending messages from server to client.

---------------------------------
Registering and sending a message
---------------------------------
The following two decorators can be used to register 
a method as an usermessage:
 
.. automethod:: core.usermessages.usermessage

.. automethod:: core.usermessages.usermessage_shared

Sending the message then becomes as easy as calling the method::

    from core.usermessages import usermessage, usermessage_shared, CSingleUserRecipientFilter

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
        
        # Without args. Defaults to reliable broadcast
        print('Calling function testfunc')
        testfunc('5', '10')
        
        # With custom filter. Send to specific user. In this case the first player in the array
        # The message arguments are always formal arguments, while keyword arguments are used for 
        # configuring the message
        print('Calling function testfunc with custom filter')
        filter = CSingleUserRecipientFilter(UTIL_PlayerByIndex(1))
        filter.MakeReliable()
        testfunc('42', '22', filter=filter)
        
        # Shared function called on both server and client
        #print('Calling shared function testfunc2')
        testfunc2('666', '45')


You can also use the ``SendUserMessage`` method in case you only
know the name of the message or do not want to import the module
with the method:

.. automethod:: core.usermessages.SendUserMessage

---------------------------------
Filters
---------------------------------
Filters control to which client an usermessage is sent.
The following filters can be used for sending usermessages:

.. autoclass:: core.usermessages.CRecipientFilter
    :members:
    
.. autoclass:: core.usermessages.CSingleUserRecipientFilter
    :members:
    
.. autoclass:: core.usermessages.CReliableBroadcastRecipientFilter
    :members:
    
.. autoclass:: core.usermessages.CBroadcastRecipientFilter
    :members:
    
.. autoclass:: core.usermessages.CPASFilter
    :members:
    
.. autoclass:: core.usermessages.CPASAttenuationFilter
    :members:
    
.. autoclass:: core.usermessages.CPVSFilter
    :members:
