#! /usr/bin/env python
""" 
Script for loading the casper_n correlator's X engine FPGAs. 

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
    #raise
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
    p.add_option('-f', '--fpga', dest='fpga', type='int', default=-1, 
        help='Program this fpga number (x engine board, ordering as defined in config file, zero-indexed). Set to -1 for all (default).')

    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

try:
    lh=corr.log_handlers.DebugLogHandler()
    print 'Loading the configuration file %s...'%args[0],
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    if (opts.fpga < 0):
        print('\nProgramming all FPGAs...'),
        sys.stdout.flush()
        c.prog_all()
        print 'done.'
    else:
        print('\nProgramming all FPGA %i: %s...'%(opts.fpga,c.servers[opts.fpga])),
        sys.stdout.flush()
        c.fpgas[opts.fpga].progdev(c.config['bitstream'])
        print 'done.'

#    lh.printMessages()

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()


