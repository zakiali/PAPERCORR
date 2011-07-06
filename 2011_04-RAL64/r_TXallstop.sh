#!/usr/bin/env bash

for ROACH in px1 px2 px3 px4 px5 px6 px7 px8
do
    `ssh root@$ROACH pkill -f corr_tx_cache_xaui.py`
    echo ssh root@$ROACH pkill -f corr_tx_cache_xaui.py 
done
