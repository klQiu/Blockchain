pragma solidity ^0.4.23;

contract Mortal {
    /* Define variable owner of the type address */
    address owner;

    /* This function is executed at initialization and sets the owner of the contract */
    function Mortal() public { owner = msg.sender; }

    /* Function to recover the funds on the contract */
    function kill() public { if (msg.sender == owner) selfdestruct(owner); }
}

contract Fogchain_1 is Mortal {
    /* Define variable greeting of the type string */
    string version;
    int power_demand;

    event ConsumeEvent(
        uint seq_num,
        address from,
        int amount,
        uint portion,
        uint deposit);

    event ProduceEvent(
        uint seq_num,
        address from,
        int amount);

    event BatteryStoreEvent(
        uint seq_num,
        address from,
        int amount,
        uint deposit);

    event BatteryResellEvent(
        uint seq_num,
        address from,
        int amount);

    event SettleEvent(
        uint seq_num,
        address indexed from,
        int power_demand);

    /* This runs when the contract is executed */
    function Fogchain_1(string _version) public {
        version = _version;
    }

    /* post consumption function */
    function post_cons(uint seq_num, int amount, uint portion, uint money) public 
    returns (uint, address, int, uint, uint) {
        power_demand += amount;
        emit ConsumeEvent(seq_num, msg.sender, amount, portion, money);
        return (seq_num, msg.sender, amount, portion, money);
    }

    function post_prod(uint seq_num, int amount) public
    returns (uint, address, int){
        power_demand -= amount;
        emit ProduceEvent(seq_num, msg.sender, amount);
        return (seq_num, msg.sender, amount);
    }

    function post_store(uint seq_num, int amount, uint money) public
    returns (uint, address, int, uint){
        power_demand -= amount;
        emit BatteryStoreEvent(seq_num, msg.sender, amount, money);
        return (seq_num, msg.sender, amount, money);
    }

    function resell(uint seq_num, int amount) public
    returns (uint, address, int){
        power_demand += amount;
        emit BatteryResellEvent(seq_num, msg.sender, amount);
        return (seq_num, msg.sender, amount);
    }

    function settle(uint seq_num) public
    returns (uint, address, int){
        int req_power = 0;
        if(power_demand>0){
            req_power = power_demand;
            power_demand = 0;
        }
        emit SettleEvent(seq_num, msg.sender, req_power);
        return (seq_num, msg.sender, req_power);
    }
}