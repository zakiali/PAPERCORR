import unittest, numpy as n
from casper_correlator.rx import BufferSocket, CollateBuffer
import casper_correlator.sim as sim
import socket, time, struct

def loopback(data, port=8888):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 200000)
    sock.connect(('localhost', port))
    sock.send(data)
    sock.close()

PORT = 8888
NANT = 8
packet_in_callback = None
data_in_readout = False

class TestBufferSocket(unittest.TestCase):
    def setUp(self):
        self.bs = BufferSocket()
    def dtest_start_stop(self):
        for i in range(10):
            self.bs.start(PORT)
            self.bs.stop()
    def dtest_init(self):
        bs = BufferSocket(item_count=10)
        bs = BufferSocket(payload_len=1024)
        bs = BufferSocket(item_count=100, payload_len=9000)
    def dtest_set_unset_callback(self):
        def callback(s): pass
        self.bs.set_callback(callback)
        self.bs.unset_callback()
        cb = CollateBuffer(nant=8,npol=1,nchan=2048,nwin=1)
        self.bs.set_callback(cb)
        self.bs.unset_callback()
        self.assertRaises(TypeError, self.bs.set_callback, (None,))
    def dtest_auto_shutdown(self):
        bs = BufferSocket()
        def callback(s): pass
        bs.set_callback(callback)
        bs.start(PORT)
        for i in range(10):
            loopback('Test' * 10)
            time.sleep(.0001)
        del(bs)
        loopback('Test' * 10)
    def dtest_get_packets_in_callback(self):
        def callback(s):
            global packet_in_callback
            packet_in_callback = s
        self.bs.set_callback(callback)
        self.bs.start(PORT)
        for i in range(100):
            loopback('Test' * 10)
            time.sleep(.0001)
        self.bs.stop()
        self.bs.unset_callback()
        self.assertEqual(packet_in_callback, 'Test' * 10)
    def test_cb_callback(self):
        cb1 = CollateBuffer(nant=NANT,npol=1,nchan=2048,nwin=1)
        cb2 = CollateBuffer(nant=NANT,npol=1,nchan=2048,nwin=1, sdisp=1, sdisp_destination_ip="192.168.1.196")
        def callback(i,j,pol,t,data, flags):
            global data_in_readout
            data_in_readout = True
        cb1.set_callback(callback)
        bs = BufferSocket()
        bs.set_callback(cb1)
        bs.start(PORT)
        xengs = [sim.XEngine(nant=NANT,npol=1,nchan=2048,engine_id=x, intlen=1562500) \
            for x in range(NANT)]
        xstreams = [x.get_pkt_stream() for x in xengs]
        timestamp = None
        cnt = 0
        while True:
            for x in xstreams:
                pkt = x.next()
                pkt.currerr = cnt
                cnt += 1
                if timestamp is None: timestamp = pkt.timestamp
                if pkt.timestamp > timestamp + 2: break
                loopback(pkt.pack(), port=PORT)
                cb2.collate_packet(pkt)
            time.sleep(.0001)
            if pkt.timestamp > timestamp + 2: break
        bs.stop()
        self.assertTrue(data_in_readout)
    def dtest_all_data(self):
        cb = CollateBuffer(nant=NANT,npol=1,nchan=2048,nwin=1)
        def callback(i,j,pol,t,data,flags):
            self.assertTrue(n.all(flags == 0))
        cb.set_callback(callback)
        bs = BufferSocket()
        bs.set_callback(cb)
        bs.start(PORT)
        xengs = [sim.XEngine(nant=NANT,npol=1,nchan=2048,engine_id=x) \
            for x in range(NANT)]
        xstreams = [x.get_pkt_stream() for x in xengs]
        timestamp = None
        while True:
            for x in xstreams:
                pkt = x.next()
                if timestamp is None: timestamp = pkt.timestamp
                if pkt.timestamp > timestamp + 2: break
                loopback(pkt.pack(), port=PORT)
            time.sleep(.0001)
            if pkt.timestamp > timestamp + 2: break
        bs.stop()


    


if __name__ == '__main__':
    unittest.main()
