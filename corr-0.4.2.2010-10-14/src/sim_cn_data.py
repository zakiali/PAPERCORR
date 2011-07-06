"""A module for generating simulation data for a casper_n correlator.  This
is used to verify the data-flow through the packetization and readout system.

Author: Aaron Parsons
Modified: Jason Manley
Date: 2007/10/29
Revisions:
2008-02-08  JRM Neatening, removing redundant interfaces

2007-10-29  JRM added addr_decode and addr_encode functions

"""

import struct, time, math

def xeng_encode(freq,n_xeng=8, n_chans=2048,adc_clk=600,ddc_decimation=4,ddc_mix_freq=0.25):
    bandwidth = adc_clk/ddc_decimation
    center_freq = adc_clk*ddc_mix_freq
    start_freq = center_freq - bandwidth/2
    im = freq - start_freq
    chan = int((float(im)/bandwidth * n_chans))
    out = dict()
    if (chan >= (n_chans/2)):
        chan = chan - (n_chans/2)
    else:
        chan = chan + (n_chans/2)
    out['chan'] = chan
    out['x_eng'] = int(chan % n_xeng)
    out['group'] = int(chan/n_xeng)
    return out

def xeng_decode(x_eng,chan,n_xeng=8, n_chans=2048,adc_clk=600,ddc_decimation=4,ddc_mix_freq=0.25):    
    bandwidth = float(adc_clk)/ddc_decimation
    chan_bw = bandwidth/n_chans
    print chan_bw
    center_freq = float(adc_clk)*ddc_mix_freq
    start_freq = center_freq - bandwidth/2
    freq_offset = x_eng * chan_bw
    freq = (chan*n_xeng)*chan_bw
    freq = freq + freq_offset
    if freq >= bandwidth/2:
        freq += start_freq
    else:
        freq += center_freq
    return freq

def addr_decode(address,vector_len=18432):
    """Calculates which bank,row,rank,column and block a particular 
    address maps to. Good for BEE2 1GB DRAMs."""
    if vector_len > 512:
        bit_shift = int(math.ceil(math.log(float(vector_len)/512.0,2)))
    else:
        bit_shift = 1
    #print bit_shift
    #address = (2**20) + (2**29) +(2**13)
    out = dict()
    out['bank'] = (address & ((2**28) + (2**29)))>>28
    out['row'] =  (address & (  ((2**28)-1) - ((2**14)-1)  ))>>14
    out['rank'] = (address & (2**13))>>13
    out['col'] = (address & (  ((2**13)-1) - ((2**3)-1)  ))>>3
    out['block'] = out['bank'] + ((out['row']>>bit_shift) <<2) + (out['rank']<<10)
    #print bank,row,rank,col,block
    return out

def addr_encode(int_num=0,offset=0,vector_len=18432):
    """Calculates the address location in DRAM of an integration.
    int_num: the number of the integration you're looking for.
    offset:
    vector_len: Programmed length of the DRAM_VACC."""
    if vector_len > 512:
        bit_shift = int(math.ceil(math.log(float(vector_len)/512.0,2)))
    else:
        bit_shift = 1

    block_row_bits = 14-bit_shift

    bank = int_num & 3
    block_row = (int_num >> 2) & ((2**block_row_bits)-1) 
    rank = (int_num>>(block_row_bits + 2))

    column = offset & ((2**9)-1)
    row_offset = (offset >> 9)

    address = (column << 4) + (rank<<13) + (row_offset << 14) + (block_row<<(14 + bit_shift)) + (bank << 28)
    
    #print bank,bit_shift, block_row, block_row_bits, rank, column, row_offset
    return address


def ij2bl(i, j):
    """Convert i, j baseline notation (counting from 0) to Miriad's baseline
    notation (counting from 1, a 16 bit number)."""
    return ((i+1) << 8) | (j+1)

def bl2ij(bl):
    """Convert from Miriad's baseline notation (counting from 1, a 16 bit 
    number) to i, j baseline notation (counting from 0)."""
    return ((bl >> 8) & 255) - 1, (bl & 255) - 1

def encode_32bit(bl, stokes, r_i, chan):
    """Encode baseline, stokes, real/imaginary, and frequency info as 
    a 32 bit number."""
    return (r_i << 31) | (stokes << 29) | (chan << 16) | bl

def decode_32bit(data):
    """Decode baseline, stokes, real/imaginary, and frequency info from
    a 32 bit number."""
    bl = data & 16383
    freq = (data >> 16) & 8191
    stokes = (data >> 29) & 3
    r_i = (data >> 31) & 1
    return bl, stokes, r_i, freq

def get_bl_order(n_ants):
    """Return the order of baselines output by an x engine in the casper_n
    correlator.  Baselines are in Miriad notation."""
    order1, order2 = [], []
    for i in range(n_ants):
        for j in range(int(n_ants/2),-1,-1):
            k = (i-j) % n_ants
            if i >= k: order1.append((k, i))
            else: order2.append((i, k))
    order2 = [o for o in order2 if o not in order1]
    return [ij2bl(*o) for o in order1 + order2]

def sim_x_engine(x_num, n_ants, n_stokes, n_chans, endian='<'):
    """Generate data for an x engine in a casper_n correlator.  Each data
    sample is encoded with the baseline, stokes, real/imag, frequency
    that it represents."""
    data = []
    bls = get_bl_order(n_ants)
    # Loop through channels in X engine (spaced every n_ants channels)
    for coarse_chan in range(n_chans/n_ants):
        c = coarse_chan * n_ants + x_num
        # Loop through baseline order out of X engine
        for bl in bls:
            # Loop through stokes parameters
            for s in range(n_stokes):
                # Real and imaginary components
                for ri in (0, 1):
                    data.append(encode_32bit(bl, s, ri, c))
    fmt = '%s%dI' % (endian, len(data))
    return struct.pack(fmt, *data)

