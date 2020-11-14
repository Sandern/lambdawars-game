import sys
import os
import shutil

from gameinterface import concommand, FCVAR_CHEAT
from core.usermessages import usermessage

# Make methods
@usermessage(messagename='makeclientdocs')
def MakeClientDocs(**kwargs):
    clientsourcedir = os.path.abspath('./python/docsclient')
    clientoutdir = os.path.abspath('./python/docsclient/_build/html')
    outdir = os.path.abspath('./python/docs/_build/html')

    if os.path.exists(clientoutdir):
        shutil.rmtree(clientoutdir)
    sys.argv = ['']
    import sphinx
    sphinx.main(['make_docs', '-b', 'html', clientsourcedir, clientoutdir])
    
    # Merge client library into the server and shared library
    clientlibraryout = os.path.join(outdir, 'clientlibrary')
    if os.path.exists(clientlibraryout):
        shutil.rmtree(clientlibraryout)
    shutil.copytree(clientoutdir, clientlibraryout)
    
if isserver:
    @concommand('py_makedocs', 'Generate sphinx python docs', FCVAR_CHEAT)
    def MakeServerDocs(args):
        # Settings
        sourcedir = os.path.abspath('./python/docs')
        outdir = os.path.abspath('./python/docs/_build/html')
        sys.argv = ['']
        import sphinx
        
        # Generate
        sphinx.main(['make_docs', '-b', 'html', sourcedir, outdir])
        
        # Tell client to also generate
        MakeClientDocs()
    