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
from wallet_generator import WalletGenerator  # Añadir esta importación

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad
from Crypto.Random import get_random_bytes
import base64

app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": ["http://localhost:3000"],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})
blockchain = Blockchain()

blockchain.public_keys = {}

def clean_public_key(key):
    return re.sub(r'\s+', '', key)

@app.route('/generate_wallet', methods=['GET'])
def generate_wallet():
    try:
        print("Iniciando generación de wallet...")
        wallet_gen = WalletGenerator()
        wallet_data = wallet_gen.generate_wallet()
        
        print(f"Wallet generada exitosamente: {wallet_data['address']}")
        
        # Almacenar la clave pública y establecer balance inicial
        blockchain.public_keys[wallet_data['address']] = wallet_data['public_key']
        blockchain.balances[wallet_data['address']] = 10
        
        return jsonify(wallet_data), 200
    except Exception as e:
        print(f"Error en la ruta generate_wallet: {str(e)}")
        traceback.print_exc()  # Imprime el stack trace completo
        return jsonify({'error': str(e)}), 500

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
    if not blockchain.validate_chain():
        return jsonify({'message': 'The blockchain is invalid'}), 400
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
    try:
        # Convertir la clave pública de hex a bytes
        public_key_bytes = bytes.fromhex(public_key)
        
        # 1. SHA256
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        
        # 2. RIPEMD160
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).hexdigest()
        
        return ripemd160_hash
    except Exception as e:
        print(f"Error en generate_address_from_public_key: {str(e)}")
        raise

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
    try:
        data = request.get_json()
        encrypted_private_key = data.get('encrypted_private_key')
        password = data.get('password')

        print(f"Recibida solicitud de descifrado")
        print(f"Password recibida: {password}")
        print(f"Encrypted key recibida: {encrypted_private_key}")

        if not encrypted_private_key or not password:
            return jsonify({'error': 'Missing encrypted_private_key or password'}), 400

        try:
            decrypted_private_key = decrypt_private_key(encrypted_private_key, password)
            return jsonify({'decrypted_private_key': decrypted_private_key}), 200
        except Exception as e:
            print(f"Error específico en el descifrado: {str(e)}")
            return jsonify({'error': f'Decryption failed: {str(e)}'}), 400

    except Exception as e:
        print(f"Error general en la ruta: {str(e)}")
        return jsonify({'error': str(e)}), 500

def decrypt_private_key(encrypted_private_key, password):
    try:
        print(f"Intentando descifrar con password: {password}")
        print(f"Encrypted key recibida: {encrypted_private_key}")
        
        # Decode the base64 encrypted data
        encrypted_data = base64.b64decode(encrypted_private_key)
        print(f"Longitud de datos cifrados: {len(encrypted_data)}")

        # Extract salt, IV, and ciphertext
        salt = encrypted_data[:16]
        iv = encrypted_data[16:32]
        ciphertext = encrypted_data[32:]
        
        print(f"Salt (hex): {salt.hex()}")
        print(f"IV (hex): {iv.hex()}")

        # Derive the key from the password and salt
        key = PBKDF2(password, salt, dkLen=32)
        print(f"Derived key (hex): {key.hex()}")

        # Create an AES cipher object
        cipher = AES.new(key, AES.MODE_CBC, iv)

        # Decrypt the data
        decrypted_padded_data = cipher.decrypt(ciphertext)
        
        # Unpad the decrypted data
        decrypted_data = unpad(decrypted_padded_data, AES.block_size)
        result = decrypted_data.decode()
        
        print(f"Descifrado exitoso, resultado: {result}")
        return result
        
    except Exception as e:
        print(f"Error durante el descifrado: {str(e)}")
        raise

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

        # Convertir los valores numéricos
        transaction_data['amount'] = float(transaction_data['amount'])
        transaction_data['fee'] = float(transaction_data['fee'])

        # Obtener el bloque
        block = blockchain.chain[block_index]

        # Verificación especial para transacciones del contrato
        if transaction_data.get('type') == 'contract_transfer':
            matching_transaction = next(
                (tx for tx in block['transactions'] if 
                 tx.get('type') == 'contract_transfer' and
                 tx['sender'] == transaction_data['sender'] and 
                 tx['recipient'] == transaction_data['recipient'] and 
                 abs(float(tx['amount']) - transaction_data['amount']) < 0.00001 and
                 (not tx.get('fee') or abs(float(tx.get('fee', 0)) - transaction_data['fee']) < 0.00001)
                ),
                None
            )

            if matching_transaction:
                if (transaction_data['sender'] == 'escrow_contract' and
                    matching_transaction.get('signature') == 'VALID'):
                    return jsonify({'message': 'Válido'}), 200
            
            return jsonify({'message': 'Error'}), 400

        # Para transacciones normales
        matching_transaction = next(
            (tx for tx in block['transactions'] if 
             tx['sender'] == transaction_data['sender'] and 
             tx['recipient'] == transaction_data['recipient'] and 
             abs(float(tx['amount']) - transaction_data['amount']) < 0.00001 and  # Usar comparación aproximada
             abs(float(tx.get('fee', 0)) - transaction_data['fee']) < 0.00001),   # Usar comparación aproximada
            None
        )

        if not matching_transaction:
            return jsonify({'message': 'Error'}), 400

        transaction_data['timestamp'] = matching_transaction['timestamp']
        transaction_copy = transaction_data.copy()
        transaction_copy.pop('signature', None)

        is_valid = verify_signature(public_key, transaction_copy, signature)
        if is_valid:
            return jsonify({'message': 'Válido'}), 200
        else:
            return jsonify({'message': 'Error'}), 400

    except Exception as e:
        print(f"Error en verify_block: {str(e)}")
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
    vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    transaction_string = json.dumps(transaction, sort_keys=True)
    try:
        vk.verify(bytes.fromhex(signature), transaction_string.encode())
        return True
    except:
        return False
    
    
@app.route('/escrow/create', methods=['POST'])
def create_escrow():
    try:
        values = request.get_json()
        required = ['buyer', 'seller', 'amount', 'description', 'privateKey']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        # Generar ID único para el acuerdo
        agreement_id = hashlib.sha256(
            f"{values['buyer']}{values['seller']}{time()}".encode()
        ).hexdigest()

        # Crear el acuerdo y la transacción de fondos
        blockchain.escrow_contract.create_agreement(
            agreement_id=agreement_id,
            buyer=values['buyer'],
            seller=values['seller'],
            amount=float(values['amount']),
            description=values['description'],
            buyer_private_key=values['privateKey']
        )

        return jsonify({
            'message': 'Escrow agreement created and funds transfer transaction added to mempool',
            'agreement_id': agreement_id
        }), 201

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/confirm-shipment', methods=['POST'])
def confirm_shipment():
    try:
        values = request.get_json()
        required = ['agreement_id', 'seller', 'tracking_info']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        # Actualizar el estado directamente
        success = blockchain.escrow_contract.confirm_shipment(
            agreement_id=values['agreement_id'],
            seller=values['seller'],
            tracking_info=values['tracking_info']
        )

        if success:
            return jsonify({'message': 'Shipment confirmed', 'status': 'SHIPPED'}), 200
        else:
            return jsonify({'error': 'Failed to confirm shipment'}), 400

    except Exception as e:
        return jsonify({'error': str(e)}), 400
    
@app.route('/escrow/confirm-seller', methods=['POST'])
def confirm_seller():
    try:
        values = request.get_json()
        required = ['agreement_id', 'seller']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        blockchain.escrow_contract.confirm_seller_participation(
            agreement_id=values['agreement_id'],
            seller=values['seller']
        )

        return jsonify({'message': 'Seller participation confirmed'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/confirm-delivery', methods=['POST'])
def confirm_delivery():
    try:
        values = request.get_json()
        required = ['agreement_id', 'buyer']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        # Confirmar entrega y crear transacciones de pago
        blockchain.escrow_contract.confirm_delivery(
            agreement_id=values['agreement_id'],
            buyer=values['buyer']
        )

        return jsonify({'message': 'Delivery confirmed and payment transactions added to mempool'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/open-dispute', methods=['POST'])
def open_dispute():
    try:
        values = request.get_json()
        required = ['agreement_id', 'party', 'reason']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        blockchain.escrow_contract.open_dispute(
            agreement_id=values['agreement_id'],
            party=values['party'],
            reason=values['reason']
        )

        return jsonify({'message': 'Dispute opened'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/agreements/<wallet_address>', methods=['GET'])
def get_agreements(wallet_address):
    """Obtiene todos los acuerdos relacionados con una dirección"""
    try:
        agreements = []
        for agreement_id, agreement in blockchain.escrow_contract.state['agreements'].items():
            if agreement['buyer'] == wallet_address or agreement['seller'] == wallet_address:
                agreement_copy = agreement.copy()
                agreement_copy['id'] = agreement_id
                agreements.append(agreement_copy)

        return jsonify({'agreements': agreements}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/agreement/<agreement_id>', methods=['GET'])
def get_agreement(agreement_id):
    try:
        agreement = blockchain.escrow_contract.get_agreement(agreement_id)
        if not agreement:
            return jsonify({'error': 'Agreement not found'}), 404

        return jsonify(agreement), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)