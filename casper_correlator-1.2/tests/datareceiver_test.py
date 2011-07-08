import unittest, numpy as n, aipy as a
import casper_correlator.sim as sim, casper_correlator.dacq as dacq
import socket, time, struct, ephem, os

def loopback(data, port=8888):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 200000)
    sock.connect(('localhost', port))
    sock.send(data)
    sock.close()

PORT = 8888

class TestBufferSocket(unittest.TestCase):
    def setUp(self):
        bm = a.phs.Beam(n.array([.15]))
        ants = [a.phs.Antenna(   0,   0,   0, bm),
                a.phs.Antenna( 210,-140,-260, bm),
                a.phs.Antenna( 200,-810,-250, bm),
                a.phs.Antenna(-250,-670, 310, bm),
                a.phs.Antenna(-280,-460, 350, bm),
                a.phs.Antenna(-280,-360, 340, bm),
                a.phs.Antenna(-170,-100, 220, bm),
                a.phs.Antenna( -70, -20, 100, bm),]
        self.aa = a.phs.AntennaArray(('38','-80'), ants)
        self.bs = dacq.DataReceiver(self.aa, pols=['xx'],
            nchan=2048, sfreq=0.121142578125, sdf=7.32421875e-05,
            inttime=14.3165578842, t_per_file=ephem.second*10, sdisp=1, sdisp_destination_ip="192.168.1.196")
    def dump_packet(self, pkt):
        print "Len:",pkt.packet_len,"Off:",pkt.heap_off
        print "XID:",pkt.engine_id
        #print "Data:",pkt.data
    def test_all_data(self):
        self.bs.start(PORT)
        xengs = [sim.XEngine(nant=len(self.aa),npol=1,nchan=2048,engine_id=x,intlen=1562500) \
            for x in range(len(self.aa))]
        xstreams = [x.get_pkt_stream() for x in xengs]
        timestamp = None
        while True:
            for x in xstreams:
                pkt = x.next()
                if timestamp is None: timestamp = pkt.timestamp
                if pkt.timestamp > timestamp + 20: break
                loopback(pkt.pack(), port=PORT)
            time.sleep(.0001)
            if pkt.timestamp > timestamp + 20: break
        self.bs.stop()
        self.assertTrue(os.path.exists('zen.2450000.00000.uv'))
        self.assertTrue(os.path.exists('zen.2450000.00013.uv'))

if __name__ == '__main__':
    unittest.main()
