#! /usr/bin/env python
"""Selects TVGs thoughout the correlator.\n
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

if  __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('rst_errors.py CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-r', '--n_retries', dest='n_retries', type='int', default=-1,
        help='Number of times to try after an error before giving up. Set to -1 for infinity. Default: -1')

    p.add_option('-s', '--sram_ct', dest='sram_ct', action='store_true',
        help='Enable the SRAM corner-turn TVG. You should see a ramp function at the XAUI port.')
    p.add_option('-f', '--fft', dest='fft', action='store_true',
        help='Enable the first FFT TVG which has a 4b input label and 4b frequency counter.')
    p.add_option('-c', '--fftc', dest='fftc', action='store_true',
        help='Enable the second FFT TVG which outputs a frequency counter over 16b.')
    p.add_option('-x', '--xeng', dest='xeng', action='store_true',
        help='Enable the Xeng counter TVG.')

    opts, args = p.parse_args(sys.argv[1:])
    
    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

    if opts.sram_ct:
        tvg_sram_ct=True
    else:
        tvg_sram_ct=False

    if opts.fft:
        tvg_fft=True
    else:
        tvg_fft=False

    if opts.fftc:
        tvg_fftc=True
    else:
        tvg_fftc=False

    if opts.xeng:
        tvg_xeng=True
    else:
        tvg_xeng=False

lh=corr.log_handlers.DebugLogHandler()

try:
    print 'Parsing configuration file...',
    c=corr.corr_functions.Correlator(args[0],lh)
    for s,server in enumerate(c.config['servers']): c.loggers[s].setLevel(10)
    print 'done.'

    print 'F engine TVGs:'
    if tvg_fft and not tvg_fftc:
        print('\tEnabling first FFT TVG...')
    if tvg_fftc and not tvg_fft:
        print('\tEnabling second FFT TVG...')
    if tvg_fft and tvg_fftc:
        print("\tYou can't have both FFT TVGs on at the same time.")
    if tvg_sram_ct:
        print('\tEnabling SRAM corner-turn TVG...')
    c.write_all_feng_ctrl(use_sram_tvg=tvg_sram_ct, use_fft_tvg1=tvg_fft, use_fft_tvg2=tvg_fftc)
    print 'done all F engine TVGs.'

    print '\nX engine TVGs:'
    if opts.xeng:
        print('\tEnabling Xeng TVG...'),
        c.sel_xeng_tvg(mode=1)
        print 'done Xengine TVG.'
    #elif opts.vacc:
    #    print('\tEnabling VACC TVG...')
    #    print 'done VACC TVG.'
    print 'done all X engine TVGs.'


except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

