pragma solidity ^0.4.23;


contract Mortal {
    /* Define variable owner of the type address */
    address owner;

    /* This function is executed at initialization and sets the owner of the contract */
    function Mortal() public { owner = msg.sender; }

    /* Function to recover the funds on the contract */
    function kill() public { if (msg.sender == owner) selfdestruct(owner); }
}


contract Fogchain_2 is Mortal {
    struct Account{
        uint8 role;
        // amount of electricity consumption, in Joul
        uint consumption;
        // amount of output by prosumer or battery station or power station, in Joul
        uint output;
        // unpaid expense, negative denotes income
        int bill;
    }

    // CONSUMER denotes the registration status, 
    // other roles are regarded as special consumers
    uint8 constant public CONSUMER = 1;
    uint8 constant public PROSUMER = 2;
    // battery station
    uint8 constant public RETAILER = 3;
    /* POWER_STATION is not used since we assume the electricity generation
     * of power station can be derived from the difference between consumption and
     * prosumer production.  
     */
    uint8 constant public POWER_STATION = 4;

    // the starting time of the system, for calculating sequence block number
    uint public TIME_START;
    // the interval of a sequence block 
    uint public SEQUENCE_INV;
    // the renewable electricity price for prosumer output
    uint public RENEWABLE_PRICE;
    // the unrenewable electricity price for power station output
    uint public UNRENEWABLE_PRICE;
    // the price settled by the last settlement
    uint public latest_price;
    // the latest sequence block number settled 
    uint public last_settlement;

    mapping(address => Account) public account_map;
    // mapping of the event-emitted account address, to avoid duplicated event
    mapping(address => bool) logged_map;
    address[] public consumer_addrs;
    address[] public pure_consumer_addrs;
    address[] public prosumer_addrs;
    address[] public retailer_addrs;
    address[] public power_station_addrs;

    event ConsEvent(uint indexed seqnum, address indexed cons_addr, uint cons);
    event ProdEvent(uint indexed seqnum, address indexed prod_addr, uint prod);
    event SellEvent(uint indexed seqnum, address indexed sell_addr, uint sold);
    event SettleEvent(uint indexed seqnum, uint indexed role, address indexed account_addr, uint consumption, uint output,  int expense);
    event PsGenEvent(uint indexed seqnum, address indexed ps_addr, uint generation);
    event PriceEvent(uint indexed seqnum, uint c_price, uint ps_price, uint bs_price, uint p_price);

    function Fogchain_2(uint seq_blk_interval, uint renew_price, uint unre_price) public {
        SEQUENCE_INV = seq_blk_interval;
        TIME_START = now;
        RENEWABLE_PRICE = renew_price;
        UNRENEWABLE_PRICE = unre_price;
        latest_price = (RENEWABLE_PRICE+UNRENEWABLE_PRICE)/2;
        last_settlement = 0;
    }

    // TODO: this modifier may incur undesirable gas cost due to settlement
    // make sure the previous sequence block is settled
    modifier only_completed_prev_seq(){
        /// TODO: due to the ganache event log filter bug, disable functions with 
        /// this modifier to call settle() (e.g. consumer, prosumer), such that the 
        /// monitor(power station) does not need a filter
        // if(get_current_seqnum() > (last_settlement+1)){
        //     settle();
        // }
        
        require(get_current_seqnum() <= last_settlement+1, "the previous block has been settled");
        _;
    }

    modifier not_registered(){
        require(account_map[msg.sender].role == 0);
        _;
    }

    /// get current sequence block number
    function get_current_seqnum() constant public  
        returns (uint seqnum) 
    {
        uint cur_seqnum = (now - TIME_START)/SEQUENCE_INV;
        return (cur_seqnum);
    }

    /// get last settlement sequence block number
    function get_last_settlement() constant public
        returns (uint seqnum)
    {
        return (last_settlement);
    }

    function get_bill(address account) constant public
        returns (int expense)
    {
        return account_map[account].bill;
    }

    function register_consumer() public not_registered{
        account_map[msg.sender].role = CONSUMER;
        consumer_addrs.push(msg.sender);
	pure_consumer_addrs.push(msg.sender);
    }

    function register_prosumer() public  not_registered{
        account_map[msg.sender].role = PROSUMER;
        consumer_addrs.push(msg.sender);
        prosumer_addrs.push(msg.sender);
    }

    function register_battery_station() public not_registered{
        account_map[msg.sender].role = RETAILER;
        consumer_addrs.push(msg.sender);
        retailer_addrs.push(msg.sender);
    }

    function register_power_station() public not_registered{
        account_map[msg.sender].role = POWER_STATION;
        consumer_addrs.push(msg.sender);
        power_station_addrs.push(msg.sender);
    }

    /// post consumption, assumption: any role can post_cons
    function post_cons(uint amount) public only_completed_prev_seq
        returns (uint seqnum, uint cons) 
    {   
        require(account_map[msg.sender].role != 0, "any registered node can consume");
        
        account_map[msg.sender].consumption += amount;

        uint cur_seqnum = get_current_seqnum();
        uint consumption = account_map[msg.sender].consumption;

        emit ConsEvent(cur_seqnum, msg.sender, consumption);
        return (cur_seqnum, consumption);
    }

    /// post production, assumption: only prosumer can post_cons
    function post_prod(uint amount) public only_completed_prev_seq
        returns (uint seqnum, uint prod)
    {   
        require(account_map[msg.sender].role == PROSUMER, "consitent node type");

        account_map[msg.sender].output += amount;

        uint cur_seqnum = get_current_seqnum();
        uint production = account_map[msg.sender].output;

        emit ProdEvent(cur_seqnum, msg.sender, production);
        return (seqnum, production);
    }

    /// post sale, assumption: only retailer(battery station) can post_sell
    function post_sell(uint amount) public only_completed_prev_seq
        returns (uint seqnum, uint sold)
    {
        require(account_map[msg.sender].role == RETAILER, "consitent node type");

        account_map[msg.sender].output += amount;

        uint cur_seqnum = get_current_seqnum();
        uint cur_sold = account_map[msg.sender].output;

        emit SellEvent(cur_seqnum, msg.sender, cur_sold);
        return (seqnum, cur_sold);
    }

    /// post power station generation, assumption: only power station can post_ps_gen
    function post_ps_gen(uint amount) public only_completed_prev_seq
        returns (uint seqnum, uint generation)
    {
        require(account_map[msg.sender].role == POWER_STATION, "consitent node type");

        account_map[msg.sender].output += amount;

        uint cur_seqnum = get_current_seqnum();
        uint cur_generation = account_map[msg.sender].output;

        emit PsGenEvent(cur_seqnum, msg.sender, cur_generation);
        return (seqnum, cur_generation);
    }

    /// settle the previous sequence block
    function settle() public returns (uint seqnum){
        uint cur_seqnum = get_current_seqnum();
        // return 0 if still in the sequence block next to the last_settlement
        if(cur_seqnum <= last_settlement+1){
            return 0;
        }

        uint cons_sum = 0;
        uint prod_sum = 0;
        uint bs_sum = 0;
        uint64 i = 0;

        // consumer_addrs contains all the registered account addresses
        for (i=0; i<consumer_addrs.length; i++){
            cons_sum += account_map[consumer_addrs[i]].consumption;
        }

        for (i=0; i<prosumer_addrs.length; i++){
            prod_sum += account_map[prosumer_addrs[i]].output;
        }

        for (i=0; i<retailer_addrs.length; i++){
            bs_sum += account_map[retailer_addrs[i]].output;
        }

        // TODO: the power station account is not used here, assuming power station does not consume electricity

        /* TODO BEGIN: 
         * the electricity generation is currently derived from the consumption data.
         * the derived electricity generation is all asigned to the first registered power station
         */
        uint ps_sum = cons_sum - prod_sum - bs_sum;
        uint revenue_sum = (latest_price*bs_sum)
                                +(UNRENEWABLE_PRICE*ps_sum)
                                +(RENEWABLE_PRICE*prod_sum);

        uint c_price;
        if(cons_sum != 0){
            c_price = revenue_sum/cons_sum;
        }
        else{
            c_price = latest_price;
        }
        emit PriceEvent(cur_seqnum-1, c_price, UNRENEWABLE_PRICE, latest_price, RENEWABLE_PRICE);
        int expense;
        uint consumption;
        uint output;

        // emit event for power station
        if(power_station_addrs.length == 0){
            emit SettleEvent(cur_seqnum-1, POWER_STATION, 0x0, 0, ps_sum, -int(ps_sum*UNRENEWABLE_PRICE));
        }
        else{
            expense = -int(ps_sum*UNRENEWABLE_PRICE);
            account_map[power_station_addrs[0]].bill += expense;
            emit SettleEvent(cur_seqnum-1, POWER_STATION, power_station_addrs[0], 
                account_map[power_station_addrs[0]].consumption, ps_sum, expense);
            logged_map[power_station_addrs[0]] = true;
        }
        /* TODO END */

        // emit event for battery stations
        for (i=0; i<retailer_addrs.length; i++){
            consumption = account_map[retailer_addrs[i]].consumption;
            output = account_map[retailer_addrs[i]].output;
            expense = int(c_price*consumption)
                        - int(latest_price*output);
            account_map[retailer_addrs[i]].bill += expense;
            emit SettleEvent(cur_seqnum-1, RETAILER, retailer_addrs[i], consumption, output, expense);
            logged_map[retailer_addrs[i]] = true;
        }

        // emit event for prosumers
        for (i=0; i<prosumer_addrs.length; i++){
            consumption = account_map[prosumer_addrs[i]].consumption;
            output = account_map[prosumer_addrs[i]].output;
            expense = int(c_price*consumption)
                        - int(RENEWABLE_PRICE*output);
            account_map[prosumer_addrs[i]].bill += expense;
            emit SettleEvent(cur_seqnum-1, PROSUMER, prosumer_addrs[i], consumption, output, expense);
            logged_map[prosumer_addrs[i]] = true;
        }

        // emit event for consumers who are not battery stations, prosumers or power stations
        // and clear all the logged record and data accumulation
        for (i=0; i<consumer_addrs.length; i++){
            // power station, or prosumer or battery station
            consumption = account_map[consumer_addrs[i]].consumption;
            if(logged_map[consumer_addrs[i]] == true){
                logged_map[consumer_addrs[i]] = false;
            }
            // pure consumer
            else{
                expense = int(c_price*consumption);
                emit SettleEvent(cur_seqnum-1, CONSUMER, consumer_addrs[i], consumption, 0, expense);
            }
            account_map[consumer_addrs[i]].output = 0;
            account_map[consumer_addrs[i]].consumption = 0;
        }
        
        latest_price = c_price;
        last_settlement = cur_seqnum - 1;
        return cur_seqnum;
    }
	
    //get all consumers' addresses
    function get_consumer_addresses() view public
        returns (address[])
    {
        return pure_consumer_addrs;
    }

    //get all prosumers' addresses
    function get_prosumer_addresses() view public
        returns (address[])
    {
        return prosumer_addrs;
    }

    //get all retailers' addresses
    function get_retailer_addresses() view public
        returns (address[])
    {
        return retailer_addrs;
    }

    //get all power stations' addresses
    function get_ps_addresses() view public
        returns (address[])
    {
        return power_station_addrs;
    }

    //get number of all addresses
    function get_address_number() view public
        returns (uint)
    {
        return consumer_addrs.length;
    }
}
