from web3 import Web3

w3 = Web3(Web3.HTTPProvider('http://127.0.0.1:8545'))
print('Connected:', w3.is_connected())
if w3.is_connected():
    print('Chain ID:', w3.eth.chain_id)
    print('Block number:', w3.eth.block_number)
    print('Accounts:', len(w3.eth.accounts))
else:
    print('Connection failed')