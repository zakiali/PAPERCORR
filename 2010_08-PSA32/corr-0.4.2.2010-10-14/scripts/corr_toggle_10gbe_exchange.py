#! /usr/bin/env python
"""Resets the cumulative error counters on the X engine.
Uses KatCP TCP protocol. Good for X engine rev 310b.
"""
import corr, time, sys, numpy, os, logging

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    print "Unexpected error:", sys.exc_info()

    try:
        c.disconnect_all()
    except: pass
    time.sleep(1)
    raise
    exit()

def exit_clean():
    try:
        c.disconnect_all()
    except: pass
    exit()

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('rst_errors.py CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-d', '--disable', dest='disable', action='store_true', default=False,
        help='Explicitly disable transmission on all 10GbE cores.')
    p.add_option('-e', '--enable', dest='enable',action='store_true', default=False,
        help='Explicitly enable transmission on all 10GbE cores.')

    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

lh=corr.log_handlers.DebugLogHandler()

try:
    print 'Connecting...',
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    if opts.disable:
        print('\nPausing 10GbE output...'),
        sys.stdout.flush()
        c.write_all_xeng_ctrl(gbe_disable=True)
        print 'done.'
    elif opts.enable:
        print('\nResuming 10GbE exchange...'),
        sys.stdout.flush()
        c.write_all_xeng_ctrl(gbe_disable=False)
        print 'done.'
    else:
        print 'Toggling current state'
        current_state=c.read_all_xeng_ctrl()[0]['gbe_disable']
        if not current_state:
            print('\nPausing 10GbE output...'),
            sys.stdout.flush()
            c.write_all_xeng_ctrl(gbe_disable=True)
            print 'done.'
        else:
            print('\nResuming 10GbE exchange...'),
            sys.stdout.flush()
            c.write_all_xeng_ctrl(gbe_disable=False)
            print 'done.'
                

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()
exit()
