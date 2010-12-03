#! /usr/bin/env python
""" 
Script for checking the approximate clock rate of all X engine FPGAs.

Author: Jason Manley
date: 01 July 2009
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
    p.set_usage('init_corr.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-m', '--monitor_only', dest='monitor_only', action='store_true', default=False, 
        help='Skip the initialision. ie Only monitor.')
    p.add_option('-t', '--init_time', dest='init_time',action='store_true', default=False, 
        help='Set the BEEs time from the timeserver specified in the config file.  Default: do not set time')
    p.add_option('-r', '--n_retries', dest='n_retries', type='int', default=-1, 
        help='Number of times to try and sync the system before giving up. Set to -1 for infinity. Default: -1')

    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

lh=corr.log_handlers.DebugLogHandler()

try:
    print 'Loading the configuration file %s...'%args[0],
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    print('\nCalculating all clocks...'),
    sys.stdout.flush()
    clks=c.get_xeng_clks()
    print 'done.'

    for s,server in enumerate(c.servers):
        print server+': %i MHz'%clks[s]

#    lh.printMessages()

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()


