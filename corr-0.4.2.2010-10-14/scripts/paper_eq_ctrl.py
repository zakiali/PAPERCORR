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
            help='which channels to set. supports range of channels, 5_19 = channels 5 through 19. default is channel 0.')
    o.add_option('-e', '--coeff', dest='coeff', type='int', default=700<<7,
            help='equalization coefficient. default is 700<<7.')
    o.add_option('--zeroant', dest='zeroant', action='store_true',
            help='digital zero every antenna')
    o.add_option('--zerochans', dest='zerochans', action='store_true',
            help='zero out all the equalization channels on all roachs. Will take a few seconds')
    o.add_option('--keepinp', dest='keepint', action='store_true', 
            help='By default, all the inputs are not initialized to zero, before turning on the requested inputs from the command line inputs are updated! This option bypasses that and zeros out all antennas before selecting which inputs to turn on.')
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
        #initialize dictionary of equalization coefficients.
        ninputs = p.config['n_ants']
        eqchs = {}
        #4 dual pol ants per f engine (i.e. number of eq blocks)
        for input in range(ninputs/4):
            eqchs[input] = {}
            for linput in range(8):
                eqchs[input][linput] = n.zeros(1024,n.int32)

        #eqchs is a dictionary mapped to inputs that has { fpga : input on fpga: array value} etc..
        # note that locally on a roach input 0 and input 4 share the same eq coefficient bram. likewise with 
        #inputs (1,5),(2,6),(3,7).

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
        if opts.zeroant or opts.keepint:
            coeff = 0
            for fpga in p.fpgas:
                fpga.write_int('input_selector', 0x33333333)
            print 'Digital zero on all antennas. Exiting...'
            if not opts.keepint:
                exit()    
            else: 
                c_inputs = opts.inputs.split(',')
                c_inputs.sort()
                channels = get_chans(opts.chan)
                coeff = opts.coeff

        else:        
            c_inputs = opts.inputs.split(',')
            c_inputs.sort()
            channels = get_chans(opts.chan)
            print channels
            coeff = opts.coeff
        
        #Turn on the proper inputs. Note that the equalizer blocks give the same coeffincients to inputs
        #(0,4),(1,5),(2,6),(3,7). Hence there is no full flexibilty for turning on certain channels for 
        #certain inputs.
        dict = get_in(c_inputs)
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
                print 'writing coefficients for pf%d'%fpga,
                for i in range(8):
                    data = eqchs[fpga][i].byteswap().tostring()
                    if i > 3:
                        p.fpgas[fpga].write('eq_%d_coeffs'%(i%4),data,1024*4)
                    else:
                        p.fpgas[fpga].write('eq_%d_coeffs'%(i%4),data)

        for key in dict.keys():
            init_val = n.array(list(hex(p.fpgas[key].read_int('input_selector'))[::-1][:-2]))
            init_val[dict[key]] = '1' #noise source on has value = 1
            s = ''
            for v in init_val:
                s += v
            s = s[::-1]
            p.fpgas[key].write_int('input_selector', int(s,16))
            print 'writing into input select on FPGA %d, with hex value %s'%(key,s)

        print 'Channels that have nonzero eq coefficients'
        print channels



except(KeyboardInterrupt):
    exit()
