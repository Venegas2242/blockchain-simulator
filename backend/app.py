from flask import Flask, jsonify, request
from flask_cors import CORS
from blockchain import Blockchain
import traceback
import re
import hashlib
import json
from time import time
from wallet_generator import WalletGenerator
from crypto_utils import verify_signature, sign_transaction
import secrets

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
    print("\n===== INICIO DE MINADO =====")
    try:
        values = request.get_json()
        miner_address = clean_public_key(values.get('miner_address'))
        selected_transactions = values.get('selected_transactions', [])
        
        print(f"Direccion del minero: {miner_address}")
        print(f"Transacciones seleccionadas: {selected_transactions}")
        
        # Detener cualquier minado en curso
        blockchain.stop_mining()
        
        try:
            block = blockchain.mine(miner_address, selected_transactions)
            print(f"Bloque minado exitosamente: {block}")
            
            if not blockchain.validate_chain():
                print("Error: La cadena quedó inválida después del minado")
                blockchain.chain.pop()
                return jsonify({'message': 'Mining failed: invalid blockchain state'}), 500
            
            result = {
                'message': "New Block Forged",
                'index': block['index'],
                'transactions': block['transactions'],
                'previous_hash': block['previous_hash'],
                'hash': block['hash'],
                'nonce': block['nonce']
            }
            
            print(f"Resultado del minado: {result}")
            return jsonify(result), 200
            
        except ValueError as ve:
            print(f"Minado interrumpido: {str(ve)}")
            return jsonify({'message': 'Mining stopped'}), 200
            
    except Exception as e:
        print(f"ERROR durante el minado: {str(e)}")
        traceback.print_exc()
        return jsonify({'message': f'Mining failed: {str(e)}'}), 500
    finally:
        blockchain.mining_stopped = True

@app.route('/mine/progress', methods=['GET'])
def get_mining_progress():
    try:
        progress = blockchain.get_mining_progress()
        return jsonify(progress), 200
    except Exception as e:
        print(f"Error al obtener progreso de minado: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    print("\n====== INICIO DE NUEVA TRANSACCIÓN ======\n")
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

        # 2. Crear objeto de transacción
        transaction = {
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'fee': fee,
            'timestamp': time(),
            'type': 'normal'  # Todas las transacciones nuevas son de tipo normal
        }

        # 3. Firmar la transacción
        print("2. Firmando transacción...")
        signature = sign_transaction(private_key, transaction)
        transaction['signature'] = signature.hex()

        # 4. Añadir a la mempool
        print("3. Añadiendo a la mempool...")
        blockchain.add_to_mempool(transaction)
        
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
    """Endpoint para obtener la cadena completa"""
    try:
        if not blockchain.validate_chain():
            return jsonify({'message': 'The blockchain is invalid'}), 400
            
        response = {
            'chain': blockchain.chain,
            'length': len(blockchain.chain),
        }
        return jsonify(response), 200
        
    except Exception as e:
        print(f"Error al obtener la cadena: {str(e)}")
        return jsonify({'message': str(e)}), 500

@app.route('/generate_address', methods=['POST'])
def generate_address():
   """Genera una nueva dirección a partir de una clave pública existente"""
   try:
       values = request.get_json()
       if not values or 'public_key' not in values:
           return jsonify({'error': 'Missing public_key'}), 400

       public_key = values['public_key']
       
       # Genera una nueva dirección usando RIPEMD160(SHA256(public_key))
       # pero con un nonce adicional para generar diferentes direcciones
       nonce = secrets.token_bytes(4)  # 4 bytes de nonce aleatorio
       public_key_bytes = bytes.fromhex(public_key)
       combined = nonce + public_key_bytes
       
       # SHA256
       sha256_hash = hashlib.sha256(combined).digest()
       
       # RIPEMD160 
       address = hashlib.new('ripemd160', sha256_hash).hexdigest()
       
       # Actualiza las direcciones asociadas en blockchain
       if not hasattr(blockchain, 'wallet_addresses'):
           blockchain.wallet_addresses = {}
           
       for wallet_addr in blockchain.public_keys:
           if blockchain.public_keys[wallet_addr] == public_key:
               if wallet_addr not in blockchain.wallet_addresses:
                   blockchain.wallet_addresses[wallet_addr] = []
               blockchain.wallet_addresses[wallet_addr].append(address)
               # Inicializa balance para la nueva dirección
               blockchain.balances[address] = 0
               break

       return jsonify({'address': address}), 200
   except Exception as e:
       return jsonify({'error': str(e)}), 500

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

        if not encrypted_private_key or not password:
            return jsonify({'error': 'Missing encrypted_private_key or password'}), 400

        try:
            # Desencriptar la llave privada
            decrypted_private_key = decrypt_private_key(encrypted_private_key, password)
            
            # Generar la dirección a partir de la llave privada
            wallet_gen = WalletGenerator()
            public_key = wallet_gen.private_to_public(decrypted_private_key)
            address = wallet_gen.public_to_address(public_key)
            
            # Cargar en memoria si no existe
            if address not in blockchain.public_keys:
                blockchain.public_keys[address] = public_key
                # Si no existe el balance, inicializarlo
                if address not in blockchain.balances:
                    blockchain.balances[address] = 10

            return jsonify({
                'decrypted_private_key': decrypted_private_key,
                'address': address,
                'public_key': public_key,
                'balance': blockchain.balances[address]
            }), 200
            
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

@app.route('/verify_block', methods=['POST'])
def verify_block():
    print("\n====== INICIO DE VERIFICACIÓN DE BLOQUE ======")
    try:
        data = request.get_json()
        block_index = data.get('block_index')
        transaction_data = data.get('transaction')
        signature = data.get('signature')
        public_key = data.get('public_key')

        print(f"1. Datos recibidos:")
        print(f"   Índice del bloque: {block_index}")
        print(f"   Transacción a verificar: {json.dumps(transaction_data, indent=2)}")
        print(f"   Firma: {signature[:32]}..." if signature else "VALID")
        print(f"   Llave pública: {public_key[:32]}..." if public_key else "N/A")

        # Convertir valores numéricos
        transaction_data['amount'] = float(transaction_data['amount'])
        transaction_data['fee'] = float(transaction_data['fee'])

        # Obtener el bloque
        block = blockchain.chain[block_index]
        print(f"\n2. Bloque obtenido: #{block['index']}")
        print(f"   Total de transacciones en el bloque: {len(block['transactions'])}")

        # Determinar el tipo de transacción
        is_escrow_contract = transaction_data.get('sender') == 'escrow_contract'
        is_escrow_deposit = transaction_data.get('recipient') == 'escrow_contract'
        
        print("\n3. Buscando transacción coincidente...")
        # Lógica especial para verificar transacciones relacionadas con escrow
        if is_escrow_contract:
            # Para transacciones desde el contrato
            matching_transaction = next(
                (tx for tx in block['transactions'] if 
                 tx.get('type') == 'contract_transfer' and
                 tx['sender'] == 'escrow_contract' and 
                 tx['recipient'] == transaction_data['recipient'] and
                 abs(float(tx['amount']) - transaction_data['amount']) < 0.00001 and
                 (not tx.get('fee') or abs(float(tx.get('fee', 0)) - transaction_data['fee']) < 0.00001) and
                 tx.get('signature') == 'VALID'),
                None
            )
            
            if matching_transaction:
                print("\n4. Transacción del contrato encontrada y válida")
                return jsonify({'message': 'Válido'}), 200
            else:
                print("\n4. Transacción del contrato no encontrada o inválida")
                return jsonify({'message': 'Error'}), 400

        elif is_escrow_deposit:
            # Para transacciones hacia el contrato
            print("   Verificando depósito al escrow...")
            matching_transaction = next(
                (tx for tx in block['transactions'] if 
                 tx['sender'] == transaction_data['sender'] and 
                 tx['recipient'] == 'escrow_contract' and 
                 abs(float(tx['amount']) - transaction_data['amount']) < 0.00001 and
                 abs(float(tx.get('fee', 0)) - transaction_data['fee']) < 0.00001),
                None
            )
        else:
            # Para transacciones normales
            print("   Verificando transacción normal...")
            matching_transaction = next(
                (tx for tx in block['transactions'] if 
                 tx['sender'] == transaction_data['sender'] and 
                 tx['recipient'] == transaction_data['recipient'] and 
                 abs(float(tx['amount']) - transaction_data['amount']) < 0.00001 and
                 abs(float(tx.get('fee', 0)) - transaction_data['fee']) < 0.00001),
                None
            )

        if not matching_transaction:
            print("\nERROR: No se encontró una transacción coincidente")
            return jsonify({'message': 'Error'}), 400

        print("\n4. Transacción encontrada:", json.dumps(matching_transaction, indent=2))

        # Verificación de firma para transacciones normales y depósitos al escrow
        transaction_data['timestamp'] = matching_transaction['timestamp']
        transaction_data['type'] = matching_transaction.get('type', 'normal')

        print("\n5. Verificando firma...")
        print(f"   Datos a verificar: {json.dumps(transaction_data, indent=2)}")
        
        is_valid = verify_signature(public_key, transaction_data, signature)
        print(f"   Resultado de verificación: {'Válido' if is_valid else 'Inválido'}")

        if is_valid:
            print("\n====== FIN DE VERIFICACIÓN - ÉXITO ======")
            return jsonify({'message': 'Válido'}), 200
        else:
            print("\n====== FIN DE VERIFICACIÓN - FALLO ======")
            return jsonify({'message': 'Error'}), 400

    except Exception as e:
        print(f"\nERROR en verify_block: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'message': 'Error'}), 400

@app.route('/balance', methods=['GET'])
def get_balance():
    address = request.args.get('address')
    if not address:
        return jsonify({'message': 'Missing address parameter'}), 400
    
    print(f"Retrieving balance for {address}")
    balance = blockchain.get_balance(clean_public_key(address))
    return jsonify({'balance': balance}), 200

# def get_balance(self, address):
#    """Obtiene el balance total de una dirección incluyendo todas sus direcciones asociadas"""
#    total_balance = self.balances.get(address, 0)
   
#    # Si la dirección tiene direcciones adicionales asociadas, suma sus balances
#    if hasattr(self, 'wallet_addresses') and address in self.wallet_addresses:
#        for addr in self.wallet_addresses[address]:
#            total_balance += self.balances.get(addr, 0)
           
#    return total_balance
    
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
        required = ['agreement_id', 'buyer', 'reason']
        if not all(k in values for k in required):
            return jsonify({'error': 'Missing values'}), 400

        blockchain.escrow_contract.open_dispute(
            agreement_id=values['agreement_id'],
            buyer=values['buyer'],
            reason=values['reason']
        )

        return jsonify({'message': 'Disputa abierta y reembolso iniciado'}), 200

    except Exception as e:
        return jsonify({'error': str(e)}), 400

@app.route('/escrow/agreements/<wallet_address>', methods=['GET'])
def get_agreements(wallet_address):
    """Obtiene todos los acuerdos relacionados con una dirección"""
    try:
        active_agreements = []
        completed_agreements = []
        cancelled_agreements = []
        
        for agreement_id, agreement in blockchain.escrow_contract.state['agreements'].items():
            if agreement['buyer'] == wallet_address or agreement['seller'] == wallet_address:
                agreement_copy = agreement.copy()
                agreement_copy['id'] = agreement_id
                
                # Clasificar acuerdos según su estado
                if agreement['status'] == 'COMPLETED':
                    completed_agreements.append(agreement_copy)
                elif agreement['status'] == 'CANCELLED':
                    cancelled_agreements.append(agreement_copy)
                else:
                    active_agreements.append(agreement_copy)
                    
        # Ordenar cada lista por timestamp (más recientes primero)
        active_agreements.sort(key=lambda x: x['timestamp'], reverse=True)
        completed_agreements.sort(key=lambda x: x['timestamp'], reverse=True)
        cancelled_agreements.sort(key=lambda x: x['timestamp'], reverse=True)
        
        # Combinar las listas en el orden deseado
        all_agreements = active_agreements + completed_agreements + cancelled_agreements
        
        return jsonify({'agreements': all_agreements}), 200

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
    
@app.route('/settings/difficulty', methods=['GET'])
def get_difficulty():
    return jsonify({'difficulty': blockchain.mining_difficulty}), 200

@app.route('/settings/difficulty', methods=['POST'])
def set_difficulty():
    try:
        data = request.get_json()
        difficulty = data.get('difficulty')
        
        if difficulty is None or not isinstance(difficulty, int) or difficulty < 0 or difficulty > 4:
            return jsonify({'error': 'Invalid difficulty value'}), 400
            
        print(f"Actualizando dificultad de minado a {difficulty} ceros")
        blockchain.mining_difficulty = difficulty
        return jsonify({'message': 'Difficulty updated successfully'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)