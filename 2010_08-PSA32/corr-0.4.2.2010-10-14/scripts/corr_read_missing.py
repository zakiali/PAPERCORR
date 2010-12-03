#! /usr/bin/env python
"""
Reads the error counters on the correlator and reports accumulated XAUI and
packet errors.
\n\n
Revisions:
2009-12-01  JRM Layout changes, check for loopback sync
2009/11/30  JRM Added support for gbe_rx_err_cnt for rev322e onwards.
2009/07/16  JRM Updated for x engine rev 322 with KATCP.
"""
import corr, time, sys,struct,logging

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
    p.set_usage('read_missing.py [options] CONFIG_FILE')
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
    n_xeng_per_fpga = c.config['x_per_fpga']
    n_xaui_ports_per_fpga=c.config['n_xaui_ports_per_fpga']
    xeng_acc_len=c.config['xeng_acc_len']
    start_t = time.time()
    #clear the screen:
    print '%c[2J'%chr(27)

    while True:

        loopback_ok=c.check_loopback_mcnt() 
        xaui_errors=[c.read_uint_all('xaui_err%i'%(x)) for x in range(n_xaui_ports_per_fpga)]
        xaui_rx_cnt=[c.read_uint_all('xaui_cnt%i'%(x)) for x in range(n_xaui_ports_per_fpga)]
        gbe_tx_cnt =[c.read_uint_all('gbe_tx_cnt%i'%(x)) for x in range(n_xaui_ports_per_fpga)]
        gbe_tx_err =[c.read_uint_all('gbe_tx_err_cnt%i'%(x)) for x in range(n_xaui_ports_per_fpga)]

    
        rx_cnt     = [c.read_uint_all('rx_cnt%i'%(x)) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        gbe_rx_cnt = [c.read_uint_all('gbe_rx_cnt%i'%x) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        gbe_rx_err_cnt = [c.read_uint_all('gbe_rx_err_cnt%i'%x) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        rx_err_cnt = [c.read_uint_all('rx_err_cnt%i'%x) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        loop_cnt   = [c.read_uint_all('loop_cnt%i'%x) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        loop_err_cnt = [c.read_uint_all('loop_err_cnt%i'%x) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        mcnts      = [c.read_uint_all('loopback_mux%i_mcnt'%(x)) for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga))]
        x_cnt      = [c.read_uint_all('pkt_reord_cnt%i'%(x)) for x in range(n_xeng_per_fpga)]
        x_miss     = [c.read_uint_all('pkt_reord_err%i'%(x)) for x in range(n_xeng_per_fpga)]
        last_miss_ant = [c.read_uint_all('last_missing_ant%i'%(x)) for x in range(n_xeng_per_fpga)]
        
        vacc_cnt   = [c.read_uint_all('vacc_cnt%i'%x) for x in range(n_xeng_per_fpga)]
        vacc_err_cnt = [c.read_uint_all('vacc_err_cnt%i'%x) for x in range(n_xeng_per_fpga)]

        loopmcnt=[]
        gbemcnt=[]
        for mi,mv in enumerate(mcnts):
            loopmcnt.append([mv[x]/(2**16) for x,f in enumerate(c.fpgas)])
            gbemcnt.append([mv[x]&((2**16)-1) for x,f in enumerate(c.fpgas)])

        sum_bad_pkts = sum([sum(x_miss_n) for x_miss_n in x_miss])/xeng_acc_len
        sum_xaui_errs = sum([sum(xaui_error_n) for xaui_error_n in xaui_errors])
        sum_spectra = sum([sum(engcnt) for engcnt in x_cnt])

        # move cursor home
        print '%c[2J'%chr(27)
        for fn,fpga in enumerate(c.fpgas):
            print '  ', servers[fn]

            for x in range(n_xaui_ports_per_fpga):
                print '\tXAUI%i         RX cnt: %10i    Errors: %10i'%(x,xaui_rx_cnt[x][fn],xaui_errors[x][fn])
                print '\t10GbE%i        TX cnt: %10i    Errors: %10i'%(x,gbe_tx_cnt[x][fn],gbe_tx_err[x][fn]) 

            for x in range(min(n_xaui_ports_per_fpga,n_xeng_per_fpga)):
                print "\t10GbE%i        RX cnt: %10i    Errors: %10i"%(x,gbe_rx_cnt[x][fn],gbe_rx_err_cnt[x][fn])
                print '\tLoopback%i        cnt: %10i    Ovrflw: %10i'%(x,loop_cnt[x][fn],loop_err_cnt[x][fn])
                print "\tLoopback_mux%i    cnt: %10i    Errors: %10i"%(x,rx_cnt[x][fn],rx_err_cnt[x][fn])
                print '\t  Loopback%i     mcnt: %6i'%(x,loopmcnt[x][fn])
                print '\t  GBE%i          mcnt: %6i'%(x,gbemcnt[x][fn]) 
                
            for x in range(n_xeng_per_fpga):
                print '\tX engine%i Spectr cnt: %10i    Errors: %10.2f'%(x,x_cnt[x][fn],float(x_miss[x][fn])/float(xeng_acc_len)),
                if x_miss[x][fn]>0: print 'Last missing antenna: %i'%last_miss_ant[x][fn]
                else: print '' 
                print "\tVector Accum%i    cnt: %10i    Errors: %10i"%(x,vacc_cnt[x][fn],vacc_err_cnt[x][fn])
            print ''

        print 'Total number of spectra processed: %i'%sum_spectra
        print 'Total bad X engine data: %i packets'%sum_bad_pkts
        print 'Total bad XAUI packets received: %i'%sum_xaui_errs
        print 'Loopback muxes all syncd: ',loopback_ok
        print 'Time:', time.time() - start_t
        time.sleep(2)

except KeyboardInterrupt:
        exit_clean()
except: 
        exit_fail()

exit_clean()

