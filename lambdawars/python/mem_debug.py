
# Only available in debug mode (developer > 1)
if __debug__:
    from gameinterface import concommand, AutoCompletion
    from core.signals import postlevelshutdown
    from core.dispatch import receiver
    import objgraph
    import srcmgr

    import weakref
    import tracemalloc
    import gc
    import sys

    snapshots = {}
    snapshot_id = 1

    # Last list of ValidateRefsCleanedUp
    roots = []

    prefix = 'c' if isclient else ''

    @concommand(prefix+'py_mem_debug_start')
    def CCDebugStart(args):
        tracemalloc.start(int(args[1] or 1))

    @concommand(prefix+'py_mem_takesnapshot')
    def CCTakeSnapshot(args):
        global snapshot_id
        snapshot_name = 'snapshot_%d' % snapshot_id
        snapshots[snapshot_name] = tracemalloc.take_snapshot()
        snapshot_id += 1
        print('Created snapshot "%s"' % snapshot_name)

    @concommand(prefix+'py_mem_compare_snapshots', completionfunc=AutoCompletion(lambda: snapshots.keys()))
    def CCCompareSnapshots(args):
        print('Comparing "%s" to "%s"' % (args[1], args[2]))
        snapshot1 = snapshots[args[1]]
        snapshot2 = snapshots[args[2]]
        try:
            n = int(args[3])
        except ValueError:
            n = 10

        top_stats = snapshot2.compare_to(snapshot1, 'lineno')

        print("[ Top 10 differences ]")
        for stat in top_stats[:n]:
            print(stat)

    @concommand(prefix+'py_mem_compare_snapshots_detail', completionfunc=AutoCompletion(lambda: snapshots.keys()))
    def CCCompareSnapshotsDetail(args):
        print('Comparing "%s" to "%s"' % (args[1], args[2]))
        snapshot1 = snapshots[args[1]]
        snapshot2 = snapshots[args[2]]
        try:
            n = int(args[3])
        except ValueError:
            n = 10

        top_stats = snapshot2.compare_to(snapshot1, 'lineno')
        stat = top_stats[n]

        for line in stat.traceback.format():
            print(line)

    # Small tool to validate refs are cleaned up. By default runs on post level shutdown signal
    __refs_to_check = []

    def CheckRefDebug(ref):
        """ Post level shutdown checks if reference is None. If not, indicates it's not cleaned up correctly!
        """
        # Store as weakref to not influence the garbage collection
        __refs_to_check.append(weakref.ref(ref))

    def ValidateRefsCleanedUp():
        global __refs_to_check, roots

        try:
            if srcmgr.DEVVERSION:
                # Force collection now to avoid false results
                gc.collect()

                for i, ref in enumerate(__refs_to_check):
                    inst = ref()
                    if inst is None:
                        # Cleaned up!
                        continue

                    cls = inst.__oldclass__ if hasattr(inst, '__oldclass__') else inst.__class__

                    debug_name = 'refdebug_%s_%d_%s' % ('client' if isclient else 'server', i, cls.__name__)
                    # Print ref count -1 because we hold a reference here after getting the weakref.
                    PrintWarning('Instance did not clean up correctly! %s. Ref count is: %d\n' % (debug_name, sys.getrefcount(inst)-1))
                    # Not cleaned up, but we expected it to be :(?
                    objgraph.show_backrefs([inst], filename='%s.png' % debug_name)
                    # Forward ref?
                    objgraph.show_refs([inst], filename='%s_forward.png' % debug_name)

                # Show potential leaking objects
                print('Potentially leaking objects: ')
                roots = objgraph.get_leaking_objects()
                print(objgraph.show_most_common_types(objects=roots))
        finally:
            __refs_to_check = []


    @concommand(prefix+'py_mem_check_refs_cleaned_up')
    def CCCheckRefsCleanedUp(args):
        ValidateRefsCleanedUp()

    @receiver(postlevelshutdown)
    def PostLevelShutdown(*args, **kwargs):
        ValidateRefsCleanedUp()