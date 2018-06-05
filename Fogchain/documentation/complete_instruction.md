# Setting up environment for Raspberry Pi
1. (optional, to remotely connect the Raspeberry Pi)
    + ssh default username `pi`, pwd `raspberry`
2. Install nodejs (5.0+)
    + `https://www.w3schools.com/nodejs/nodejs_raspberrypi.asp`
    + `sudo apt-get update`
    + `sudo apt-get dist-upgrade`
    + *If necessary*, remove old version of nodejs `https://www.raspberrypi.org/forums/viewtopic.php?t=141770`
    + `curl -sL https://deb.nodesource.com/setup_8.x | sudo -E bash -`
    + `sudo apt-get install -y nodejs`
    + check version `node -v`
3. Install Truffle 
    + `npm install -g truffle`  (`-g` to install globally)
4. *(optional, only for development and testing)* Install Ganache CLI
    + `npm install -g ganache-cli`
5. ~~Install Geth~~
    + ~~The following steps are deleted (DO NOT ever add any Debian/Ubuntu repositories or software)~~
    + ~~*If* `add-apt-repository` command not found, `apt-get install software-properties-common` (*change mirror if there is mirror issue* `https://ixu.me/pi-raspberry-3-using-ali-cloud-mirror-cloud.html`)~~
    + ~~`sudo add-apt-repository -y ppa:ethereum/ethereum`~~
    + ~~`sudo apt-get update` and `sudo apt-get install ethereum`~~
6. Install Geth
    + **(not used here)** Official Raspberry Pi instructions `https://github.com/ethereum/wiki/wiki/Raspberry-Pi-instructions`  
    + **Binary install** `https://ethereum.stackexchange.com/questions/31610/how-to-install-geth-on-rpi-3b`
        * find the latest arm7 geth binary (**Develop builds** for `bootnote` etc.) from `https://geth.ethereum.org/downloads/`, then download the release. E.g. `wget https://gethstore.blob.core.windows.net/builds/geth-alltools-linux-arm7-1.8.4-unstable-30deb606.tar.gz`
        * `tar -xvf geth-linux-arm7....`
        * `cd` to the bin folder
        * `sudo cp * /usr/local/bin/` (copy `geth`,`bootnode`... to PATH)
        * `geth h` to check whether it works
7. Web3 support
    + `pip3 install web3`

# Quick Start
## Initialization
1. Initialize blockchain meta info `geth --datadir=./chaindata/ init ./genesis.json`
    + the blockchain would be stored at the path specified by `datadir`
    + genesis state is specifed by the file after `init`, which all nodes agree upon
    + Future runs of geth on this data directory will use the genesis block you have defined. `geth --datadir path/to/custom/data/folder`
2. **To start a bootnode** (not a full fledged node)
    + `bootnode --genkey=boot.key`
    + `bootnode --nodekey=boot.key`
3. **To start a new node**
    + `geth --datadir=path/to/custom/data/folder --bootnodes <bootnode-enode-url> --rpc` (`--rpc` to accept RPC connections)
        * e.g. `geth --datadir=chaindata --bootnodes enode://622ca699100a8c07575e8222e4d521565c39ba1ebc91a444f1b5707b3d69c47f77ef9c888014701c031fbfaef75ba837cc8ab013ffd11341ac36175941ad1d6b@10.27.11.220:30301 --rpc --rpcapi=web3,eth,personal,miner,net,txpool`
    + **To start a geth console** when a node is running, either
        + Via ipc: `geth attach ipc:ipc/end/point`  (`ipc/end/point` is showed when a node starts running, e.g. `\\.\pipe\geth.ipc`) 
        + Via http endpoint (if http rpc enabled), e.g. `geth attach http://191.168.1.1:8545`
4. To enable mining
    + `geth <usual-flags> --mine --minerthreads=1 --etherbase=0x0000000000000000000000000000000000000000` (start mining blocks and transactions on a single CPU thread, crediting all proceedings to the account specified by `--etherbase`)


## Geth CLI utilities / Management APIs
- To start a geth console, check the previous section or refer to `https://github.com/ethereum/go-ethereum/wiki/JavaScript-Console`
- **Note that to enable different modules, options has to be specified when a node is started**, refer to `https://github.com/ethereum/go-ethereum/wiki/Management-APIs#enabling-the-management-apis` 


### Network connectivity
`https://github.com/ethereum/go-ethereum/wiki/Connecting-to-the-network`
1. checking connectivity:
    + `> net.listening`
    + `> net.peerCount`
    + `> admin.peers`
    + `> admin.nodeInfo`

### Account management
`https://github.com/ethereum/go-ethereum/wiki/Managing-your-accounts#creating-accounts`


### Mining
- `> miner.start()`, `> miner.stop()`


## Contract Migration from Truffle to Geth
1. First unlock the account to enable contract migration ability. `personal.unlockAccount('accountaddress', 'pwdphrase')` 
2. change the migration configuration in `truffle-config.js` according to the rpc http endpoint of the geth node.
3. `truffle migrate --network netname`
    + make sure there are miners running in the network to confirm the contract submission

## Interacting with the Contract by Management API
### Construct the contract obj by `eth` API
In order to other people to run your contract they need two things: the address where the contract is located and the ABI (Application Binary Interface) which is a sort of user manual, describing the name of its functions and how to call them.
- command template: `var varName = eth.contract(ABI).at(Address);`
- e.g. `var greeter = eth.contract([{constant:false,inputs:[],name:'kill',outputs:[],type:'function'},{constant:true,inputs:[],name:'greet',outputs:[{name:'',type:'string'}],type:'function'},{inputs:[{name:'_greeting',type:'string'}],type:'constructor'}]).at('greeterAddress');`
- There are a number of ways to get the ABI of a contract. The following way extracts it from the Truffle build file generated after `truffle compile`
    + The abi is stored in the `abi` object in the contract json file in the build folder of the truffle project

### Call the contract
- use `varName.functionName` to call functions in the contract. 
- e.g. `greeter.greet()`



# Misc
- Bootnode enode: `enode://590397fafe0f280d1d34c3f6d1c3e1a87485ef5863bf25bc6e883ede80a903f772713e0b83cb14d1496411b8d037a1d9bed993ce217cac86c52bf9953646e802@121.42.159.28:30301`
- Currently the smart contracts are developed in in Truffle and compiled and migrated to Geth node by Truffle command, future work would do it with `solc` python package and merge it into user interface.


