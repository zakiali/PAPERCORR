#!/usr/bin/env python

'''
Grabs the contents of "snap_loopback_mux" for analysis. Valid for rev310 and onwards only. This has no OOB capturing.
Assumes the correlator is already initialsed and running etc.

'''
import corr, time, numpy, struct, sys, logging

#brams
brams=['bram_msb','bram_lsb','bram_oob']
#dev_name = 'descramble_window0_snap_in'
dev_name = 'snap_rx0'

# OOB signalling bit offsets:
ip_addr_bit_width = 8
ip_addr_bit_offset = 24
ant_bit_width = 7
ant_bit_offset = 17
mcnt_bit_width = 12
mcnt_bit_offset = 5
loop_ack_bit = 4
gbe_ack_bit = 3
valid_bit = 2
eof_bit = 1
flag_bit = 0


pkt_ip_mask = (2**(ip_addr_bit_width+ip_addr_bit_offset)) -(2**ip_addr_bit_offset)
ant_mask = (2**(ant_bit_width+ant_bit_offset)) -(2**ant_bit_offset)
mcnt_mask = (2**(mcnt_bit_width+mcnt_bit_offset)) -(2**mcnt_bit_offset)

def ip2str(pkt_ip):
    ip_4 = (pkt_ip&((2**32)-(2**24)))>>24
    ip_3 = (pkt_ip&((2**24)-(2**16)))>>16
    ip_2 = (pkt_ip&((2**16)-(2**8)))>>8
    ip_1 = (pkt_ip&((2**8)-(2**0)))>>0
    #print 'IP:%i. decoded to: %i.%i.%i.%i'%(pkt_ip,ip_4,ip_3,ip_2,ip_1)
    return '%i.%i.%i.%i'%(ip_4,ip_3,ip_2,ip_1)    

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

def feng_unpack(f,hdr_index,pkt_len):
    #the loopback block unpacks the packet in firmware and removes the header from the data stream. Thus don't need to unpack here.
    #pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f]['data'][(4*hdr_index):(4*hdr_index)+4]+bram_dmp['bram_lsb'][f]['data'][(4*hdr_index):(4*hdr_index)+4])[0]
    #pkt_mcnt =(pkt_64bit&((2**64)-(2**16)))>>16
    #pkt_ant = pkt_64bit&((2**16)-1)

    sum_polQ_r = 0
    sum_polQ_i = 0
    sum_polI_r = 0
    sum_polI_i = 0

    #average the packet contents from the very first entry
    for pkt_index in range(0,(pkt_len)):
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
        ave_bits_used_Q_r = numpy.log2(level_polQ_r*(2**num_bits))

    if level_polQ_i < 1.0/(2**num_bits):
        ave_bits_used_Q_i = 0
    else:
        ave_bits_used_Q_i = numpy.log2(level_polQ_i*(2**num_bits))

    if level_polI_r < 1.0/(2**num_bits):
        ave_bits_used_I_r = 0
    else:
        ave_bits_used_I_r = numpy.log2(level_polI_r*(2**num_bits))

    if level_polI_i < 1.0/(2**num_bits):
        ave_bits_used_I_i = 0
    else:
        ave_bits_used_I_i = numpy.log2(level_polI_i*(2**num_bits))

    return {'rms_polQ':rms_polQ,\
            'rms_polI':rms_polI,\
            'ave_bits_used_Q_r':ave_bits_used_Q_r,\
            'ave_bits_used_Q_i':ave_bits_used_Q_i,\
            'ave_bits_used_I_r':ave_bits_used_I_r,\
            'ave_bits_used_I_i':ave_bits_used_I_i}


if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('snap_10gbe_tx.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-t', '--man_trigger', dest='man_trigger', action='store_true',
        help='Trigger the snap block manually')   
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Print raw contents.')  
    p.add_option('-r', '--raw', dest='raw', action='store_true',
        help='Capture clock-for-clock data (ignore external valids on snap block).')
 
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
    print 'Connecting...',
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    print '------------------------'
    print 'Grabbing snap data...',
    bram_dmp=c.snap_x(dev_name,brams,man_trig=man_trig,man_valid=man_valid,wait_period=2)
    print 'done'

    servers = c.servers
    fpgas = c.fpgas
    binary_point = c.config['feng_fix_pnt_pos']
    num_bits = c.config['feng_bits']
    packet_len=c.config['10gbe_pkt_len']
    n_ants=c.config['n_ants']
    n_chans=c.config['n_chans']
    header_len=1

    print 'Unpacking bram contents...',
    sys.stdout.flush()
    bram_oob=dict()
    for f,fpga in enumerate(fpgas):
        sys.stdout.flush()
        bram_oob[f]={'raw':struct.unpack('>%iL'%(len(bram_dmp[brams[2]][f])/4),bram_dmp[brams[2]][f])}
        bram_oob[f].update({'eof':[bool(i & (2**eof_bit)) for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'flag':[bool(i & (2**flag_bit)) for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'valid':[bool(i & (2**valid_bit)) for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'gbe_ack':[bool(i & (2**gbe_ack_bit)) for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'loop_ack':[bool(i & (2**loop_ack_bit)) for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'ip_addr':[(i&pkt_ip_mask)>>ip_addr_bit_offset for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'ant':[(i&ant_mask)>>ant_bit_offset for i in bram_oob[f]['raw']]})
        bram_oob[f].update({'mcnt':[(i&mcnt_mask)>>mcnt_bit_offset for i in bram_oob[f]['raw']]})
        #print '\n\nFPGA %i, bramoob:'%f,bram_oob
    print 'Done unpacking.'

    if opts.verbose:
        for f,fpga in enumerate(fpgas):
            for i in range(len(bram_dmp[brams[0]][f])/4):
                pkt_64bit = struct.unpack('>Q',bram_dmp['bram_msb'][f][(4*i):(4*i)+4]+bram_dmp['bram_lsb'][f][(4*i):(4*i)+4])[0]
                pkt_ip_str = ip2str(bram_oob[f]['ip_addr'][i])
                pkt_mcnt=bram_oob[f]['mcnt'][i]
                pkt_ant=bram_oob[f]['ant'][i]
                print '[%s]'%(servers[f]),
                print 'IDX: %6i IP: %s. MCNT: %6i. ANT: %4i.  Contents: %016x'%(i,pkt_ip_str,pkt_mcnt,pkt_ant,pkt_64bit),
                if bram_oob[f]['valid'][i]: print '[VALID]',
                if bram_oob[f]['flag'][i]: print '[FLAG BAD]',
                if bram_oob[f]['gbe_ack'][i]: print '[GBE ]',
                if bram_oob[f]['loop_ack'][i]: print '[Loop]',
                if bram_oob[f]['eof'][i]: print '[EOF!]'
                else: print ''
                

    report = dict()
    mcnts = dict()

    print 'Analysing packets:'
    for f,fpga in enumerate(fpgas):
        report[f]=dict()
        mcnts[f]=dict()
        report[f]['pkt_total']=0
        pkt_len = 0
        prev_eof_index=-1

        for i in range(len(bram_dmp[brams[2]][f])/4):
            if bram_oob[f]['eof'][i]:

                pkt_ip_str = ip2str(bram_oob[f]['ip_addr'][i])
                pkt_mcnt=bram_oob[f]['mcnt'][i]
                pkt_ant=bram_oob[f]['ant'][i]
                pkt_freq=bram_oob[f]['mcnt'][i]%n_chans
                hdr_index=prev_eof_index+1
                pkt_len=i-prev_eof_index

                print '[%s] EOF at %4i. IP: %12s. MCNT: %6i. Freq: %4i ANT: %4i. Len: %3i. '%(servers[f],i,pkt_ip_str,pkt_mcnt,pkt_freq,pkt_ant,pkt_len),
                if bram_oob[f]['gbe_ack'][hdr_index]: print '[GBE ]',
                if bram_oob[f]['loop_ack'][hdr_index]: print '[Loop]',

                report[f]['pkt_total']+=1

                if prev_eof_index > 0:
                    #Check to make sure the packet length is correct. Don't process if it's bad.
                    if pkt_len != packet_len:
                        print '[BAD PKT LEN]'
                        if not report[f].has_key('bad_pkt_len'):
                            report[f]['bad_pkt_len'] ={'cnt': 1, 'bad_mcnts':[pkt_mcnt]}
                        else:
                            report[f]['bad_pkt_len']['cnt'] += 1
                            report[f]['bad_pkt_len']['bad_mcnts'].append(pkt_mcnt)
                    else:
                        feng_unpkd_pkt=feng_unpack(f,hdr_index,pkt_len)
                        #Check to make sure the hardware unpacker correctly held MCNT constant for the entire packet length:
                        first_mcnt = bram_oob[f]['mcnt'][hdr_index]
                        for pkt_index in range(hdr_index,hdr_index+pkt_len):
                            if first_mcnt != bram_oob[f]['mcnt'][pkt_index]:
                                print '[MCNT ERR]',
                                if not report[f].has_key('mcnt_errors'):
                                    report[f]['mcnt_errors']={'cnt':1, 'bad_mcnts':[pkt_mcnt]}
                                else:
                                    report[f]['mcnt_errors']['cnt'] += 1
                                    report[f]['mcnt_errors']['bad_mcnts'].append(pkt_mcnt)

                        try: mcnts[f][pkt_mcnt][pkt_ant]=i
                        except:
                            mcnts[f][pkt_mcnt]=numpy.ones(n_ants,numpy.int)*(-1)
                            mcnts[f][pkt_mcnt][pkt_ant]=i
                        #print mcnts

                        if not report[f].has_key('dest_ips'):
                            report[f].update({'dest_ips':{pkt_ip_str:1}})
                        elif report[f]['dest_ips'].has_key(pkt_ip_str):
                            report[f]['dest_ips'][pkt_ip_str] += 1
                        else:
                            report[f]['dest_ips'].update({pkt_ip_str:1})


                        try: mcnts[f][pkt_mcnt][pkt_ant]=i
                        except:
                            mcnts[f][pkt_mcnt]=numpy.ones(n_ants,numpy.int)*(-1)
                            mcnts[f][pkt_mcnt][pkt_ant]=i
                        #print mcnts

                        print 'HDR @ %4i. 4 bit power: PolQ: %4.2f, PolI: %4.2f'%(hdr_index,feng_unpkd_pkt['rms_polQ'],feng_unpkd_pkt['rms_polI'])

                        if not report[f].has_key('Antenna%02i'%pkt_ant):
                            report[f]['Antenna%02i'%pkt_ant] = 1
                        else:
                            report[f]['Antenna%02i'%pkt_ant] += 1
                else: print 'skipped first packet.'
                prev_eof_index=i


        rcvd_mcnts = mcnts[f].keys()
        rcvd_mcnts.sort()
        if opts.verbose: print '[%s] Received mcnts: '%servers[f],rcvd_mcnts
        report[f]['min_pkt_latency']=9999
        report[f]['max_pkt_latency']=-1
        for i in rcvd_mcnts[1:-1]:
            max_mcnt = mcnts[f][i].max()/pkt_len
            min_mcnt = mcnts[f][i].min()/pkt_len

            #check to ensure that we received all data for each mcnt:
            if mcnts[f][i].min() < 0:
                if not report[f].has_key('missing_mcnts'):  report[f]['missing_mcnts']=[i]
                else: report[f]['missing_mcnts'].append(i)
                if opts.verbose:
                    print """[%s] We're missing data for mcnt %016i from antennas """%(servers[f],i),
                    for ant in range(n_ants):
                        if mcnts[f][i][ant] < 0: print ant,
                    print ''

            #check the latencies in the mcnt values:
            if opts.verbose: print '[%s] MCNT: %i. Max: %i, Min: %i. Diff: %i'%(servers[f],i,max_mcnt,min_mcnt,max_mcnt-min_mcnt)
            if (max_mcnt-min_mcnt)>0:
                if report[f]['max_pkt_latency']<(max_mcnt-min_mcnt) and min_mcnt>0: report[f]['max_pkt_latency']=max_mcnt-min_mcnt
                if report[f]['min_pkt_latency']>(max_mcnt-min_mcnt) and min_mcnt>0: report[f]['min_pkt_latency']=max_mcnt-min_mcnt

    print 'Done with all servers. '

    print '\n REPORT:'
    

    print '\n\nDone with all servers.\nSummary:\n==========================' 
    for server,srvr in enumerate(servers):
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


