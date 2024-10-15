from flask import Flask, jsonify, request, send_file
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import SigningKey, SECP256k1, VerifyingKey
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.backends import default_backend
import binascii
import traceback
import hashlib
import io
import logging

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
blockchain = Blockchain()

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

@app.route('/mine', methods=['POST'])
def mine():
    try:
        values = request.get_json()
        miner_address = values.get('miner_address')
        if not miner_address:
            return jsonify({'message': 'Missing miner address'}), 400

        block = blockchain.mine(miner_address)
        new_balance = blockchain.get_balance(miner_address)
        logger.info(f"Mined block for {miner_address}. New balance: {new_balance}")

        response = {
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
            'new_balance': new_balance
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error mining new block: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Error mining new block: {str(e)}'}), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    try:
        values = request.get_json()
        logger.info(f"Received transaction request: {values}")
        required = ['sender', 'recipient', 'amount', 'signature']
        if not all(k in values for k in required):
            return jsonify({'message': 'Missing values'}), 400

        sender = values['sender']
        recipient = values['recipient']
        amount = float(values['amount'])
        signature = bytes.fromhex(values['signature'])

        logger.info(f"Sender: {sender}")
        logger.info(f"Recipient: {recipient}")
        logger.info(f"Amount: {amount}")
        logger.info(f"Signature: {signature.hex()}")

        # Verify the transaction signature
        #try:
        #    if not blockchain.verify_transaction(sender, recipient, amount, signature):
        #        return jsonify({'message': 'Invalid transaction signature'}), 400
       #except Exception as e:
        #    logger.error(f"Error verifying signature: {str(e)}")
        #    return jsonify({'message': f'Error verifying signature: {str(e)}'}), 400

        # Check if sender has sufficient balance
        sender_balance = blockchain.get_balance(sender)
        logger.info(f"Sender balance before transaction: {sender_balance}")
        if sender_balance < amount:
            return jsonify({'message': f'Insufficient funds. Balance: {sender_balance}, Amount: {amount}'}), 400

        # Create the transaction and mine the block immediately
        block = blockchain.new_transaction_and_mine(sender, recipient, amount, values['signature'])
        
        new_sender_balance = blockchain.get_balance(sender)
        new_recipient_balance = blockchain.get_balance(recipient)
        logger.info(f"New sender balance: {new_sender_balance}")
        logger.info(f"New recipient balance: {new_recipient_balance}")

        response = {
            'message': f'Transaction processed and added to Block {block["index"]}',
            'new_sender_balance': new_sender_balance,
            'new_recipient_balance': new_recipient_balance
        }
        return jsonify(response), 201
    except ValueError as ve:
        logger.error(f"ValueError in new_transaction: {str(ve)}")
        return jsonify({'message': str(ve)}), 400
    except Exception as e:
        logger.error(f"Error processing transaction: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Error processing transaction: {str(e)}'}), 500

@app.route('/chain', methods=['GET'])
def full_chain():
    try:
        logger.info("Fetching full blockchain")
        chain = blockchain.chain
        logger.info(f"Chain length: {len(chain)}")
        logger.debug(f"Chain content: {chain}")
        response = {
            'chain': chain,
            'length': len(chain),
        }
        return jsonify(response), 200
    except Exception as e:
        logger.error(f"Error fetching blockchain: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Error fetching blockchain: {str(e)}'}), 500

@app.route('/generate_keys', methods=['GET'])
def generate_keys():
    try:
        wallet = blockchain.generate_wallet()
        logger.info(f"Generated new wallet. Address: {wallet['address']}")
        return jsonify(wallet), 200
    except Exception as e:
        logger.error(f"Error in generate_keys: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'message': f'Failed to generate keys: {str(e)}'}), 500

@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if not address:
        return jsonify({'message': 'Missing address parameter'}), 400
    balance = blockchain.get_balance(address)
    logger.info(f"Balance request for address {address}: {balance}")
    return jsonify({'balance': balance}), 200

@app.route('/download_private_key', methods=['POST'])
def download_private_key():
    values = request.get_json()
    if not values:
        return jsonify({'message': 'No data provided'}), 400
    
    private_key_hex = values.get('private_key')
    password = values.get('password')
    
    if not private_key_hex or not password:
        return jsonify({'message': 'Missing values'}), 400
    
    try:
        # Convert hex string to bytes
        private_key_bytes = bytes.fromhex(private_key_hex)
        
        # Create an EC private key object
        private_key = ec.derive_private_key(
            int.from_bytes(private_key_bytes, byteorder='big'),
            ec.SECP256K1(),
            default_backend()
        )
        
        # Serialize the private key to PEM format
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode())
        )
        
        # Create a BytesIO object from the PEM data
        pem_io = io.BytesIO(pem)
        pem_io.seek(0)
        
        # Send the file
        return send_file(
            pem_io,
            as_attachment=True,
            download_name='private_key.pem',
            mimetype='application/x-pem-file'
        )
    
    except Exception as e:
        logger.error(f"Error generating PKCS#5 key: {str(e)}")
        return jsonify({'message': 'Error generating PKCS#5 key'}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)