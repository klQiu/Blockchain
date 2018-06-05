import json
from web3 import Web3

contract_info_path = 'contract_address.json'

def json_to_contract_interface(contract_name):
    '''get the contract address and abi from a json file
    
    Args:
        contract_name (str): the name of the contract

    Returns:
        (str, list): the contract address and contract abi

    Raises:
        KeyError: if the contract can not be found by `contract_name`
    '''
    with open(contract_info_path, 'r') as f:
        contract = json.load(f).get(contract_name)
    
    if contract is None:
        raise KeyError('Contract not found')

    return contract.get('address'), contract.get('abi')





def display_node_info(node, account=None):
    '''display node information
    
    Args:
        node(Web3): the Web3 instance (geth node)
        account(0x str): the address of the account to display info
    '''
    print('-'*50)
    print('chainId:', node.net.chainId)
    if account is None:
        print('accounts:', node.eth.accounts)
        print('coinbase address:', node.eth.coinbase)
        print('coinbase balance(wei):', node.eth.getBalance(node.eth.coinbase))
    else:
        print('account address:', account)
        print('account balance:', node.eth.getBalance(account))
    print('lastest block number:', node.eth.blockNumber)
    print('gas price(wei):', node.eth.gasPrice)
    print('-'*50+'\n')


def get_contract(node, contract_name):
    '''get contract instance

    Args:
        node(Web3): the Web3 instance (geth node)
        contract_name(str): the name of the contract
    '''
    address, abi = json_to_contract_interface(contract_name)
    try:
        contract = node.eth.contract(address=address, abi=abi)
    except Exception:
        address = node.toChecksumAddress(address)
        contract = node.eth.contract(address=address, abi=abi)
    return contract





    
    