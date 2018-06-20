#! /bin/sh
ETH0=enp0s31f6 #有线网卡
WIFI=wlx485d605766e1 #无线网卡

ETH_RTT=50ms
ETH_RATE=7040kbit

WIFI_RTT=70ms
WIFI_RATE=9185kbit

tc qd del dev $ETH0 root
tc qd add dev $ETH0 root handle 1:0 tbf rate $ETH_RATE latency 50ms burst 1540
tc qd add dev $ETH0 parent 1:0 handle 10:0 netem delay $ETH_RTT

tc qd del dev $WIFI root
tc qd add dev $WIFI root handle 1:0 tbf rate $WIFI_RATE latency 50ms burst 1540
tc qd add dev $WIFI parent 1:0 handle 10:0 netem delay $WIFI_RTT
