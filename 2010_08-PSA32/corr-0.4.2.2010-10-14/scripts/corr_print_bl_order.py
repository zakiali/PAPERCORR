#! /usr/bin/env python

import corr.sim_cn_data,os,sys

if __name__ == '__main__':
    from optparse import OptionParser

    p = OptionParser()
    p.set_usage('print_bl_order.py CONFIG_FILE')
    p.set_description(__doc__)
    opts, args = p.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configuration file! \nExiting.'
        exit()

    config = corr.cn_conf.CorrConf(args[0])
    config_status = config.read_all()
    print '\n\nParsing config file %s...'%(args[0])
    sys.stdout.flush()
n_bls=config['n_ants']*(config['n_ants']+1)/2
print 'Baseline ordering for %i antenna system:'%config['n_ants']

for i in range(n_bls):
    print 't%i:'%i,corr.sim_cn_data.bl2ij(corr.sim_cn_data.get_bl_order(config['n_ants'])[i])

print "done"
