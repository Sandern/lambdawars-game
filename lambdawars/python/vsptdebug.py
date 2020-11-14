import sys
import os
import shlex

def run_vspt_debug(commandline):
    ''' Runs Visual Studio Python Tools debugger '''
    args = shlex.split(commandline)
    
    launcherfilepath = args[0]
    vsptpath = os.path.dirname(launcherfilepath)
    if vsptpath not in sys.path:
        sys.path.append(vsptpath)
    
    port_num = int(args[2])
    debug_id = args[3]
    redirect_output = '--redirect-output' in args
    
    import visualstudio_py_debugger
    
    # remove us from modules so there's no trace of us
    sys.modules['$visualstudio_py_debugger'] = sys.modules['visualstudio_py_debugger']
    __name__ = '$visualstudio_py_debugger'
    del sys.modules['visualstudio_py_debugger']
    
    print('visualstudio_py_debugger.attach_process(%s, %s)' % (port_num, debug_id))
    visualstudio_py_debugger.attach_process(port_num, debug_id, report = True)
    assert visualstudio_py_debugger.DETACHED == False, 'Visual Studio Python Tools not attached!'

    if redirect_output:
        visualstudio_py_debugger.enable_output_redirection()

    # setup the current thread
    cur_thread = visualstudio_py_debugger.new_thread()
    assert(cur_thread != None)
    cur_thread.stepping = visualstudio_py_debugger.STEPPING_LAUNCH_BREAK

    # start tracing on this thread
    sys.settrace(cur_thread.trace_func)
    
    assert visualstudio_py_debugger.DETACHED == False, 'Visual Studio Python Tools not attached!'
    
    print('Attached Visual Studio Python Tools debugger with debug id %s and port number %s' % (debug_id, port_num))