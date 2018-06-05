1. start ganache node
    - `ganache-cli --port 8545 -b 1`
2. deploy the smart contract
    - `cd` to `smart-contract` folder
    - `truffle compile`
    - `truffle migrate --network development`
    - ~~copy the abi object from `smart-contract/build/contracts/Fogchain_1.json` to `interface/contract_address.json`~~ `cd` to `interface/`, run `get_contract_abi.py --name <contract_name>` 
    - copy the `FogChain_1` contract address from console to `interface/contract_address.json`
3. start the interface
    - `cd` to `interface/`
    - `python3 <node_type>.py --ip <ganache_ip>`  the default ip argument is local host, set it to the ip address where the ganache node is hosted if necessary
