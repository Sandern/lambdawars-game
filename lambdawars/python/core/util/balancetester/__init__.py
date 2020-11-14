if not isserver:
    raise Exception('balancetester should be runned from server!')
    
from . import commands
from . import balancetest
from . import runner
from . import reporter
