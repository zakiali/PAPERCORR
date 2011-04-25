#!/usr/bin/env python

'''
\n\nNOT YET PORTED. UNTESTED AND INCOMPLETE.\n\n
Grabs the contents of "snap_xout0" (one per FPGA) at the output of the X eng
and prints any non-zero values.
Assumes the correlator is already initialsed and running etc.
Only good for 4 bit X engines with accumulation length of 128 and demux of 8.

'''

import corr, time, numpy, pylab, struct, sys, logging

#brams
brams=['bram']
dev_name = 'snap_pre_xeng0'

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

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('my_snap_pre_xeng_out.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-v', '--print_all', dest='print_all', action='store_true', 
        help='Print all the decoded results (be verbose).')
    p.add_option('-o', '--ch_offset', dest='ch_offset', type='int', default=0,
        help='Start capturing at specified channel number. Default is 0.')
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

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
    x_per_fpga = c.config['x_per_fpga']
    n_ants = c.config['n_ants']
    n_stokes = c.config['n_stokes']
    xeng_acc_len = c.config['xeng_acc_len']
    n_bls = c.config['n_bls']

    report = dict()
    ch_offset = opts.ch_offset

    if num_bits !=4:
        print 'ERR: this script is only written to interpret 4 bit data. Your F engine outputs %i bits.'%num_bits
        exit_fail()
    if xeng_acc_len !=128:
        print 'ERR: this script is only written to interpret data from X engines with acc length of 128. Your X engine accumulates for %i samples.'%xeng_acc_len
        exit_fail()

    print '------------------------'
    print 'Triggering Capture...',
    offset = ch_offset*n_stokes*n_bls*2
    print "at offset %i..."%offset,
    sys.stdout.flush()
    bram_dmp=c.snap_x(dev_name,brams,man_trig=False,wait_period=2,offset=offset)
    print 'Done.'

    print 'Unpacking bram contents...'
   #hardcode unpack of 16 bit values. Assumes bitgrowth of log2(128)=7 bits and input of 4_3 * 4_3.
    sys.stdout.flush()
    bram_data=[]
    for f,fpga in enumerate(c.fpgas):
        unpack_length=(bram_dmp['lengths'][f])
        print " Unpacking %i values from %s."%(unpack_length,c.servers[f])
        if unpack_length>0:
            #unpack length is multiplied by two because of the "short" fmt(h).
            bram_data.append(struct.unpack('>%ih'%(unpack_length*2), bram_dmp[brams[0]][f]))
            print bram_data
        else:
            print ' Got no data back for %s.'%c.servers[f]
            bram_data.append([])
    print 'Done.'
    print '========================\n'

    for f,fpga in enumerate(c.fpgas):
        xeng=f
        print '--------------------'
        print '\nX engine %i'%(xeng)
        print '--------------------'
        for li in range(len(bram_data[f])/2):
            #index over complex numbers in bram
            index = li + bram_dmp['offsets'][f]/2
            stokes = index%n_stokes
            bls_index=(index/n_stokes)%n_bls
            freq=(index/n_stokes/n_bls)*x_per_fpga*len(c.fpgas) + xeng
            i,j=corr.sim_cn_data.bl2ij(corr.sim_cn_data.get_bl_order(n_ants)[bls_index])
            real_val = bram_data[f][li*2]
            imag_val = bram_data[f][li*2+1]
            print '[%s] [%4i]: Freq: %i. bls: %2i_%2i. Stokes: %i. Raw value: 0x%05x + 0x%05xj (%6i + %6ij).'%(c.servers[f], index, freq, i,j, stokes, real_val,imag_val,real_val,imag_val)
        print 'Done with %s, X engine %i'%(c.servers[f],xeng)
    print 'Done with all'

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

