#!/usr/bin/env bash

for ROACH in px1 px2 px3 px4 px5 px6 px7 px8
do
    var1=`ssh root@$ROACH pgrep -f '^/boffiles/.*bof$'`
    echo ssh root@$ROACH "corr_tx_cache_xaui.py -i 169.254.145.1 -x 2  $@ $var1"
    `ssh root@$ROACH "corr_tx_cache_xaui.py -i 169.254.145.1 -x 2  $@ $var1 < /dev/null >& /dev/null &"`
done
