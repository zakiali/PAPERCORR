#!/usr/bin/env python

'''
Grabs the contents of "snap_gbe_tx" for analysis.
Assumes the correlator is already initialsed and running etc.
Revisions
2009-12-01  JRM uses katcp_wrapper function now.
2009/11/12  JRM after discussion with Dave.
'''
import corr, time, numpy, struct, sys, logging

gbe_device='gbe0'

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

def ip2str(pkt_ip):
    ip_4 = (pkt_ip&((2**32)-(2**24)))>>24
    ip_3 = (pkt_ip&((2**24)-(2**16)))>>16
    ip_2 = (pkt_ip&((2**16)-(2**8)))>>8
    ip_1 = (pkt_ip&((2**8)-(2**0)))>>0
    #print 'IP:%i. decoded to: %i.%i.%i.%i'%(pkt_ip,ip_4,ip_3,ip_2,ip_1)
    return '%i.%i.%i.%i'%(ip_4,ip_3,ip_2,ip_1)    

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('snap_10gbe_tx.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Be Verbose; print raw packet contents of CPU contents.')   
    p.add_option('-r', '--n_retries', dest='n_retries', type='int', default=-1,
        help='Number of times to try after an error before giving up. Set to -1 for infinity. Default: -1')
    p.add_option('-a', '--arp', dest='arp', action='store_true',
        help='Print the ARP table.')

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
    #assemble struct for header stuff...
    #0x00 - 0x07: My MAC address
    #0x08 - 0x0b: Not used
    #0x0c - 0x0f: Gateway addr
    #0x10 - 0x13: my IP addr
    #0x14 - 0x17: Not assigned
    #0x18 - 0x1b: Buffer sizes
    #0x1c - 0x1f: Not assigned
    #0x20       : soft reset (bit 0)
    #0x21       : fabric enable (bit 0)
    #0x22 - 0x23: fabric port 
    
    #0x24 - 0x27: XAUI status (bit 2,3,4,5=lane sync, bit6=chan_bond)
    #0x28 - 0x2b: PHY config
    #0x28       : RX_eq_mix
    #0x29       : RX_eq_pol
    #0x2a       : TX_preemph
    #0x2b       : TX_diff_ctrl

    #0x1000     : CPU TX buffer
    #0x2000     : CPU RX buffer
    #0x3000     : ARP tables start


    print '\n\n================================'
    for f,fpga in enumerate(c.fpgas):
        print c.servers[f]
        fpga.print_10gbe_core_details(gbe_device,arp=opts.arp,cpu=opts.verbose) 
    print '================================'



except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()


