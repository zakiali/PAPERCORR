#!/usr/bin/python
import casper_correlator,corr,ephem,aipy,numpy,sys

# 2-14-2011 Z.A. added 16-31 in 'ants'. preparation for 64 input corr.
if sys.argv[1:]==[]:
    print 'Please specify n for n-input correlator.'
    exit()      
lh=corr.log_handlers.DebugLogHandler()
c=corr.corr_functions.Correlator(sys.argv[1],lh)
nants = c.config['n_ants']
port = c.config['rx_udp_port']
n_chans = c.config['n_chans']
bandwidth = c.config['adc_clk']/2 # GHz
sdf = bandwidth/n_chans
sfreq = bandwidth # Second Nyquist zone
location=0,0,0
acc_len = c.config['acc_len'] * c.config['xeng_acc_len']
int_time = 2*n_chans*acc_len/(bandwidth*2*1e9) #integration time in seconds
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

try:
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
except(KeyboardInterrupt):
    rx.stop()







