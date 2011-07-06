ROACH=$1

#Reset using the XPORT GPIOs:
#UDP Write to port 0x77F0 (30704)
#UDP String: 1A FF FF FF FF XX XX XX XX
#Last four bytes are the GPIO line values. The XPORT has only 3 GPIO's and only bit 1 is important. Bit 1 must be toggled to reset the board, easiest is to write FF FF FF FF and then 00 00 00 00.
#for ROACH in roach030111x roach030112x roach030113x roach030114x
for ROACH in px1x px2x px3x px4x px5x px6x px7x px8x 
do
    echo "Starting $ROACH..."
    echo -n -e "\0002\0201\0002\0377\0377" | nc -w 1 $ROACH 10001
done
