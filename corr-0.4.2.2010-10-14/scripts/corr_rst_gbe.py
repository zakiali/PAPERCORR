#! /usr/bin/env python
"""Resets the cumulative error counters on the X engine.
Uses KatCP TCP protocol. Good for X engine rev 310b.
"""
import corr, time, sys, numpy, os, logging

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
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
    p.add_option('-r', '--n_retries', dest='n_retries', type='int', default=-1,
        help='Number of times to try after an error before giving up. Set to -1 for infinity. Default: -1')
    p.add_option('-v', '--verbose', dest='verbose',action='store_true', default=False,
        help='Be verbose about errors.')

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

    print('\nResetting GBE cores counters...'),
    sys.stdout.flush()
    c.write_all_xeng_ctrl(gbe_rst=True)
    c.write_all_xeng_ctrl(gbe_rst=False)
    print 'done.'

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()
exit()
