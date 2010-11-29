import unittest, struct
from casper_correlator.rx import CorrPacket
import bitstring

HEADER_SIZE = 56
PKT_ID = 19282
OPTS = {
    'n_options':6, 
    'msb_first':1,
    'bits_per_val':32, 
    'instrument_id':3,
    'instance_id':0,
    'engine_id':59,
    'timestamp':64, 
    'heapoff':128,
    'packetlen':8,
    'packetcount':1,
    'currerr':0, 
    'heaplen':8, 
    'data':(55,22),
}

PACKET = struct.pack('>HHHH', PKT_ID, 3, 0, OPTS['n_options']) + \
    struct.pack('>HHHH', 50, OPTS['instrument_id'], OPTS['instance_id'], OPTS['engine_id']) + \
    struct.pack('>HHI', 3, 0, OPTS['timestamp']) + \
    struct.pack('>HHI', 52, 0, OPTS['currerr']) + \
    struct.pack('>H', 51) + bitstring.BitString(uintbe=OPTS['packetlen'], length=24).bytes + \
    bitstring.BitString(uintbe=OPTS['packetlen'], length=24).bytes + \
    struct.pack('>HHI', 5, 0, OPTS['heapoff']) + \
    struct.pack('>HHI', 53, 0, 0) + \
    struct.pack('>II',  *OPTS['data'])

cp = CorrPacket()
cp.unpack_header(PACKET)
cp.unpack_data(PACKET[cp.header_size():], len(PACKET[cp.header_size():]))
print "header:",cp.header_size()
print "data:",len(cp.get_data())
print "data size:",cp.size()
print "instance_id",cp.instance_id
print "instrument_id",cp.instrument_id
print "engine_id",cp.engine_id
print struct.unpack('>II', cp.get_data())
