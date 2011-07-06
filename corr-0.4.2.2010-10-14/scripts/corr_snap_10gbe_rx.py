#!/usr/bin/env python

'''
Grabs the contents of "snap_gbe_rx" for analysis.
Assumes the correlator is already initialsed and running etc.

'''
import corr, time, numpy, struct, sys, logging

#brams
brams=['bram_msb','bram_lsb','bram_oob']
dev_name = 'snap_gbe_rx0'

# OOB signalling bit offsets:
ip_addr_bit_width = 32-8
ip_addr_bit_offset = 7
led_up_bit = 6
led_rx_bit = 5
eof_bit = 4
rx_bad_frame_bit = 3
rx_over_bit = 2
valid_bit = 1
ack_bit = 0


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

def feng_unpack(f,hdr_index,pkt_len):
    pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*hdr_index):(4*hdr_index)+4]+bram_dmp['bram_lsb'][f][(4*hdr_index):(4*hdr_index)+4])[0]
    pkt_mcnt =(pkt_64bit&((2**64)-(2**16)))>>16
    pkt_ant = pkt_64bit&((2**16)-1)
    pkt_freq = pkt_mcnt%c.config['n_chans']
    pkt_xeng = pkt_freq%(c.config['x_per_fpga']*len(c.config['servers']))

    sum_polQ_r = 0
    sum_polQ_i = 0
    sum_polI_r = 0
    sum_polI_i = 0

    #average the packet contents - ignore first entry (header)
    for pkt_index in range(1,(pkt_len)):
        abs_index = hdr_index + pkt_index
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

    num_accs = (pkt_len-1)*(64/16)

    level_polQ_r = numpy.sqrt(float(sum_polQ_r)/ num_accs)
    level_polQ_i = numpy.sqrt(float(sum_polQ_i)/ num_accs)
    level_polI_r = numpy.sqrt(float(sum_polI_r)/ num_accs)
    level_polI_i = numpy.sqrt(float(sum_polI_i)/ num_accs)

    rms_polQ = numpy.sqrt(((level_polQ_r)**2)  +  ((level_polQ_i)**2))
    rms_polI = numpy.sqrt(((level_polI_r)**2)  +  ((level_polI_i)**2))

    if level_polQ_r < 1.0/(2**num_bits):
        ave_bits_used_Q_r = 0
    else:
        ave_bits_used_Q_r = numpy.log2(level_polQ_r*(2**binary_point))

    if level_polQ_i < 1.0/(2**num_bits):
        ave_bits_used_Q_i = 0
    else:
        ave_bits_used_Q_i = numpy.log2(level_polQ_i*(2**binary_point))

    if level_polI_r < 1.0/(2**num_bits):
        ave_bits_used_I_r = 0
    else:
        ave_bits_used_I_r = numpy.log2(level_polI_r*(2**binary_point))

    if level_polI_i < 1.0/(2**num_bits):
        ave_bits_used_I_i = 0
    else:
        ave_bits_used_I_i = numpy.log2(level_polI_i*(2**binary_point))

    return {'pkt_mcnt': pkt_mcnt,\
            'pkt_ant':pkt_ant,\
            'pkt_freq':pkt_freq,\
            'pkt_xeng':pkt_xeng,\
            'rms_polQ':rms_polQ,\
            'rms_polI':rms_polI,\
            'ave_bits_used_Q_r':ave_bits_used_Q_r,\
            'ave_bits_used_Q_i':ave_bits_used_Q_i,\
            'ave_bits_used_I_r':ave_bits_used_I_r,\
            'ave_bits_used_I_i':ave_bits_used_I_i}



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

    print '------------------------'
    print 'Grabbing snap data...',
    bram_dmp=c.snap_x(dev_name,brams,man_trig=man_trig,man_valid=man_valid,wait_period=2)
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
            bram_oob[f].update({'led_up':[bool(i & (2**led_up_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'led_rx':[bool(i & (2**led_rx_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'bad_frame':[bool(i & (2**rx_bad_frame_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'overflow':[bool(i & (2**rx_over_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'valid':[bool(i & (2**valid_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'ack':[bool(i & (2**ack_bit)) for i in bram_oob[f]['raw']]})
            bram_oob[f].update({'ip_addr':[(i&pkt_ip_mask)>>ip_addr_bit_offset for i in bram_oob[f]['raw']]})
            #print '\n\nFPGA %i, bramoob:'%f,bram_oob
    print 'Done unpacking.'

    mcnts = dict()
    base_ants=[[x for x in range(c.config['n_xaui_ports_per_fpga'])] for f in c.fpgas]
    ant=0
    for x in range(c.config['n_xaui_ports_per_fpga']):
        for f,fpga in enumerate(c.fpgas):
            base_ants[f][x]=ant
            ant += c.config['n_ants_per_xaui']

    print 'Analysing packets:'
    for f,fpga in enumerate(c.fpgas):
        report[f]=dict()
        mcnts[f]=dict()
        report[f]['pkt_total']=0
        pkt_len = 0
        prev_eof_index=-1

        for i in range(len(bram_dmp[brams[2]][f])/4):
            if opts.verbose or opts.raw:
                pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*i):(4*i)+4]+bram_dmp['bram_lsb'][f][(4*i):(4*i)+4])[0]
                print '[%s] IDX: %4i Contents: %016x'%(servers[f],i,pkt_64bit),
                if bram_oob[f]['led_rx'][i]: print '[rx_data]',
                if bram_oob[f]['valid'][i]: print '[valid]',
                if bram_oob[f]['ack'][i]: print '[rd_ack]',
                if not bram_oob[f]['led_up'][i]: print '[LNK DN]',
                if bram_oob[f]['bad_frame'][i]: print '[BAD FRAME]',
                if bram_oob[f]['overflow'][i]: print '[OVERFLOW]',
                if bram_oob[f]['eof'][i]: print '[eof]',
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

                if pkt_len != packet_len+1:
                    print '[BAD PKT LEN]'
                    if not report[f].has_key('bad_pkt_len'):
                        report[f]['bad_pkt_len'] = 1
                    else:
                        report[f]['bad_pkt_len'] += 1

                else:
                    feng_unpkd_pkt=feng_unpack(f,hdr_index,pkt_len)
                    
                    # Record the reception of the packet for this antenna, with this mcnt
                    try: mcnts[f][feng_unpkd_pkt['pkt_mcnt']][feng_unpkd_pkt['pkt_ant']]=i
                    except: 
                        mcnts[f][feng_unpkd_pkt['pkt_mcnt']]=numpy.ones(n_ants,numpy.int)*(-1)
                        mcnts[f][feng_unpkd_pkt['pkt_mcnt']][feng_unpkd_pkt['pkt_ant']]=i
                    #print mcnts


                    print 'HDR @ %4i. MCNT %12u. Ant: %3i. Freq: %4i. Xeng: %2i, 4 bit power: PolQ: %4.2f, PolI: %4.2f'%(hdr_index,feng_unpkd_pkt['pkt_mcnt'],feng_unpkd_pkt['pkt_ant'],feng_unpkd_pkt['pkt_freq'],feng_unpkd_pkt['pkt_xeng'],feng_unpkd_pkt['rms_polQ'],feng_unpkd_pkt['rms_polI'])

                    if not report[f].has_key('Antenna%i'%feng_unpkd_pkt['pkt_ant']):
                        report[f]['Antenna%i'%feng_unpkd_pkt['pkt_ant']] = 1
                    else:
                        report[f]['Antenna%i'%feng_unpkd_pkt['pkt_ant']] += 1


        rcvd_mcnts = mcnts[f].keys()
        rcvd_mcnts.sort()

        if opts.verbose: print '[%s] Received mcnts: '%servers[f],rcvd_mcnts
        report[f]['min_pkt_latency']=99999999
        report[f]['max_pkt_latency']=-1

        for mcnt in rcvd_mcnts[2:-2]:
            #simulate the reception of the loopback antenna's mcnts, but only for the x engines that actually have connected f engines:
            if f < (c.config['n_ants']/c.config['n_ants_per_xaui']/c.config['n_xaui_ports_per_fpga']):
                print 'Replacing antennas on FPGA %s for mcnt %i'%(c.servers[f],mcnt)
                for a in range(base_ants[f][0],base_ants[f][0]+c.config['n_ants_per_xaui']): mcnts[f][mcnt][a]=mcnts[f][mcnt].max()

            #find the min and max indices of each mcnt:
            max_mcnt = mcnts[f][mcnt].max()/pkt_len
            min_mcnt = mcnts[f][mcnt].min()/pkt_len

            #check to ensure that we received all data for each mcnt, by looking for any indices that weren't recorded:
            if mcnts[f][mcnt].min() < 0:
                if not report[f].has_key('missing_mcnts'):  report[f]['missing_mcnts']=[mcnt]
                else: report[f]['missing_mcnts'].append(mcnt)
                if opts.verbose:
                    print """[%s] We're missing data for mcnt %016i from antennas """%(servers[f],mcnt),
                    for ant in range(n_ants):
                        if mcnts[f][mcnt][ant] < 0: print ant,
                    print ''

            #check the latencies in the mcnt values:
            if opts.verbose: print '[%s] MCNT: %i. Max: %i, Min: %i. Diff: %i'%(servers[f],mcnt,max_mcnt,min_mcnt,max_mcnt-min_mcnt)
            if (max_mcnt-min_mcnt)>0:
                if report[f]['max_pkt_latency']<(max_mcnt-min_mcnt) and min_mcnt>=0: report[f]['max_pkt_latency']=max_mcnt-min_mcnt
                if report[f]['min_pkt_latency']>(max_mcnt-min_mcnt) and min_mcnt>=0: report[f]['min_pkt_latency']=max_mcnt-min_mcnt


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
