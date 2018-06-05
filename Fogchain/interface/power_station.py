import time 
import argparse
import csv

from util import *

'''
Power station listens to all the PriceEvent and SettleEvent.

TODO: Power station is supposed to settle a sequence block once the sequence block is ended,
      but as the invocation of settlement is not guaranteed to be from power station, this 
      feature may be changed in future.
'''

# web3 node
node = None
# smart contract
Fogchain = None
# account address of the transaction sender
from_account = None
# data emulator
datapath1 = '../data-emulator/power_station/emulation1.csv'
datapath2 = '../data-emulator/power_station/emulation2.csv'

price_event_filter = None
settle_event_filter = None


def get_role(role_code):
    '''
    convert the role code to specific role type string, 
    see SettleEvent in smart contract documentation
    '''
    if role_code == 1:
        return 'Consumer'
    elif role_code == 2:
        return 'Prosumer'
    elif role_code == 3:
        return 'Battery Station'
    elif role_code == 4:
        return 'Power Station'
    else:
        return 'Unknown type'

def handle_price_event(event):
    args = event['args']
    print('\n' + '-' * 60)
    print('Event name: %s' % event['event'])
    print('*' * 60)
    print('seqnum: %d' % args['seqnum'])
    print('consumption price: %d wei/Joul' % args['c_price'] + '\n')
    
    print('sale price (prosumers):\t\t%d wei/Joul' % args['p_price'])    
    print('sale price (battery station):\t%d wei/Joul' % args['bs_price'])
    print('sale price (power station):\t%d wei/Joul' % args['ps_price'])
    print('-' * 60 + '\n')
    seqnum = args['seqnum']
    c_price = args['c_price']
    p_price = args['p_price']
    bs_price = args['bs_price']
    ps_price = args['ps_price']
    fieldnames2 = ['seqNum', 'consumption price', 'prosumer price', 'battery station price', 'power station price']
    with open(datapath2,'a',newline='') as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames2)
        writer.writerow({'seqNum':seqnum, 'consumption price':c_price, 'prosumer price':p_price, 'battery station price':bs_price, 'power station price':ps_price})
    print('-'*40 + '\n')

def handle_settle_event(event):
    args = event['args']
    # print('\n' + '-'*40)
    # print('Event name: %s' % event['event'])
    # print('*'*40)
    # print('seqnum: %d' % args['seqnum'])
    # print('account: %s' % args['account_addr'])
    print('')
    print('node type:\t\t%s' % get_role(args['role']))
    print('account:\t\t%s' % args['account_addr'])
    print('consumption:\t\t%d Joul' % args['consumption'])
    print('electricity output:\t%d Joul' % args['output'])
    print('expense:\t\t%d\n' % args['expense'])
    seqnum = args['seqnum']
    account = args['account_addr']
    expense = args['expense']
    fieldnames1 = ['seqNum', 'account', 'expense']
    with open(datapath1,'a',newline='') as csvfile:
        writer = csv.DictWriter(csvfile,fieldnames=fieldnames1)
        writer.writerow({'seqNum':seqnum,'account':account,'expense':expense})
    # print('-'*40 + '\n')


def monitor_events(poll_interval = 1.5):
    while True:
        '''TODO: see TODO section in main function'''
        # for event in price_event_filter.get_all_entries():
        #     handle_price_event(event)
        # for event in settle_event_filter.get_all_entries():
        #     handle_settle_event(event)
        if Fogchain.functions.get_current_seqnum().call() > \
            Fogchain.functions.get_last_settlement().call() + 1:
            settle()
        time.sleep(poll_interval)


# currently not used, see TODO section in class description
def settle():
    ## execute the function locally
    # response = Fogchain.functions.settle(seq_num).call()
    # response = response_formatter % (response[0], response[1], response[2])
    
    # execute the function publicly
    tx_hash = Fogchain.functions.settle().transact({'from': from_account})
    '''
    TODO BEGIN:
        blocking to handle events,
        shamelessly doing this because the createFilter API is not working
    '''
    tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
    settle_events = Fogchain.events.SettleEvent().processReceipt(tx_receipt)
    price_events = Fogchain.events.PriceEvent().processReceipt(tx_receipt)

    # handle PriceEvent
    for event in price_events:
        handle_price_event(event)

    # handle SettleEvent and display them together
    print('-' * 60)
    print('Event name: SettleEvent')
    print('*' * 60)
    num = price_events[0]['args']['seqnum']
    print('seqnum: %d' % num)
    for event in settle_events:
        handle_settle_event(event)
    print('-' * 60 + '\n')
    '''
    TODO END
    '''
   


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', type=str, default="127.0.0.1",
                        help='the rpc ip address of the node')
    parser.add_argument('-p', '--port', type=int, default=8545,
                        help='the rpc port number of the node')
    parser.add_argument('-a', '--account_idx', type=int, default=0,
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
        # register as a power station
        tx_hash = Fogchain.functions.register_power_station().transact({'from': from_account})
        # blocking until mined
        tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
    except ValueError:
        # already registered
        pass

    '''
    # TODO: creatFilter API is not working due to a known bug of ganache:
    # https://github.com/trufflesuite/ganache-cli/issues/494
    # https://github.com/ethereum/web3.py/issues/674
    '''
    price_event_filter = Fogchain.events.PriceEvent.createFilter(fromBlock=0)
    settle_event_filter = Fogchain.events.SettleEvent.createFilter(fromBlock=0)
    with open(datapath1, 'w', newline='') as outcsv1:
        fieldnames1 = ['seqNum', 'account', 'expense']
        writer1 = csv.DictWriter(outcsv1,fieldnames=fieldnames1)
        writer1.writeheader()

    with open(datapath2, 'w', newline='') as outcsv2:
        fieldnames2 = ['seqNum', 'consumption price', 'prosumer price', 'battery station price', 'power station price']
        writer2 = csv.DictWriter(outcsv2,fieldnames=fieldnames2)
        writer2.writeheader()
    monitor_events()
