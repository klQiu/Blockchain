import sched, time
import argparse
import csv

from util import *

# the scheduler for executing task periodically
scheduler = sched.scheduler(time.time, time.sleep)
# emulator data
consumer_datapath = '../data-emulator/consumer/emulation_res.csv'
f = open(consumer_datapath, 'r')
csv_reader = csv.reader(f)
headers = next(csv_reader)


# web3 node
node = None
# smart contract
Fogchain = None
# account address of the transaction sender
from_account = None

response_formatter = '-'*40 + '\nSequential Numer: %d\nConsumer: %s\nConsumption: %d Joul\n' + '-'*40
local_rep_formatter = '-'*40 + '\nSequential Numer: %d\nConsumption: %d Joul\n' + '-'*40

def post_cons(amount):
    try:
        # # execute the function locally
        # transaction = {'from': node.eth.accounts[3]}
        # gas_estimate = Fogchain.functions.post_cons(amount).estimateGas(transaction)
        # response = Fogchain.functions.post_cons(amount).call({'from': node.eth.accounts[3], 'gas': gas_estimate*10})
        # response = local_rep_formatter % (response[0], response[1])
        # print(response)
        # return

        # execute the function publicly
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
    try:
        consumption = next(csv_reader)[2]
    # if EOF
    except StopIteration:
        f.seek(0)
        next(csv_reader)
        consumption = next(csv_reader)[2]

    # convert to int for smart contract
    consumption = round(float(consumption) + 259)

    '''TODO BEGIN:
        due to the filter bug of Ganache,
        shamelessly make the consumer wait for a settlement
    '''
    while Fogchain.functions.get_current_seqnum().call() > \
            Fogchain.functions.get_last_settlement().call() + 1:
        time.sleep(1.5)
    '''TODO END'''

    print(time.strftime('\n\n%X %x %Z')+' Calling smart contract') 
    post_cons(consumption)

    sc.enter(delay, priority, simulate, argument=(sc, delay, priority))
 


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-i', '--ip', type=str, default="127.0.0.1",
                        help='the rpc ip address of the node')
    parser.add_argument('-p', '--port', type=int, default=8545,
                        help='the rpc port number of the node')
    parser.add_argument('-a', '--account_idx', type=int, default=1,
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
        # register as a consumer
        tx_hash = Fogchain.functions.register_consumer().transact({'from': from_account})
        # blocking until mined
        tx_receipt = node.eth.waitForTransactionReceipt(tx_hash)
    except ValueError:
        # already registered
        pass

    scheduler.enter(delay=10, priority=1, action=simulate, argument=(scheduler, 10, 1))
    scheduler.run()
