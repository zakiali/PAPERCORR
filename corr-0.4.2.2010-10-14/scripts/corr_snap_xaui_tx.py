#!/usr/bin/env python

'''
Grabs the contents of "snap_xaui_tx" for analysis.
Assumes 4 bit values for power calculations.
Assumes the correlator is already initialsed and running etc.

Author: Jason Manley

Revisions:
2010-01-13: JRM First revision

'''
import corr, time, numpy, struct, sys, logging, stats, socket

#brams
brams=['bram_msb','bram_lsb','bram_oob']
dev_name = 'snap_xaui_tx0'

# OOB signalling bit allocations:
ip_addr_bit_width = 32-5
ip_addr_bit_offset = 5
eof_bit = 4
sync_bit = 3
linkdn_bit = 2
mrst_bit = 1
pkt_err_bit=0

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


def feng_unpack(f,hdr_index,pkt_len,skip_indices):
    pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*hdr_index):(4*hdr_index)+4]+bram_dmp['bram_lsb'][f][(4*hdr_index):(4*hdr_index)+4])[0]
    pkt_mcnt =(pkt_64bit&((2**64)-(2**16)))>>16
    pkt_ant  = pkt_64bit&((2**16)-1)
    pkt_freq = pkt_mcnt%n_chans
    sum_polQ_r = 0
    sum_polQ_i = 0
    sum_polI_r = 0
    sum_polI_i = 0

    #average the packet contents - ignore first entry (header)
    for pkt_index in range(1,(pkt_len)):
        abs_index = hdr_index + pkt_index
        
        if skip_indices.count(abs_index)>0: 
            #print 'Skipped %i'%abs_index
            continue

        pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*abs_index):(4*abs_index)+4]+bram_dmp['bram_lsb'][f][(4*abs_index):(4*abs_index)+4])[0]


        for offset in range(0,64,16):
            polQ_r = (pkt_64bit & ((2**(offset+16)) - (2**(offset+12))))>>(offset+12)
            polQ_i = (pkt_64bit & ((2**(offset+12)) - (2**(offset+8))))>>(offset+8)
            polI_r = (pkt_64bit & ((2**(offset+8)) - (2**(offset+4))))>>(offset+4)
            polI_i = (pkt_64bit & ((2**(offset+4)) - (2**(offset))))>>offset

            #square each number and then sum it
            sum_polQ_r += (float(((numpy.int8(polQ_r << 4)>> 4)))/(2**binary_point))**2
            sum_polQ_i += (float(((numpy.int8(polQ_i << 4)>> 4)))/(2**binary_point))**2
            sum_polI_r += (float(((numpy.int8(polI_r << 4)>> 4)))/(2**binary_point))**2
            sum_polI_i += (float(((numpy.int8(polI_i << 4)>> 4)))/(2**binary_point))**2
        
        #print 'Processed %i. Sum Qr now %f...'%(abs_index, sum_polQ_r)

    num_accs = (pkt_len-len(skip_indices))*(64/16)

    level_polQ_r = numpy.sqrt(float(sum_polQ_r)/ num_accs)
    level_polQ_i = numpy.sqrt(float(sum_polQ_i)/ num_accs)
    level_polI_r = numpy.sqrt(float(sum_polI_r)/ num_accs)
    level_polI_i = numpy.sqrt(float(sum_polI_i)/ num_accs)

    rms_polQ = numpy.sqrt(((level_polQ_r)**2)  +  ((level_polQ_i)**2))
    rms_polI = numpy.sqrt(((level_polI_r)**2)  +  ((level_polI_i)**2))
        
    if level_polQ_r < 1.0/(2**num_bits):
        ave_bits_used_Q_r = 0
    else:
        ave_bits_used_Q_r = numpy.log2(level_polQ_r*(2**(num_bits)))

    if level_polQ_i < 1.0/(2**num_bits):
        ave_bits_used_Q_i = 0
    else:
        ave_bits_used_Q_i = numpy.log2(level_polQ_i*(2**(num_bits)))

    if level_polI_r < 1.0/(2**num_bits):
        ave_bits_used_I_r = 0
    else:
        ave_bits_used_I_r = numpy.log2(level_polI_r*(2**(num_bits)))

    if level_polI_i < 1.0/(2**num_bits):
        ave_bits_used_I_i = 0
    else:
        ave_bits_used_I_i = numpy.log2(level_polI_i*(2**(num_bits)))

    return {'pkt_mcnt': pkt_mcnt,\
            'pkt_ant':pkt_ant,\
            'pkt_freq':pkt_freq,\
            'rms_polQ':rms_polQ,\
            'rms_polI':rms_polI,\
            'level_polQ_r':level_polQ_r,\
            'level_polQ_i':level_polQ_i,\
            'level_polI_r':level_polI_r,\
            'level_polI_i':level_polI_i,\
            'ave_bits_used_Q_r':ave_bits_used_Q_r,\
            'ave_bits_used_Q_i':ave_bits_used_Q_i,\
            'ave_bits_used_I_r':ave_bits_used_I_r,\
            'ave_bits_used_I_i':ave_bits_used_I_i}
    

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('snap_xaui.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-t', '--man_trigger', dest='man_trigger', action='store_true',
        help='Trigger the snap block manually')   
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Print raw output.')  
    p.add_option('-r', '--n_retries', dest='n_retries', type='int', default=-1,
        help='Number of times to try after an error before giving up. Set to -1 for infinity. Default: -1')
    p.add_option('-c', '--raw', dest='raw', action='store_true',
        help='Capture clock-for-clock data (ignore external valids on snap block).')

 
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

    n_retries = opts.n_retries
    if opts.man_trigger: man_trigger=True
    else: man_trigger=False

report=[]
lh=corr.log_handlers.DebugLogHandler()

try:
    print 'Parsing configuration file...',
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    binary_point = c.config['feng_fix_pnt_pos']
    packet_len=c.config['10gbe_pkt_len']
    n_chans=c.config['n_chans']
    num_bits = c.config['feng_bits']
    adc_bits = c.config['adc_bits']
    adc_levels_acc_len = c.config['adc_levels_acc_len']
    report = dict()
    n_ants = c.config['n_ants']
    n_ants_per_ibob=c.config['n_ants_per_xaui']
    servers = [s['server'] for s in c.config['servers']]

    if num_bits != 4:
        print 'This script is only written to work with 4 bit quantised values.'
        exit()

    print '------------------------'
    print 'Grabbing snap data...',
    bram_dmp=c.snap_x(dev_name,brams,man_trig=man_trigger,wait_period=2)
    print 'done'
    
    print 'Unpacking bram out of band contents...',
    sys.stdout.flush()
    bram_oob=dict()
    for f,server in enumerate(c.servers):
        if len(bram_dmp[brams[2]][f])<=4:
            print '\n   No data for X engine %s.'%server
            bram_oob[f]={}
        else:
            if opts.verbose:
                print '\n   Got %i values from %s.'%(len(bram_dmp[brams[2]][f])/4,server)
            bram_oob[f]={'raw':struct.unpack('>%iL'%(len(bram_dmp[brams[2]][f])/4),bram_dmp[brams[2]][f])}
            #print bram_oob[f]['raw']
            bram_oob[f].update({'linkdn':[bool(i&(2**linkdn_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'mrst':[bool(i&(2**mrst_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'pkt_err':[bool(i & (2**pkt_err_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'eof':[bool(i & (2**eof_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'sync':[bool(i&(2**sync_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'ip_addr':[(i&pkt_ip_mask)>>ip_addr_bit_offset for i in bram_oob[f]['raw']]})

    print 'Done.'

    print 'Analysing packets...'

    for f,server in enumerate(c.servers):
        print c.servers[f] + ': '
        report[f]=dict()
        report[f]['pkt_total']=0
        pkt_len = 0
        prev_eof_index=-1

        for i in range(0,len(bram_dmp[brams[2]][f])/4):
            ip_addr=socket.inet_ntop(socket.AF_INET,struct.pack('>I',bram_oob[f]['ip_addr'][i]))
            if opts.verbose:
                pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*i):(4*i)+4]+bram_dmp['bram_lsb'][f][(4*i):(4*i)+4])[0]
                print '[%s @ %4i]: %016X, destination %s'%(c.servers[f],i,pkt_64bit,ip_addr),
                if bram_oob[f]['mrst'][i]: print '[MRST]'
                if bram_oob[f]['eof'][i]: print '[EOF]'
                if bram_oob[f]['sync'][i]: print '[SYNC]'
                print '' 

            if bram_oob[f]['linkdn'][i]: print '[LINK DOWN]',
            if bram_oob[f]['pkt_err'][i]: print '[PKT_ERR]',

            if bram_oob[f]['eof'][i] and not opts.raw:
                print '[%s] EOF at %4i. Dest: %12s. Len: %3i. '%(servers[f],i,ip_addr,i-prev_eof_index),
                report[f]['pkt_total']+=1
                hdr_index=prev_eof_index+1
                pkt_len=i-prev_eof_index
                prev_eof_index=i

                if not report[f].has_key('dest_ips'):
                    report[f].update({'dest_ips':{ip_addr:1}})
                elif report[f]['dest_ips'].has_key(ip_addr):
                    report[f]['dest_ips'][ip_addr] += 1
                else:
                    report[f]['dest_ips'].update({ip_addr:1})


                if pkt_len != packet_len+1:
                    print 'Malformed Fengine Packet'
                    if not report[f].has_key('Malformed F-engine Packets'):
                        report[f]['Malformed F-engine Packets'] = 1
                    else:
                        report[f]['Malformed F-engine Packets'] += 1

                else:
                    feng_unpkd_pkt=feng_unpack(f,hdr_index,pkt_len,skip_indices=[])

                    ## Record the reception of the packet for this antenna, with this mcnt
                    #try: mcnts[f][feng_unpkd_pkt['pkt_mcnt']][feng_unpkd_pkt['pkt_ant']]=i
                    #except: 
                    #    mcnts[f][feng_unpkd_pkt['pkt_mcnt']]=numpy.zeros(n_ants,numpy.int)
                    #    mcnts[f][feng_unpkd_pkt['pkt_mcnt']][feng_unpkd_pkt['pkt_ant']]=i
                    #print mcnts
                    print 'HDR @ %4i. MCNT %12u. Ant: %3i. 4 bit power: PolQ: %4.2f, PolI: %4.2f'%(hdr_index,feng_unpkd_pkt['pkt_mcnt'],feng_unpkd_pkt['pkt_ant'],feng_unpkd_pkt['rms_polQ'],feng_unpkd_pkt['rms_polI'])

                    if not report[f].has_key('Antenna%i'%feng_unpkd_pkt['pkt_ant']):
                        report[f]['Antenna%i'%feng_unpkd_pkt['pkt_ant']] = 1
                    else:
                        report[f]['Antenna%i'%feng_unpkd_pkt['pkt_ant']] += 1

    print '\n\nDone with all servers.\nSummary:\n==========================' 

    for server,srvr in enumerate(c.servers):
        keys = report[server].keys()
        keys.sort()
        print '------------------------'
        print srvr
        print '------------------------'
        for key in keys:
            print key,': ',report[server][key]
    print '=========================='

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

