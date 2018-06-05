import sched, time
import argparse

from util import *
from consumer import post_cons

# the scheduler for executing task periodically
scheduler = sched.scheduler(time.time, time.sleep)
# just used for test
flag = 0

# web3 node
node = None
# smart contract
Fogchain = None
# account address of the transaction sender
from_account = None

nothing_formatter = '-'*40 + '\nSequential Numer: %d\nBattery Station: %s\nThe battery station did nothing\n' + '-'*40
response_formatter = '-'*40 + '\nSequential Numer: %d\nBattery Station: %s\nStorage: %d Joul\n' + '-'*40
post_sell_formatter = '-'*40 + '\nSequential Numer: %d\nBattery Station: %s\nResale: %d Joul\n' + '-'*40

def post_sell(amount):
    try:
        ## execute the function locally
        # response = Fogchain.functions.resell(seq_num, amount).call()
        # response = post_sell_formatter % (response[0], response[1], response[2])

        tx_hash = Fogchain.functions.post_sell(amount).transact({'from': from_account})
        tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
        event_logs = Fogchain.events.SellEvent().processReceipt(tx_receipt)
        args = event_logs[0]['args']
        response = post_sell_formatter % (args['seqnum'], args['sell_addr'], args['sold'])
        print(response)
    except ValueError as e:
        print('Failed to post_sell: ' + str(e))
        print('Last sequence block number of settlement:%d' % Fogchain.functions.get_last_settlement().call())
        print('Current sequence block number:%d ' % Fogchain.functions.get_current_seqnum().call()) 

def post_cons(amount):
    try:
        tx_hash = Fogchain.functions.post_cons(amount).transact({'from': from_account})
        tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
        event_logs = Fogchain.events.ConsEvent().processReceipt(tx_receipt)
        args = event_logs[0]['args']
        response = response_formatter % (args['seqnum'], args['cons_addr'], args['cons'])
        print(response)
    except ValueError as e:
        print('Failed to post_cons: ' + str(e))
        print('Last sequence block number of settlement:%d' % Fogchain.functions.get_last_settlement().call())
        print('Current sequence block number:%d ' % Fogchain.functions.get_current_seqnum().call())


def simulate(sc, delay, priority):
    '''
    simulate the interaction with the contract, 
    this function is used only for testing purpose
    '''

    '''TODO BEGIN:
        due to the filter bug of Ganache,
        shamelessly make the battery station wait for a settlement
    '''
    seqnum = Fogchain.functions.get_current_seqnum().call()
    while seqnum > Fogchain.functions.get_last_settlement().call() + 1:
        time.sleep(1.3)
    '''TODO END'''

    print(time.strftime('\n\n%X %x %Z')+' Calling smart contract')

    global flag
    if ((flag % 7 == 0) or (flag % 7 == 1)):
        post_cons(100)
    elif ((flag % 7 == 5) or (flag % 7 == 6)):
        post_sell(100)
    else:
        response = nothing_formatter % (seqnum, from_account)
        print(response)

    flag += 1
    sc.enter(delay, priority, simulate, argument=(sc, delay, priority))

 

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', type=str, default="127.0.0.1",
                        help='the rpc ip address of the node')
    parser.add_argument('-p', '--port', type=int, default=8545,
                        help='the rpc port number of the node')
    parser.add_argument('-a', '--account_idx', type=int, default=3,
                        help='the account index of the transaction sender')
    args = parser.parse_args()

    socket_addr = 'http://%s:%d' % (args.ip,args.port)
    print('connecting to node at %s \n\n' % socket_addr)

    # connect to the  node
    node = Web3(Web3.HTTPProvider(socket_addr))
    from_account = node.eth.accounts[args.account_idx]
    # node info
    display_node_info(node, from_account)

    Fogchain = get_contract(node, 'Fogchain')

    try:
        # register as a battery station
        tx_hash = Fogchain.functions.register_battery_station().transact({'from': from_account})
        # blocking until mined
        tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
    except ValueError:
        # already registered
        pass
    
    scheduler.enter(delay=10, priority=1, action=simulate, argument=(scheduler, 10, 1))
    scheduler.run()
