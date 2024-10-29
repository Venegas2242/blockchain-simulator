from flask import Flask, jsonify, request
from flask_cors import CORS
from blockchain import Blockchain
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import binascii
import traceback
import re
import hashlib
import json
from time import time

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
    print("\n=== INICIO DE GENERACIÓN DE WALLET ===")
    password = "1234"
    
    # 1. Generación de par de llaves usando ECDSA con curva SECP256k1
    print("1. Generando par de llaves usando ECDSA (Elliptic Curve Digital Signature Algorithm)")
    print("   Usando la curva SECP256k1 (la misma que usa Bitcoin)")
    sk = SigningKey.generate(curve=SECP256k1)
    vk = sk.get_verifying_key()
    
    # 2. Convertir llaves a formato hexadecimal
    print("\n2. Convirtiendo llaves a formato hexadecimal")
    private_key = binascii.hexlify(sk.to_string()).decode('ascii')
    public_key = binascii.hexlify(vk.to_string()).decode('ascii')
    print(f"   Llave privada (primeros 32 chars): {private_key[:32]}...")
    print(f"   Llave pública (primeros 32 chars): {public_key[:32]}...")
    
    # 3. Cifrar llave privada usando AES y PBKDF2
    print("\n3. Cifrando llave privada:")
    print("   - Usando PBKDF2 (Password-Based Key Derivation Function 2)")
    print("   - AES en modo CBC para el cifrado")
    print("   - Generando salt aleatorio de 16 bytes")
    encrypted = encrypt_private_key(private_key, password)
    
    # 4. Generar dirección usando RIPEMD160
    print("\n4. Generando dirección usando algoritmo RIPEMD160:")
    print("   a) Convertir llave pública a bytes")
    print("   b) Calcular SHA256 de la llave pública")
    print("   c) Calcular RIPEMD160 del resultado de SHA256")
    address = generate_address_from_public_key(public_key)
    print(f"   Dirección generada: {address}")

    # 5. Inicializar balance y almacenar llave pública
    print("\n5. Inicializando wallet en la blockchain:")
    if not hasattr(blockchain, 'public_keys'):
        blockchain.public_keys = {}
    
    blockchain.public_keys[address] = public_key
    blockchain.balances[address] = 10  # Balance inicial
    print(f"   Balance inicial establecido: {blockchain.balances[address]} BBC")
    print("=== FIN DE GENERACIÓN DE WALLET ===\n")

    return jsonify({
        'private_key': private_key,
        'public_key': public_key,
        'encrypted_key': encrypted,
        'address': address
    }), 200

@app.route('/mine', methods=['POST'])
def mine():
    print("\n=== INICIO DE MINADO ===")
    try:
        values = request.get_json()
        miner_address = clean_public_key(values.get('miner_address'))
        selected_transactions = values.get('selected_transactions', [])
        
        print(f"1. Minero: {miner_address[:8]}...")
        print(f"2. Transacciones seleccionadas: {len(selected_transactions)}")

        # 1. Minar el bloque
        print("\n3. Iniciando proceso de minado:")
        print("   a) Seleccionando transacciones de la mempool")
        print("   b) Calculando recompensa y comisiones")
        print("   c) Creando transacción coinbase")
        print("   d) Calculando merkle root")
        print("   e) Buscando nonce válido (Proof of Work)")
        block = blockchain.mine(miner_address, selected_transactions)
        
        # 2. Verificar validez de la cadena
        print("\n4. Verificando validez de la cadena completa")
        if not blockchain.validate_chain():
            print("ERROR: La cadena no es válida después del minado")
            blockchain.chain.pop()
            return jsonify({'message': 'Mining failed: invalid blockchain state'}), 500

        print("\n5. Minado exitoso:")
        print(f"   Nuevo bloque: #{block['index']}")
        print(f"   Hash: {block['hash'][:16]}...")
        print(f"   Transacciones: {len(block['transactions'])}")
        reward = next(tx['amount'] for tx in block['transactions'] if tx['sender'] == "0")
        print(f"   Recompensa total: {reward} BBC")
        print("=== FIN DE MINADO ===\n")

        return jsonify({
            'message': "New Block Forged",
            'index': block['index'],
            'transactions': block['transactions'],
            'previous_hash': block['previous_hash'],
            'hash': block['hash'],
            'reward': reward
        }), 200

    except Exception as e:
        print(f"ERROR durante el minado: {str(e)}")
        return jsonify({'message': f'Mining failed: {str(e)}'}), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    print("\n=== INICIO DE NUEVA TRANSACCIÓN ===")
    try:
        values = request.get_json()
        required = ['sender', 'recipient', 'amount', 'fee', 'privateKey']
        if not all(k in values for k in required):
            return jsonify({'message': 'Missing values'}), 400

        # 1. Preparar datos de la transacción
        print("1. Preparando datos de la transacción")
        sender = clean_public_key(values['sender'])
        recipient = clean_public_key(values['recipient'])
        amount = float(values['amount'])
        fee = float(values['fee'])
        private_key = values['privateKey']
        
        print(f"   De: {sender[:8]}...")
        print(f"   Para: {recipient[:8]}...")
        print(f"   Cantidad: {amount} BBC")
        print(f"   Comisión: {fee} BBC")

        # 2. Crear objeto de transacción
        print("\n2. Creando objeto de transacción")
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
            'timestamp': time()
        }
        print("   Transacción creada con timestamp:", transaction['timestamp'])

        # 3. Firmar la transacción
        print("\n3. Firmando transacción:")
        print("   a) Serializando transacción a JSON")
        print("   b) Generando firma usando ECDSA con la llave privada")
        signature = sign_transaction(private_key, transaction)
        transaction['signature'] = signature.hex()
        print(f"   Firma generada (primeros 32 chars): {transaction['signature'][:32]}...")

        # 4. Añadir a la mempool
        print("\n4. Añadiendo transacción a la mempool")
        blockchain.add_to_mempool(transaction)
        print("=== FIN DE NUEVA TRANSACCIÓN ===\n")
        
        return jsonify({'message': 'Transaction added to mempool'}), 201

    except Exception as e:
        print(f"ERROR en nueva transacción: {str(e)}")
        return jsonify({'message': f'Error processing transaction: {str(e)}'}), 500

@app.route('/mempool', methods=['GET'])
def get_mempool():
    """Endpoint para obtener las transacciones pendientes en la mempool"""
    mempool = blockchain.get_mempool()
    current_reward = blockchain.calculate_block_reward()
    
    return jsonify({
        'pending_transactions': mempool,
        'current_block_reward': current_reward,
        'mempool_size': len(mempool)
    }), 200

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
    print("\n--- INICIO DE CIFRADO DE LLAVE PRIVADA ---")
    # 1. Generar salt aleatorio
    salt = get_random_bytes(16)
    print(f"Salt generado (hex): {salt.hex()}")

    # 2. Derivar llave de 32 bytes usando PBKDF2
    print("Derivando llave de 32 bytes usando PBKDF2")
    key = PBKDF2(password, salt, dkLen=32)
    print(f"Llave derivada (hex): {key.hex()}")

    # 3. Crear objeto AES en modo CBC
    cipher = AES.new(key, AES.MODE_CBC)
    print(f"IV generado (hex): {cipher.iv.hex()}")

    # 4. Padding y cifrado
    print("Aplicando padding PKCS7 y cifrando con AES-CBC")
    padded_data = pad(private_key.encode(), AES.block_size)
    encrypted_data = cipher.encrypt(padded_data)

    # 5. Combinar salt, IV y datos cifrados
    encrypted_private_key = salt + cipher.iv + encrypted_data
    result = base64.b64encode(encrypted_private_key).decode()
    print("--- FIN DE CIFRADO DE LLAVE PRIVADA ---\n")
    return result

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

@app.route('/verify_block', methods=['POST'])
def verify_block():
    try:
        data = request.get_json()
        block_index = data.get('block_index')
        transaction_data = data.get('transaction')
        signature = data.get('signature')
        public_key = data.get('public_key')

        transaction_data['amount'] = float(transaction_data['amount'])
        transaction_data['fee'] = float(transaction_data['fee'])

        # Get the block from the specified index
        block = blockchain.chain[block_index]

        # Find the specific transaction in the block
        matching_transaction = next(
            (tx for tx in block['transactions'] if 
             tx['sender'] == transaction_data['sender'] and 
             tx['recipient'] == transaction_data['recipient'] and 
             tx['amount'] == transaction_data['amount'] and 
             tx['fee'] == transaction_data['fee']),
            None
        )  

        if not matching_transaction:
            return jsonify({'message': 'Error'}), 400

        # Access the timestamp from the specific transaction in the block
        transaction_data['timestamp'] = matching_transaction['timestamp']

        # Create a copy of the transaction without the signature to verify it
        transaction_copy = transaction_data.copy()
        transaction_copy.pop('signature', None)

        # Verify the signature using the provided public key
        is_valid = verify_signature(public_key, transaction_copy, signature)
        if is_valid:
            return jsonify({'message': 'Válido'}), 200
        else:
            return jsonify({'message': 'Error'}), 400
    except Exception as e:
        return jsonify({'message': 'Error'}), 400

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
