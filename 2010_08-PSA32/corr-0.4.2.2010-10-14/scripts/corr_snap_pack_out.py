#!/usr/bin/env python

'''
Grabs the contents of "snap_pack_out" for analysis.
Assumes the correlator is already initialsed and running etc.

'''
import corr, time, numpy, struct, sys, logging

#brams
brams=['bram_msb','bram_lsb','bram_oob']
dev_name = 'snap_pack_out'

# OOB signalling bit offsets:
ip_addr_bit_width = 32-3
ip_addr_bit_offset = 3
eof_bit = 2
discard_bit = 1
valid_bit = 0

pkt_ip_mask = (2**(ip_addr_bit_width+ip_addr_bit_offset)) -(2**ip_addr_bit_offset)

def exit_fail():
    print 'FAILURE DETECTED. Log entries:\n',lh.printMessages()
    print "Unexpected error:", sys.exc_info()
    try:
        c.disconnect_all()
    except: pass
    raise
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

def spead_unpack(f,hdr_index,pkt_len):
    pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*hdr_index):(4*hdr_index)+4]+bram_dmp['bram_lsb'][f][(4*hdr_index):(4*hdr_index)+4])[0]

    #check magic number
    if (pkt_64bit[0]&((2**64)-(2**48))>>48)==0x4b52:
        print 'SPEAD pkt @ %10i:'%hdr_index,
        spead_ver = pkt_64bit[0]&((2**48)-(2**32))>>32
        spead_rsvd= pkt_64bit[0]&((2**32)-(2**16))>>16
        n_opts    = pkt_64bit[0]&((2**16)-(2**0))
        
        for i in range(n_opts): 
            opt_id  = pkt_64bit[i]&((2**64)-(2**48))>>48
            opt_val = pkt_64bit[i]&((2**48)-1)
            if   opt_id == 0x0000: print '[NULL]',
            elif opt_id == 0x0001: print '[Instr type: 0x%12X]'%opt_val,
            elif opt_id == 0x0002: print '[Instanc ID: 0x%12X]'%opt_val,
            elif opt_id == 0x0003: print '[Timestamp : 0x%12X]'%opt_val,
            elif opt_id == 0x0004: print '[Payld len : 0x%12X]'%opt_val,
            elif opt_id == 0x0005: print '[Payld ofst: 0x%12X]'%opt_val,
            elif opt_id == 0x000D: print '[Strm  ctrl: 0x%12X]'%opt_val,
            elif opt_id == 0x000E: print '[Metapktcnt: 0x%12X]'%opt_val,
            elif opt_id == 0x0030: print '[Optn descr: 0x%12X]'%opt_val,
            elif opt_id == 0x0031: print '[Pyld descr: 0x%12X]'%opt_val,
            else: print 'Got unkown option 0x%i at local index %4i: 0x%12X'%(opt_id,i,opt_val),

        print ''

        for i in range(pkt_len-n_opts-1):
            print 'Processing some data' 

        return {'ver':spead_ver,
                'rsvd':spead_rsvd,
                'n_opts': n_opts}

    else: 
        print 'Got a bad pkt at global index %i.'%hdr_index
        return


    




if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('snap_gbe_rx.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-r', '--raw', dest='raw', action='store_true',
        help='Capture clock-for-clock data (ignore external valids on snap block).')   
    p.add_option('-t', '--man_trigger', dest='man_trigger', action='store_true',
        help='Trigger the snap block manually')   
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Be Verbose; print raw packet contents.')   

    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()


    if opts.man_trigger:
        man_trig=True
    else:
        man_trig=False

    if opts.raw:
        man_valid=True
    else:
        man_valid=False

lh=corr.log_handlers.DebugLogHandler()

try:
    print 'Loading the configuration file %s...'%args[0],
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    if opts.man_trigger:
        man_ctrl = (1<<1)+1
    else:        man_ctrl = 1
    if opts.raw:
        man_ctrl += (1<<2)

    report = dict()
    binary_point = c.config['feng_fix_pnt_pos']
    num_bits = c.config['feng_bits']
    packet_len=c.config['10gbe_pkt_len']
    n_ants = c.config['n_ants']
    n_ants_per_ibob=c.config['n_ants_per_xaui']
    servers = [s['server'] for s in c.config['servers']]
    
    wait_time=c.config['int_time']*4

    print 'Waiting up to %2.2f seconds for snap data to become available.'%wait_time

    print '------------------------'
    print 'Grabbing snap data...',
    bram_dmp=c.snap_x(dev_name,brams,man_trig=man_trig,man_valid=man_valid,wait_period=wait_time)
    print 'done'

    #print 'BRAM DUMPS:'
    #print bram_dmp

    print 'Unpacking bram contents...',
    sys.stdout.flush()
    bram_oob=dict()
    for f,fpga in enumerate(c.fpgas):
        if bram_dmp['lengths'][f] ==0:
            print '\tERR: received nothing on %s.'%servers[f]
        else:
            bram_oob[f]={'raw':struct.unpack('>%iL'%(len(bram_dmp[brams[2]][f])/4),bram_dmp[brams[2]][f])}
            bram_oob[f].update({'eof':[bool(i & (2**eof_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'discard':[bool(i & (2**discard_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'valid':[bool(i & (2**valid_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'ip_addr':[(i&pkt_ip_mask)>>ip_addr_bit_offset for i in bram_oob[f]['raw']]})
            print '\n\nFPGA %i got %i vectors, bramoob:'%(f,bram_dmp['lengths'][f]),bram_oob
    print 'Done unpacking.'

    print 'Analysing packets:'
    for f,fpga in enumerate(c.fpgas):
        report[f]=dict()
        report[f]['pkt_total']=0
        pkt_len = 0
        prev_eof_index=-1

        for i in range(len(bram_dmp[brams[2]][f])/4):
            if opts.verbose or opts.raw:
                pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*i):(4*i)+4]+bram_dmp['bram_lsb'][f][(4*i):(4*i)+4])[0]
                print '[%s] IDX: %4i Contents: %016x'%(servers[f],i,pkt_64bit),
                if bram_oob[f]['valid'][i]: print '[valid]',
                if bram_oob[f]['discard'][i]: print '[discard]',
                if bram_oob[f]['eof'][i]: print '[EOF]',
                print ''

            if bram_oob[f]['eof'][i] and not opts.raw:
                pkt_ip_str = ip2str(bram_oob[f]['ip_addr'][i])
                print '[%s] EOF at %4i. Src: %12s. Len: %3i. '%(servers[f],i,pkt_ip_str,i-prev_eof_index),
                report[f]['pkt_total']+=1
                hdr_index=prev_eof_index+1
                pkt_len=i-prev_eof_index
                prev_eof_index=i

                if not report[f].has_key('dest_ips'):
                    report[f].update({'dest_ips':{pkt_ip_str:1}})
                elif report[f]['dest_ips'].has_key(pkt_ip_str):
                    report[f]['dest_ips'][pkt_ip_str] += 1
                else:
                    report[f]['dest_ips'].update({pkt_ip_str:1})

    print 'Done with all servers. \n REPORT:'

    print '\n\nDone with all servers.\nSummary:\n=========================='

    for server,srvr in enumerate(servers):
        print '------------------------'
        print srvr
        print '------------------------'
        for key in report[server].iteritems():
            print key[0],': ',key[1]
    print '=========================='





except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()
