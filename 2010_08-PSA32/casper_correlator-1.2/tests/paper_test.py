import unittest, numpy as n
import casper_correlator.sim as sim, casper_correlator.dacq as dacq
import socket, time, struct, ephem, os
import aipy

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
        self.n_chans=1024
        bandwidth = 0.1
        sdf = 7.32421875e-05 #bandwidth /n_chans in GHz
        sfreq = 0.121142578125
        int_time = 8 #integration time in seconds
        location=0,0,0
        t_per_file=ephem.hour
        n_windows_to_buffer=4
        n_bufferslots=128
        max_payload_len=8192
        ants=[(0,0,0),
        (1,1,1),
        (2,2,2),
        (3,3,3),
        (4,4,4),
        (5,5,5),
        (6,6,6),
        (7,7,7),
        (8,8,8),
        (9,9,9),
        (10,10,10),
        (11,11,11),
        (12,12,12),
        (13,13,13),
        (14,14,14),
        (15,15,15)]
        self.pols=['xx','yy','xy','yx']
        freqs = n.arange(self.n_chans, dtype=n.float) * sdf + sfreq
        beam = aipy.phs.Beam(freqs)
        ants = [aipy.phs.Antenna(a[0],a[1],a[2],beam) for a in ants]
        self.aa = aipy.phs.AntennaArray(ants=ants, location=location)

        self.bs=dacq.DataReceiver(self.aa, pols=self.pols,
            nchan=self.n_chans, sfreq=sfreq, sdf=sdf,
            inttime=int_time, t_per_file=ephem.second*10,
            nwin=n_windows_to_buffer, bufferslots=n_bufferslots, payload_len=max_payload_len)

        #bm = a.phs.Beam(n.array([.15]))
        #ants = [a.phs.Antenna(   0,   0,   0, bm),
        #        a.phs.Antenna( 210,-140,-260, bm),
        #        a.phs.Antenna( 200,-810,-250, bm),
        #        a.phs.Antenna(-250,-670, 310, bm),
        #        a.phs.Antenna(-280,-460, 350, bm),
        #        a.phs.Antenna(-280,-360, 340, bm),
        #        a.phs.Antenna(-170,-100, 220, bm),
        #        a.phs.Antenna( -70, -20, 100, bm),]
        #self.aa = a.phs.AntennaArray(('38','-80'), ants)
        #self.bs = dacq.DataReceiver(self.aa, pols=['xx'],
        #    nchan=2048, sfreq=0.121142578125, sdf=7.32421875e-05,
        #    inttime=14.3165578842, t_per_file=ephem.second*10)

    def dump_packet(self, pkt):
        print "Len:",pkt.packet_len,"Off:",pkt.heap_off
        print "XID:",pkt.engine_id
        #print "Data:",pkt.data
    def test_all_data(self):
        self.bs.start(PORT)
        xengs = [sim.XEngine(nant=len(self.aa),npol=len(self.pols),nchan=self.n_chans,engine_id=x) \
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
