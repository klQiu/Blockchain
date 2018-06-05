#!/bin/bash
chaindata_path="../geth/chaindata"
log_path="log/geth_log.txt"
boot_enode="enode://622ca699100a8c07575e8222e4d521565c39ba1ebc91a444f1b5707b3d69c47f77ef9c888014701c031fbfaef75ba837cc8ab013ffd11341ac36175941ad1d6b@10.27.11.220:30301"
rpc_modules="web3,eth,personal,miner,net,txpool"

echo "" >> $log_path
echo "start geth node on $(date +'%Y-%m-%d %T')\n" >> $log_path

geth --datadir=$chaindata_path --rpc --rpcapi=$rpc_modules \
	 --bootnodes $boot_enode 2>&1 | tee -a $log_path

