#! /usr/bin/env python

''' This script reads and writes from the input selector and eq coeff registers/brams on the ROACH F Engines.
xamples : 

paper_eq_ctrl.py ~/path/to/conf/file.conf  -i 0 -c 0 : turns on input 0 and channel 0. gives channel 0 eq coeff 700<<3 (default. -e controls that).

paper_eq_ctrl.py ~/path/to/conf.file.conf -i 3 -c 83 : turns on input 3/chan 83. This also turns off input0/ch0, but keeps the in0,ch0 eqcoeff on.

paper_eq_ctrl.py ~/path/to/conf.file.conf -i 3 -c 43 --update : turns on in 3 ch 43, in addition to keeping 83 on.If instead you left off the --updateit would have turned off ch 83.

paper_eq_ctrl.py ~/pthtoconf - i 0 -c 1 --update : turns on input zero chan 1 without turning off in 3, chan 43. Note that in 0, ch 0 was already on.
leave --update off to turn off ch0 from before. This will also turn off input3.

doing a --updateallchans, will only write coeffs for channels given on the input line. If --update given with --updateallchans, it will update the channels given on the command line and inputs, but will write zeros in the eq coeff for the other inputs. It will do almost the same thing. 

do a --zeroant, --zeroallchan for a hard reset. Set all values to zero.
'''
import corr, numpy as n 
import optparse, sys

from struct import unpack

def get_input(fpga,type='str'):
    '''Gets the values in the input selector register for fpga ( a katcp fpga client. 
        Type specifies the return type. supported type values: int, str (int string),hstr (hexstring with leading 0x),
        raw. Returns None type if type not recognized.'''
    try:   
        val = fpga.read_int('input_selector')
        rval = fpga.read('input_selector',4)
    except Exception, e : print e
    if type == 'int':
        return val
    elif type == 'str':
        return str(val)
    elif type == 'hstr':
        return hex(val)
    elif type == 'raw':
        return rval
    else: 
        return None

def get_eq(fpga, block='all', type='raw'):
    '''Gets all equalization values from the roach.
        By default it gets all values from all equalization blocks and returns a dictionary.
        Can give it an int(0-7) and will return a list of values/string depending on type.
        type values can be int, raw. int returns list of ints, raw returns ascii string.1024 = nchan'''
    try:
        d = None
        if block == 'all':
            d = {}
            #print 'getting_data'
            for i in range(4):
            #    print i
                if type=='raw':
                    d[i] = fpga.read('eq_%d_coeffs'%i,1024*4)
                    d[i+4] = fpga.read('eq_%d_coeffs'%i,1024*4,1024*4)
                elif type=='int':
                    d[i] = list(unpack('>1024I', fpga.read('eq_%d_coeffs'%i,1024*4)))
                    d[i+4] = list(unpack('>1024I', fpga.read('eq_%d_coeffs'%i,1024*4,1024*4)))
                else:
                    return None
                    break
        else: 
            block=int(block)
            if type=='raw':
                if block>3:
                    d = fpga.read('eq_%d_coeffs'%block, 1024*4,1024*4)
                else:
                    d = fpga.read('eq_%d_coeffs'%block, 1024*4)
            elif type=='int':
                if block>3:
                    d = list(unpack('>1024I', fpga.read('eq_%d_coeffs'%block,1024*4,1024*4)))
                else:    
                    d = list(unpack('>1024I', fpga.read('eq_%d_coeffs'%block,1024*4)))
            else:
                print 'Error'
                return None
    except Exception, e : print e                
    return d

def get_chans(cs):
    channels = []
    a = cs.split(',')
    b = []
    for st in a:
        b.append(st.split('_'))
    for l in b:     
        if len(l)==2:
            channels += range(int(l[0]),int(l[1])+1)
        else: channels.append(int(l[0]))    
    return channels
    
def get_in(inputs):
    '''Return tuples for inputs (fpga,local input).'''
    d = {}
    int_inputs = n.array(inputs,int)
    # 8 = number of inputs per f engine.
    divarr_inputs = divmod(int_inputs,8)
    tupinputs =  zip(divarr_inputs[0],divarr_inputs[1])
    for tup in tupinputs:
        if tup[0] in d.keys():
            d[tup[0]].append(tup[1])
        else:
            d[tup[0]] = [tup[1]]
    return d

######################################################################################################


try:

    o = optparse.OptionParser()
    o.add_option('-i', '--input', dest='inputs',type='string', default='0', 
            help='which input(s) to turn on. This is a list.default is 0')
    o.add_option('-c', '--chan', dest='chan', type='string', default='0',
            help='which channels to set. supports range of channels, 5_19 = channels 5 through 19(inclusive). default is channel 0.')
    o.add_option('-e', '--coeff', dest='coeff', type='int', default=700<<7,
            help='equalization coefficient. default is 700<<7.')
    o.add_option('-v', '--inval', dest='inval', type='string', default='1',
            help='What value to write into input selector for inputs given on the commandline. Default is 1=noise source. ')
    o.add_option('--zeroant', dest='zeroant', action='store_true',
            help='digital zero every antenna')
    o.add_option('--zerochans', dest='zerochans', action='store_true',
            help='zero out all the equalization channels on all roachs. Will take a few seconds')
    o.add_option('--update', dest='update', action='store_true',
            help='update channels and inputs. This does not set values to zero then write in command line values')
    o.add_option('--updateallchans', dest='updateallchans', action='store_true', 
            help='By default the only eq coefficients for inputs that are given on the command line are updated. This means that it updates all the channels for an eq block ( input).  This option bypasses that and updates all eq coefficients. This is helpfull when you dont know what channels are up and want the command line map tp stick.')
    o.add_option('--report', dest='report', action='store_true',
            help='report values')
    opts,args = o.parse_args(sys.argv[1:])

    if args==[]:
        print 'Please specify a configurateion file! \n Exiting.'
        exit()

    lh = corr.log_handlers.DebugLogHandler() 
    p = corr.corr_functions.Correlator(args[0], lh)
    for s, server in enumerate(p.config['servers']): p.loggers[s].setLevel(10)

    
    ##############################  REPORT VALUES  ##################################################################
    if opts.report:
        print 'Reporting Values...'
        print ' 3 = digital zero   2 = digital noise source2   1 = digital noise source1   0 = adc '
        print 'Getting Input Selector Values...[local inputs :  7 .... 0]'
        oninputs = []
        for i, fpga in enumerate(p.fpgas):
            inputvalues = get_input(fpga,type='hstr')
            print '     PF%2d : %s '%(i,inputvalues)
            if ('1' in inputvalues) or ('2' in inputvalues):
                if not ((i,fpga) in oninputs):
                    oninputs.append((i,fpga))
        print 'Channels with non-zero values....'
        print '\n'
        print 'Input #           Channel             Value'
        print '=======          =========           ======='
        for i, fpga in oninputs:
            chanson =  get_eq(fpga,type='int')
            for li in range(8):
                date = n.array(chanson[li])
                datewhere = n.where(date!=0)[0]
                if len(datewhere)>0:
                    for ch in datewhere:
                        print '%4d %17d %21d   '%(i*8 + li, ch, date[ch])
            
                     
    ##############################  SET VALUES  ##################################################################

    else:    
              #eqchs is a dictionary mapped to inputs that has { fpga : input on fpga: array value} etc..
        # note that locally on a roach input 0 and input 4 share the same eq coefficient bram. likewise with 
        #inputs (1,5),(2,6),(3,7).

        ninputs = p.config['n_ants']

        if opts.zerochans:
            print 'zeroing out all of the equalization coefficients'
            data = n.zeros(1024*2, n.int32) #each bram is 2048 address spaces. 2inputs at 1024channels each.
            data = data.byteswap().tostring()
            for fpga in range(ninputs/4):
                for i in range(4):
                    p.fpgas[fpga].write('eq_%d_coeffs'%i,data)
                print 'writing coefficients for pf%d'%fpga
            print 'exiting...    '
            exit()    
        if opts.zeroant: 
            coeff = 0
            for fpga in p.fpgas:
                fpga.write_int('input_selector', 0x33333333)
            print 'Digital zero on all antennas. Exiting...'
            exit()    

        else:        
            c_inputs = opts.inputs.split(',')
            c_inputs.sort()
            channels = get_chans(opts.chan)
            print channels
            coeff = opts.coeff
        
        dict = get_in(c_inputs)

        #initialize dictionary of equalization coefficients.
        eqchs = {}

        for input in range(ninputs/4):
            eqchs[input] = {}
            for linput in range(8):
                eqchs[input][linput] = n.zeros(1024,n.int32)

        if opts.update:
            for fpga,inputs in dict.iteritems():
                for inn in inputs:
                    if inn > 3:
                        eqchs[fpga][inn] = n.array(unpack('>1024I',p.fpgas[fpga].read('eq_%i_coeffs'%(inn%4),1024*4,1024*4)),dtype=n.int32)
                    else:
                        eqchs[fpga][inn] = n.array(unpack('>1024I',p.fpgas[fpga].read('eq_%i_coeffs'%(inn%4),1024*4)),dtype=n.int32)

        #Turn on the proper inputs. Note that the equalizer blocks give the same coeffincients to inputs
        #(0,4),(1,5),(2,6),(3,7). Hence there is no full flexibilty for turning on certain channels for 
        #certain inputs.
        for fpga, inputs in dict.iteritems():
            for inn in inputs:
                eqchs[fpga][inn][channels] = coeff
                if not opts.updateallchans:
                    print  'setting coefficients for fpga: %d, eqblock: %d'%(fpga,inn%4)
                    print  ' writing coefficients for fpga: %d'%fpga
                    if inn>3:
                        p.fpgas[fpga].write('eq_%d_coeffs'%(inn%4),eqchs[fpga][inn].byteswap().tostring(),1024*4)
                    else:    
                        p.fpgas[fpga].write('eq_%d_coeffs'%(inn%4),eqchs[fpga][inn].byteswap().tostring())
        if opts.updateallchans:
            for fpga in range(ninputs/4):
                #8 = number of inputs per f engine
                print 'writing coefficients for pf%d'%fpga
                for i in range(8):
                    data = eqchs[fpga][i].byteswap().tostring()
                    if i > 3:
                        p.fpgas[fpga].write('eq_%d_coeffs'%(i%4),data,1024*4)
                    else:
                        p.fpgas[fpga].write('eq_%d_coeffs'%(i%4),data)

        for f, fpga in enumerate(p.fpgas):
            if opts.update:
                init_val = n.array(list(hex(fpga.read_int('input_selector'))[::-1][:-2]))
            else:     
                init_val = n.array(list('0x33333333')[::-1][:-2])
            if f in dict.keys():
                init_val[dict[f]] = opts.inval
            s = ''
            for v in init_val:
                s += v
            s = s[::-1]
            fpga.write_int('input_selector', int(s,16))
            print 'writing into input select on FPGA %d, with hex value %s'%(f,s)

        print 'Channels that have nonzero eq coefficients'
        print channels

except(KeyboardInterrupt):
    exit()
