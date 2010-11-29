from rx import CorrPacket
import struct

def ij2bl(i, j): return ((i+1) << 8) | (j+1)
def bl2ij(bl): return ((bl >> 8) & 255) - 1, (bl & 255) - 1

def get_bl_order(n_ants):
    """Return the order of baseline data output by a CASPER correlator
    X engine."""
    order1, order2 = [], []
    for i in range(n_ants):
        for j in range(int(n_ants/2),-1,-1):
            k = (i-j) % n_ants
            if i >= k: order1.append((k, i))
            else: order2.append((i, k))
    order2 = [o for o in order2 if o not in order1]
    return tuple([o for o in order1 + order2])

def encode_32bit(i, j, stokes, r_i, chan):
    """Encode baseline, stokes, real/imaginary, and frequency info as 
    a 32 bit unsigned integer."""
    return (r_i << 31) | (stokes << 29) | (chan << 16) | ij2bl(i,j)

def decode_32bit(data):
    """Decode baseline, stokes, real/imaginary, and frequency info from
    a 32 bit number."""
    i,j = bl2ij(data & (2**16-1))
    freq = (data >> 16) & (2**13-1)
    stokes = (data >> 29) & 3
    r_i = (data >> 31) & 1
    return i, j , stokes, r_i, freq

class XEngine:
    def __init__(self, nant=8, nchan=2048, npol=4, id=0, pktlen=2048,
            engine_id=0, instance_id=0, instrument_id=3, start_t=0, intlen=1):
        self.pktlen = pktlen
        self.engine_id = engine_id
        self.instance_id = instance_id
        self.instrument_id = instrument_id
        self.t = start_t
        self.intlen = intlen
        self.data = []
        data = [encode_32bit(i,j,p, r_i, ch) \
            for ch in range(engine_id,nchan,nant) \
            for (i,j) in get_bl_order(nant) \
            for p in range(npol) \
            for r_i in [0,1] \
        ]
        self.data = struct.pack('%dI' % len(data), *data)
    def init_pkt(self):
        pkt = CorrPacket()
	pkt.packet_len = self.pktlen
	pkt.packet_count = 1
        pkt.engine_id = self.engine_id
        pkt.instance_id = self.instance_id
        pkt.instrument_id = self.instrument_id
        pkt.currerr = 0
        return pkt
    def get_pkt_stream(self):
        c, L = 0, self.pktlen
        while True:
            pkt = self.init_pkt()
            pkt.heap_off = c * L
            noff = (c+1) * L
            pkt.timestamp = self.t
            d = self.data[pkt.heap_off:noff]
            pkt.set_data(d)
	    pkt.packet_count = c
            yield pkt
            if noff >= len(self.data):
                c = 0
                self.t += self.intlen
            else: c += 1

#class CorrSimulator:
#    def __init__(self, xengines=None, nant=8, nchan=2048, npol=4):
#        if xengines is None: xengines = range(nant)
#        self.xeng = xengines
#        self.bls = get_bl_order(nant)
#        self.nchan = nchan
#        self.npol = npol
#        data = n.zeros((len(self.bls), nchan/nant, npol, 2), dtype=n.uint32)
#        for c,(i,j) in enumerate(self.bls): data[c,...] = ij2bl(i,j)
#        ch = n.arange(0, nchan, nant, dtype=n.uint32)
#        ch = n.left_shift(ch, 16)
#        ch.shape = (1,nchan/nant,1,1)
#        for c,pol in enumerate(range(npol)):
#            data[:,:,c,...] = n.bitwise_or(data[:,:,c,...], (pol << 29))
#        data[...,1] = n.bitwise_or(data[...,1], (1 << 31))
#        self.data = data
#    def get_pkt(self):
#        """Generate data for a casper_n correlator.  Each data
#        sample is encoded with the baseline, stokes, real/imag, frequency
#        that it represents."""
#        #while True:
#        #    data = self.data.copy()
#        #    for c in range(self.nchan/nant
#        data = []
#        # Loop through channels in X engine (spaced every n_ants channels)
#        for coarse_chan in range(n_chans/n_ants):
#            c = coarse_chan * n_ants + x_num
#            # Loop through baseline order out of X engine
#            for bl in bls:
#                # Loop through stokes parameters
#                for s in range(n_stokes):
#                    # Real and imaginary components
#                    for ri in (0, 1):
#                        data.append(encode_32bit(bl, s, ri, c))
#        fmt = '%s%dI' % (endian, len(data))
#        return struct.pack(fmt, *data)
#
#        
#
##class PacketSimulator:
##   def __init__(self, nant, nchan, npol):
