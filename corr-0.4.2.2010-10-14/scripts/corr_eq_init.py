#! /usr/bin/env python
import corr, numpy,sys,os,time,logging

def re_equalize(self, thresh=.1, maxval=2**17-1, max_tries=10):
        """Automatically adjust equalization for maximum flatness around 4b pwr of 10."""
        print 'Equalizing'
        for i in range(max_tries):
            d = 0
            for bl in autos: d += read_acc(bl)
            d /= len(autos)
            neweq = numpy.sqrt(numpy.where(d > 0, 10/d, maxval))
            neweq *= equalization
            neweq = numpy.clip(neweq, 0, maxval)
            p = remove_spikes(numpy.log10(neweq+1e-5), return_poly=True)
            neweq = abs(10**numpy.polyval(p, numpy.arange(d.size)))
            neweq = numpy.clip(neweq, 0, maxval)
            fit = math.sqrt(numpy.average((1 - (neweq/equalization))**2))
            print '    Percent gain change:', fit, '(thresh=%f)\n' % thresh
            if fit < thresh: break
            equalization = numpy.round(neweq)
            _apply_eq(active_chans, equalization)
            curr_acc = self['acc_num']
            print '    Waiting for accumulation...'
            while self['acc_num'] <= curr_acc + 1: time.sleep(.01)

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


verbose_level=1
if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('conf_eq.py [options] CONFIG_FILE')
    p.set_description(__doc__)
    p.add_option('-i', '--init_eq', dest='init_eq', type='int', default=-1,
        help='''Initialise all ibobs' equaliser channels to specified value.''')
    p.add_option('-p', '--eq_poly', dest='eq_poly', action='store_true', default=False,
        help='''Initialise all ibobs' equaliser channels to the equalization polynomials specified in the config file.''')
    p.add_option('-v', '--verbose', dest='verbose', action='store_true', default=False,
        help='''Be more verbose about what the script is doing.''')


    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

    verbose_level = {False: 0, True: 1}[opts.verbose]

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

    servers = c.servers
    n_chans = c.config['n_chans']
    auto_eq = c.config['auto_eq']
    n_ants_per_xaui=c.config['n_ants_per_xaui']
    n_xaui_ports_per_fpga=c.config['n_xaui_ports_per_fpga']

    if (opts.init_eq>=0):
        print '''Resetting all ibobs' %i channels' gains to %i...'''%(n_chans,opts.init_eq),
        sys.stdout.flush()
        c.ibob_eq_init(verbose_level=verbose_level,init_coeffs=[opts.init_eq])
        print 'Done.'

    elif (not auto_eq) or opts.eq_poly:
        print '''Configuring channels' gains to default values as listed in config file...''',
        sys.stdout.flush()
        c.ibob_eq_init(verbose_level=verbose_level)
        print 'Done.'

    else:
        print 'Auto-equalising...'
        print 'Not yet implemented!\n'
        #print '''Resetting all ibobs' %i channels' gains to %i...'''%(config['n_chans'],opts.auto_eq),
        # Calculate gain in IBOB to extrapolate back to 4b values
        #auto_gain = float(opts.acc_len * (opts.clk_per_sync / n_chan))
        #cross_gain = auto_gain / (2**(4+4*cross_shift))
        # Set a default equalization
        #equalization = numpy.polyval(opts.eq_poly, range(0,opts.n_chan))
        #apply_eq(range(0,opts.n_chan), equalization)

except KeyboardInterrupt:
    exit_clean()
except:
    exit_fail()

exit_clean()

