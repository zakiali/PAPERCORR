#!/usr/bin/env python

'''
Reads the values of the RMS amplitude accumulators on the ibob through the X engine's XAUI connection.\n

Revisions:
1.2 JRM Support any number of antennas together with F engine 305 and X engine rev 322 and later.\n
1.1 JRM Requires F engine rev 302 or later and X engine rev 308 or later.\n

'''
import corr, time, numpy, struct, sys, logging

pols = ['x','y']

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
    p.set_usage('corr_adc_amplitudes.py [options] CONFIG FILE')
    p.add_option('-v', '--verbose', dest='verbose', action='store_true',
        help='Print raw output.')
    p.set_description(__doc__)
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

    servers = c.servers
    fpgas = c.fpgas
    n_ants_per_xaui = c.config['n_ants_per_xaui']
    n_xaui_ports_per_fpga = c.config['n_xaui_ports_per_fpga']
    adc_bits = c.config['adc_bits']
    adc_levels_acc_len = c.config['adc_levels_acc_len']

    #mem size is data, each 32 bit numbers * n_pols * n_ants_per_xaui
    mem_size = 4*2*n_ants_per_xaui
    if opts.verbose: print 'Grabbing %i bytes from adc_pwrs'%mem_size

    while(1):
        #get the data...    
        adcs=range(len(fpgas))
        for f in range((c.config['n_ants']/c.config['n_ants_per_xaui']/c.config['n_xaui_ports_per_fpga'])):
            fpga=c.fpgas[f]
            adcs[f]=range(n_xaui_ports_per_fpga)
            for x in range(n_xaui_ports_per_fpga):
                try:
                    adcs[f][x]={'ant_levels': fpga.read('ant_levels',mem_size)}
                except KeyboardInterrupt:
                    exit_clean()
                except:
                    print 'ERR retrieving data for adc on port %i on fpga %s.'%(x,servers[f])
                    adcs[f][x]={'ant_levels': -999999999}
                
                if opts.verbose: print '[%s] [xaui%i] raw adc_pwrs:'%(servers[f],x),adcs[f][x]['ant_levels']
    
    #unpack the data
        for f in range((c.config['n_ants']/c.config['n_ants_per_xaui']/c.config['n_xaui_ports_per_fpga'])):
            fpga=c.fpgas[f]
            for x in range(n_xaui_ports_per_fpga):
                adcs[f][x]['unpacked_data'] = struct.unpack('>%iI'%(2*n_ants_per_xaui), adcs[f][x]['ant_levels'])
                if opts.verbose: print '[%s] [xaui%i] unpacked adc_pwrs:'%(servers[f],x),adcs[f][x]['unpacked_data']
                for a in range(n_ants_per_xaui):
                    adcs[f][x][a]={}
                    for p,pol in enumerate(pols):
                        offset_of_interest = (2*a + p)
                        adcs[f][x][a]['pol_%s'%p]=adcs[f][x]['unpacked_data'][offset_of_interest]
                        #calculate RMS values:
                        adcs[f][x][a]['pol_%s_rms'%(p)] = (numpy.sqrt(adcs[f][x]['unpacked_data'][offset_of_interest]/(adc_levels_acc_len))/(2**adc_bits))
                        #calculate bits used:
                        if adcs[f][x][a]['pol_%s'%(p)] == 0:
                            adcs[f][x][a]['pol_%s_bits_used'%(p)] = 0        
                        else:    
                            adcs[f][x][a]['pol_%s_bits_used'%(p)] = (numpy.log2(adcs[f][x][a]['pol_%s_rms'%(p)] * (2**(adc_bits))))


        #print the output                
        time.sleep(1)
        #Move cursor home:
        print '%c[H'%chr(27)
        #clear the screen:
        print '%c[2J'%chr(27)
        print 'IBOB: ADC0 is bottom (furthest from power port), ADC1 is top (closest to power port).'
        for f in range((c.config['n_ants']/c.config['n_ants_per_xaui']/c.config['n_xaui_ports_per_fpga'])):
            for x in range(n_xaui_ports_per_fpga):
                print '''ADC amplitudes for F engine on %s's XAUI %i'''%(servers[f],x)
                print '------------------------------------------------'
                for a in range(n_ants_per_xaui):
                    for p,pol in enumerate(pols):
                        ant,ignore_pol = c.get_ant_index(f,x,a*2)
                        #print adcs[f][x][a]
                        print 'ADC%i pol %s (ant %i%s): %.3f (%2.2f bits used)'%(a,pol,ant,pol, adcs[f][x][a]['pol_%s_rms'%(p)],adcs[f][x][a]['pol_%s_bits_used'%(p)])
                print '--------------------'

except KeyboardInterrupt:
    exit_clean()
except:
    print ''

print 'Done with all'
exit_clean()
