import unittest, struct, bitstring
from casper_correlator.rx import CorrPacket

HEADER_SIZE = 56
PKT_ID = 19282
OPTS = {
    'n_options':6, 
    'instrument_id':3,
    'instance_id':0,
    'engine_id':59,
    'timestamp':64, 
    'heap_off':128,
    'packet_len':8,
    'packet_count':1,
    'currerr':0, 
    'data':(55,22),
}

# a valid packet (for the purposes of the casper correlator) is as follows:
# 
# [PKT_ID (16b) | VER (16b)      | 0 (16b)       | # OPTS (16b)      ]
# [50 (16b)     | INSTR ID (16b) | INST ID (16b) | XENG ID (16b)     ]
# [3  (16b)     | ADC Timestamp (48b)			 	     ]
# [4  (16b)     | Heap Length (48b)				     ]
# [51  (16b)    | Packet Length (32b)            | Packet count (16b)]
# [5  (16b)     | Heap offset (48b) 				     ]
# [0 (16b)      | Reserved (will be used for heap pointer) (48b)     ]
# <heap>
#
#

PACKET = struct.pack('>HHHH', PKT_ID, 3, 0, OPTS['n_options']) + \
    struct.pack('>HHHH', 50, OPTS['instrument_id'], OPTS['instance_id'], OPTS['engine_id']) + \
    struct.pack('>HHI', 3, 0, OPTS['timestamp']) + \
    struct.pack('>HHI', 52, 0, OPTS['currerr']) + \
    struct.pack('>H', 51) + bitstring.BitString(uintbe=OPTS['packet_len'], length=24).bytes + \
    bitstring.BitString(uintbe=OPTS['packet_count'], length=24).bytes + \
    struct.pack('>HHI', 5, 0, OPTS['heap_off']) + \
    struct.pack('>HHI', 53, 0, 0) + \
    struct.pack('>II',  *OPTS['data'])

BAD_PACKET1 = struct.pack('>HHHH', 1111, 3, 0, OPTS['n_options']) + \
    struct.pack('>HHHH', 50, OPTS['instrument_id'], OPTS['instance_id'], OPTS['engine_id']) + \
    struct.pack('>HHI', 3, 0, OPTS['timestamp']) + \
    struct.pack('>HHI', 52, 0, OPTS['currerr']) + \
    struct.pack('>H', 51) + bitstring.BitString(uintbe=OPTS['packet_len'], length=24).bytes + \
    bitstring.BitString(uintbe=OPTS['packet_count'], length=24).bytes + \
    struct.pack('>HHI', 5, 0, OPTS['heap_off']) + \
    struct.pack('>HHI', 53, 0, 0) + \
    struct.pack('>II',  *OPTS['data'])

BAD_PACKET2 = struct.pack('>HHHH', PKT_ID, 3, 0, OPTS['n_options'] + 1) + \
    struct.pack('>HHHH', 50, OPTS['instrument_id'], OPTS['instance_id'], OPTS['engine_id']) + \
    struct.pack('>HHI', 3, 0, OPTS['timestamp']) + \
    struct.pack('>HHI', 52, 0, OPTS['currerr']) + \
    struct.pack('>H', 51) + bitstring.BitString(uintbe=OPTS['packet_len'], length=24).bytes + \
    bitstring.BitString(uintbe=OPTS['packet_count'], length=24).bytes + \
    struct.pack('>HHI', 5, 0, OPTS['heap_off']) + \
    struct.pack('>HHI', 53, 0, 0) + \
    struct.pack('>II',  *OPTS['data'])

class TestCorrPacket(unittest.TestCase):
    def setUp(self):
        self.cp = CorrPacket()
        self.cp.unpack_header(PACKET)
	    #self.heap_len = len(PACKET[self.cp.header_size():])

    def test_header_size(self):
        self.assertEqual(self.cp.header_size(), HEADER_SIZE)
    def test_size(self):
        cp = CorrPacket()
        self.assertEqual(cp.size(), HEADER_SIZE)
    def test_getattributes(self):
        self.assertEqual(self.cp.n_options, OPTS['n_options'])
        self.assertEqual(self.cp.instrument_id, OPTS['instrument_id'])
        self.assertEqual(self.cp.instance_id, OPTS['instance_id'])
        self.assertEqual(self.cp.engine_id, OPTS['engine_id'])
        self.assertEqual(self.cp.timestamp, OPTS['timestamp'])
        self.assertEqual(self.cp.currerr, OPTS['currerr'])
    def test_setattributes(self):
        cp = CorrPacket()
        cp.n_options     = 7; self.assertEqual(cp.n_options,     7)
        cp.instrument_id = 7; self.assertEqual(cp.instrument_id, 7)
        cp.instance_id   = 7; self.assertEqual(cp.instance_id,   7)
        cp.engine_id     = 7; self.assertEqual(cp.engine_id,     7)
        cp.timestamp     = 7; self.assertEqual(cp.timestamp,     7)
        cp.heap_off       = 7; self.assertEqual(cp.heap_off,       7)
        cp.currerr       = 7; self.assertEqual(cp.currerr,       7)
        cp.set_data('abcdefgh'); self.assertEqual(cp.get_data(), 'abcdefgh')
    def test_unpack_header(self):
        cp = CorrPacket()
        cp.unpack_header(PACKET)
        for k in OPTS:
            if not k in ['data']: self.assertEqual(getattr(cp,k), OPTS[k])
    def test_unpack_data(self):
        cp = CorrPacket()
        cp.unpack_header(PACKET)
        cp.unpack_data(PACKET[cp.header_size():])
	print "Packet data is ",len(cp.get_data()),"bytes long"
        data = struct.unpack('II', cp.get_data()) # use native endianess
        self.assertEqual(data, OPTS['data'])
    def test_unpack(self):
        cp = CorrPacket()
        cp.unpack(PACKET)
        for k in OPTS:
            if not k in ['data']: self.assertEqual(getattr(cp,k), OPTS[k])
        self.assertRaises(ValueError, cp.unpack, BAD_PACKET1)
        #self.assertRaises(ValueError, cp.unpack, BAD_PACKET2, self.heap_len)
    def test_pack_header(self):
        cp = CorrPacket()
        cp.unpack(PACKET)
        data = cp.pack_header()
        self.assertEqual(data, PACKET[:cp.header_size()])
    def test_pack_data(self):
        cp = CorrPacket()
        cp.unpack(PACKET)
        data = cp.pack_data()
        self.assertEqual(data, PACKET[cp.header_size():])
    def test_pack(self):
        cp = CorrPacket()
        cp.unpack(PACKET)
        data = cp.pack()
        print "Packlen:",len(data),"Origlen:",len(PACKET)
        self.assertEqual(data, PACKET)

if __name__ == '__main__':
    unittest.main()
