from flask import Flask, jsonify, request
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import SigningKey, SECP256k1
import binascii
import traceback
import re

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
blockchain = Blockchain()

def clean_public_key(key):
    return re.sub(r'\s+', '', key)

@app.route('/mine', methods=['POST'])
def mine():
    try:
        values = request.get_json()
        miner_address = clean_public_key(values.get('miner_address'))
        if not miner_address:
            return jsonify({'message': 'Missing miner address'}), 400

        block = blockchain.mine(miner_address)

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
        }
        return jsonify(response), 200
    except Exception as e:
        app.logger.error(f"Error mining new block: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'message': f'Error mining new block: {str(e)}'}), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    try:
        values = request.get_json()
        required = ['sender', 'recipient', 'amount', 'signature']
        if not all(k in values for k in required):
            return jsonify({'message': 'Missing values'}), 400

        sender = clean_public_key(values['sender'])
        recipient = clean_public_key(values['recipient'])
        amount = float(values['amount'])

        # Crear la transacción y minar el bloque inmediatamente
        block = blockchain.new_transaction_and_mine(sender, recipient, amount, values['signature'])
        
        response = {
            'message': f'Transaction processed and added to Block {block["index"]}'
        }
        return jsonify(response), 201
    except ValueError as ve:
        return jsonify({'message': str(ve)}), 400
    except Exception as e:
        app.logger.error(f"Error processing transaction: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'message': f'Error processing transaction: {str(e)}'}), 500

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    private_key = binascii.hexlify(sk.to_string()).decode('ascii')
    public_key = binascii.hexlify(vk.to_string()).decode('ascii')
    
    blockchain.balances[public_key] = 10  # Dar 10 unidades de moneda inicial
    
    return jsonify({'private_key': private_key, 'public_key': public_key}), 200

@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if not address:
        return jsonify({'message': 'Missing address parameter'}), 400
    balance = blockchain.get_balance(clean_public_key(address))
    return jsonify({'balance': balance}), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
