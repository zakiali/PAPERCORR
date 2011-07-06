import casper_correlator.sim as sim
import unittest

class TestXEngine(unittest.TestCase):
    def setUp(self):
        self.nant = 8
        self.nchan = 2048
        self.npol = 4
        self.xeng = sim.XEngine(nant=self.nant,nchan=self.nchan,npol=self.npol)
    def test_init(self):
        nbls = len(sim.get_bl_order(self.nant))
        self.assertEqual(len(self.xeng.data), \
            4*2*self.npol*self.nchan*nbls / self.nant)
    def test_init_pkt(self):
        pkt = self.xeng.init_pkt()
        self.assertEqual(pkt.engine_id, 0)
        self.assertEqual(pkt.instance_id, 0)
        self.assertEqual(pkt.instrument_id, 3)
        self.assertEqual(pkt.currerr, 0)
    def test_get_pkt(self):
        pktgen = self.xeng.get_pkt_stream()
        pkt = pktgen.next()
        self.assertEqual(pkt.timestamp, 0)
        self.assertEqual(pkt.heap_off, 0)
        self.assertEqual(pkt.packet_len, self.xeng.pktlen)
        t = pkt.timestamp
        pkts = []
        while pkt.timestamp == t:
            pkts.append(pkt)
            pkt = pktgen.next()
        pktlen = len(self.xeng.data) % self.xeng.pktlen
        if pktlen == 0: pktlen = self.xeng.pktlen
        self.assertEqual(pkts[-1].packet_len, pktlen)
        self.assertEqual(pkts[-1].heap_off+pkts[-1].packet_len,len(self.xeng.data))
        data = ''.join([pkt.get_data() for pkt in pkts])
        self.assertEqual(data, self.xeng.data)

if __name__ == '__main__':
    unittest.main()
