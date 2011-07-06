import unittest, struct, numpy as n
from casper_correlator.rx import CorrPacket, CollateBuffer
import casper_correlator.sim as sim

NANT = 8

class TestCollateBuffer(unittest.TestCase):
    def setUp(self):
        self.cb = CollateBuffer(nant=NANT,npol=1,nchan=2048,nwin=1)
    def test_xeng_bl_order(self):
        for i in range(32):
            h = CollateBuffer(nant=i,npol=1,nchan=1,nwin=1)
            self.assertEqual(h.xeng_bl_order(), sim.get_bl_order(i))
    def test_collate_packet(self):
        pkt = CorrPacket()
        # Make sure a correctly formatted packet is accepted
        self.cb.collate_packet(pkt)
        # Make sure bad packets are rejected
        pkt.instrument_id = 5 
        self.assertRaises(ValueError, self.cb.collate_packet, pkt)
    def test_get_buffer(self):
        dbuf,fbuf = self.cb.get_buffer()
        self.assertEqual(dbuf.shape, (147456,))
        self.assertEqual(dbuf.dtype, n.int32)
        self.assertEqual(fbuf.shape, (147456/2,))
        self.assertEqual(fbuf.dtype, n.int32)
        self.assertFalse(dbuf.flags.owndata)
        self.assertFalse(fbuf.flags.owndata)
    def test_set_unset_callback(self):
        def callback_func(i,j,pol,t,data,flags):
            print i,j,pol,t,data,flags
        self.cb.set_callback(callback_func)
        self.cb.unset_callback()
    def test_collating(self):
        xengs = [sim.XEngine(nant=NANT,npol=1,nchan=2048,engine_id=x) \
            for x in range(NANT)]
        xstreams = [x.get_pkt_stream() for x in xengs]
        timestamp = None
        while True:
            for x in xstreams:
                pkt = x.next()
                if timestamp is None: timestamp = pkt.timestamp
                if pkt.timestamp != timestamp: break
                self.cb.collate_packet(pkt)
            if pkt.timestamp != timestamp: break
        dbuf,fbuf = self.cb.get_buffer()
        self.assertEqual(len(n.where(dbuf == 0)), 1)
        dbuf = n.array([sim.decode_32bit(d) for d in dbuf])
        # nwin, nchan, npol, bls, r/i, fields
        dbuf.shape = (1, 2048, 1, len(self.cb.xeng_bl_order()), 2, 5)
        # Check real/imag
        self.assertTrue(n.all(dbuf[...,0,3] == 0))
        self.assertTrue(n.all(dbuf[...,1,3] == 1))
        # Check pol
        self.assertTrue(n.all(dbuf[...,0,:,2] == 0))
        # Check chan
        chans = n.arange(2048) ; chans.shape = (1,2048,1,1,1)
        self.assertTrue(n.all(dbuf[...,4] == chans))
        # Check bl
        blorder = n.array([(i,j) for j in range(NANT) for i in range(j+1)])
        iorder = blorder[:,0]; iorder.shape = (1,1,1,iorder.size,1)
        jorder = blorder[:,1]; jorder.shape = (1,1,1,jorder.size,1)
        self.assertTrue(n.all(dbuf[...,0] == iorder))
        self.assertTrue(n.all(dbuf[...,1] == jorder))
    def test_readout(self):
        cb = CollateBuffer(nant=NANT,npol=1,nchan=2048,nwin=1)
        xengs = [sim.XEngine(nant=NANT,npol=1,nchan=2048,engine_id=x) \
            for x in range(NANT)]
        xstreams = [x.get_pkt_stream() for x in xengs]
        timestamp = None
        def callback(i,j,pol,t,data,flags):
            self.assertEqual(data.shape, (2048,))
            self.assertEqual(flags.shape, (2048,))
            self.assertTrue(data.flags.owndata)
            self.assertTrue(flags.flags.owndata)
            data_r = n.array([sim.decode_32bit(d) \
                for d in data.real.astype(n.int32)])
            data_i = n.array([sim.decode_32bit(d) \
                for d in data.imag.astype(n.int32)])
            #print i,j,pol,t,flags.sum(),
            #print data_r[0,:], data_i[0,:]
            self.assertTrue(n.all(data_r[:,0] == i))
            # not enough dynamic range in float to resolve j
            #self.assertTrue(n.all(data_r[:,1] == j))
            self.assertTrue(n.all(data_r[:,2] == pol))
            self.assertTrue(n.all(data_r[:,3] == 0))
            self.assertTrue(n.all(data_r[:,4] == n.arange(2048)))
            self.assertTrue(n.all(data_i[:,0] == i))
            # not enough dynamic range in float to resolve j
            #self.assertTrue(n.all(data_i[:,1] == j))
            self.assertTrue(n.all(data_i[:,2] == pol))
            self.assertTrue(n.all(data_i[:,3] == 1))
            self.assertTrue(n.all(data_i[:,4] == n.arange(2048)))
        cb.set_callback(callback)
        while True:
            for x in xstreams:
                pkt = x.next()
                if timestamp is None: timestamp = pkt.timestamp
                if pkt.timestamp > timestamp + 2: break
                cb.collate_packet(pkt)
            if pkt.timestamp > timestamp + 2: break
        

if __name__ == '__main__':
    unittest.main()
