import argparse
import json

build_folder = '../smart-contract/build/contracts/%s.json'
contract_info_path =  'contract_address.json'
abi_info_path =  'abi_address.json'
UNIFORM_CONTRACT_NAME = 'Fogchain'

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--name', type=str,
                        help='the name of the contract')
    args = parser.parse_args()

    json_build = build_folder % args.name

    with open(json_build) as f:
        data = json.load(f)
        abi = data['abi']

    with open(contract_info_path, 'w') as f:
        data = {
            UNIFORM_CONTRACT_NAME:{
                'address': "0x0",
                'abi': abi
            }
        }
        json.dump(data, f)
        
    with open(abi_info_path, 'w') as g:
        data = {
            'abi': abi
        }
        json.dump(data, g)

    print('Successfully got abi')
    print('Please update the contract address in %s' % contract_info_path)
