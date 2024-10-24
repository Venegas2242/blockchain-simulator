from flask import Flask, jsonify, request
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import binascii
import traceback
import re
import hashlib
import json

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64


app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
blockchain = Blockchain()

blockchain.public_keys = {}

def clean_public_key(key):
    return re.sub(r'\s+', '', key)

@app.route('/generate_wallet', methods=['GET'])
def generate_wallet():
    password = "1234"
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    private_key = binascii.hexlify(sk.to_string()).decode('ascii')
    encrypted = encrypt_private_key(private_key, password)
    public_key = binascii.hexlify(vk.to_string()).decode('ascii')
    
    address = generate_address_from_public_key(public_key)

    # Store the public key with the address
    blockchain.public_keys[address] = public_key
    blockchain.balances[address] = 10  # Dar 10 unidades de moneda inicial
    print(f"Setting balance for {address}: {blockchain.balances[address]}")

    return jsonify({
        'private_key': private_key,
        'public_key': public_key,
        'encrypted_key': encrypted,
        'address': address
    }), 200

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
        required = ['sender', 'recipient', 'amount', 'privateKey']
        if not all(k in values for k in required):
            return jsonify({'message': 'Missing values'}), 400

        sender = clean_public_key(values['sender'])
        recipient = clean_public_key(values['recipient'])
        amount = float(values['amount'])
        private_key = values['privateKey']

        # Crear la transacción
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount
        }

        # Firmar la transacción
        signature = sign_transaction(private_key, transaction)

        # Agregar la firma a la transacción
        transaction['signature'] = signature.hex()

        # Crear la transacción y minar el bloque inmediatamente
        block = blockchain.new_transaction_and_mine(sender, recipient, amount, transaction['signature'])
        
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
    if not blockchain.validate_chain():                                  # Nuevo Ver
        return jsonify({'message': 'The blockchain is invalid'}), 400    # Nuevo Ver
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200

    
@app.route('/generate_address', methods=['POST'])
def generate_address():
    values = request.get_json()
    if not values or 'public_key' not in values:
        return jsonify({'message': 'Missing public_key'}), 400

    public_key = clean_public_key(values['public_key'])
    address = generate_address_from_public_key(public_key)
    
    return jsonify({'address': address}), 200

def generate_address_from_public_key(public_key):
    public_key_bytes = bytes.fromhex(public_key)
    sha256_hash = hashlib.sha256(public_key_bytes).digest()
    ripemd160_hash = hashlib.new('ripemd160', sha256_hash).hexdigest()
    return ripemd160_hash

def encrypt_private_key(private_key, password):
    # Generate a random salt
    salt = get_random_bytes(16)

    # Derive a 32-byte key from the password using PBKDF2
    key = PBKDF2(password, salt, dkLen=32)

    # Create an AES cipher object
    cipher = AES.new(key, AES.MODE_CBC)

    # Pad the private key
    padded_data = pad(private_key.encode(), AES.block_size)

    # Encrypt the padded data
    encrypted_data = cipher.encrypt(padded_data)

    # Combine salt, IV, and encrypted data
    encrypted_private_key = salt + cipher.iv + encrypted_data

    # Encode as base64 for easy storage/transmission
    return base64.b64encode(encrypted_private_key).decode()

@app.route('/decrypt_private_key', methods=['POST'])
def decrypt_private_key_route():
    data = request.get_json()
    encrypted_private_key = data.get('encrypted_private_key')
    password = data.get('password')

    if not encrypted_private_key or not password:
        return jsonify({'error': 'Missing encrypted_private_key or password'}), 400

    try:
        decrypted_private_key = decrypt_private_key(encrypted_private_key, password)
        return jsonify({'decrypted_private_key': decrypted_private_key}), 200
    except Exception as e:
        return jsonify({'error': 'Decryption failed. Incorrect password or invalid data.'}), 400

def decrypt_private_key(encrypted_private_key, password):
    # Decode the base64 encrypted data
    encrypted_data = base64.b64decode(encrypted_private_key)

    # Extract salt, IV, and ciphertext
    salt = encrypted_data[:16]
    iv = encrypted_data[16:32]
    ciphertext = encrypted_data[32:]

    # Derive the key from the password and salt
    key = PBKDF2(password, salt, dkLen=32)

    # Create an AES cipher object
    cipher = AES.new(key, AES.MODE_CBC, iv)

    # Decrypt the data
    decrypted_padded_data = cipher.decrypt(ciphertext)

    # Unpad the decrypted data
    decrypted_data = unpad(decrypted_padded_data, AES.block_size)

    return decrypted_data.decode()

def sign_transaction(private_key, transaction):
    try:
        # Crear la clave de firma a partir de la clave privada
        sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        transaction_string = json.dumps(transaction, sort_keys=True)
        
        # Generar la firma
        signature = sk.sign(transaction_string.encode())
        return signature
    except Exception as e:
        print(f"Error al firmar la transacción: {str(e)}")
        raise
    
#! USAR O ADAPTAR PARA VERIFICAR BLOQUES
# def verify_signature(public_key, transaction, signature):
#     """Verifica la firma de una transacción usando la clave pública."""
#     vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
#     transaction_string = json.dumps(transaction, sort_keys=True)
#     try:
#         vk.verify(signature, transaction_string.encode())
#         return True
#     except:
#         return False

# Verificacion
@app.route('/verify_block', methods=['POST'])
def verify_block():
    data = request.get_json()
    block_index = data.get('block_index')
    if block_index is None or not (0 <= block_index < len(blockchain.chain)):
        return jsonify({'message': 'Invalid block index'}), 400

    block = blockchain.chain[block_index]
    if verify_block_transactions(block):
        return jsonify({'message': f'Block {block_index} is valid'}), 200
    else:
        return jsonify({'message': f'Block {block_index} contains invalid transactions'}), 400

def verify_block_transactions(block):
    for transaction in block['transactions']:
        sender = transaction['sender']

        if sender == "0": # Si es minado
            return True
        
        signature = transaction['signature']

        # Obtenemos clave publica
        public_key = blockchain.public_keys.get(sender)
        if not public_key:
            return False  
        
        # Crear una copia de la transacción sin la firma para verificarla
        transaction_copy = transaction.copy()
        transaction_copy.pop('signature')
        
        # Verificar la firma
        if not verify_signature(public_key, transaction_copy, signature):
            return False  
    return True


@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if not address:
        return jsonify({'message': 'Missing address parameter'}), 400
    
    print(f"Retrieving balance for {address}")
    balance = blockchain.get_balance(clean_public_key(address))
    return jsonify({'balance': balance}), 200

def verify_signature(public_key, transaction, signature):
    # Verifica la firma de una transacción usando la clave pública.
    vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    transaction_string = json.dumps(transaction, sort_keys=True)
    try:
        vk.verify(bytes.fromhex(signature), transaction_string.encode())
        return True
    except:
        return False

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
