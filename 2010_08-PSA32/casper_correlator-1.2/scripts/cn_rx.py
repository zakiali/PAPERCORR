#!/usr/bin/python
import casper_correlator,corr,ephem,aipy,numpy,sys

# 2-14-2011 Z.A. added 16-31 in 'ants'. preparation for 64 input corr.
if sys.argv[1:]==[]:
    print 'Please specify n for n-input correlator.'
    exit()      
args = sys.argv[1:]
nants = int(args[0])
port = 7148
n_chans=2048
bandwidth = 0.1
sdf = 7.32421875e-05 #bandwidth /n_chans in GHz
sfreq = 0.121142578125
int_time = 200000000./2048/2048/128 #integration time in seconds
location=0,0,0
acc_len = 2048 * 128
#acc_len = 1 
 # incoming data divided by this number for correct scaling
t_per_file=ephem.minute*10
n_windows_to_buffer=4
n_bufferslots=10240
max_payload_len=8192
ants=[]
for i in range(nants):
    ants.append((i,i,i))
pols=['xx','yy','xy','yx']
freqs = numpy.arange(n_chans, dtype=numpy.float) * sdf + sfreq
beam = aipy.phs.Beam(freqs)
ants = [aipy.phs.Antenna(a[0],a[1],a[2],beam) for a in ants]
aa = aipy.phs.AntennaArray(ants=ants, location=location)
sdisp_destination_ip = "127.0.0.1"

print "Sending signal display data to",sdisp_destination_ip

rx=casper_correlator.dacq.DataReceiver(aa, pols=pols, adc_rate=100000000,
            nchan=n_chans, sfreq=sfreq, sdf=sdf,
            inttime=int_time, t_per_file=t_per_file,
            nwin=n_windows_to_buffer, bufferslots=n_bufferslots, 
            payload_len=max_payload_len, sdisp=1, 
            sdisp_destination_ip=sdisp_destination_ip,
            acc_len=acc_len)
rx.start(port)

raw_input("Press Enter to terminate...\n") 
    #capture a bunch of stuff here

rx.stop()

