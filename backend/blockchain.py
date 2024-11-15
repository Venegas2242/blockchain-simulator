import hashlib
import json
from time import time
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import math

def verify_signature(public_key, transaction, signature):
    """Verifica la firma de la transacción usando la clave pública"""
    vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    transaction_string = json.dumps(transaction, sort_keys=True)
    try:
        vk.verify(bytes.fromhex(signature), transaction_string.encode())
        return True
    except:
        return False

class SecureEscrowContract:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.address = "escrow_contract"  # Dirección fija del contrato
        self.state = {
            'locked_funds': {},    # Fondos bloqueados
            'agreements': {},      # Detalles de acuerdos
            'disputes': {},        # Disputas activas
            'confirmations': {}    # Confirmaciones de ambas partes
        }
        
        # Configuración del contrato
        self.TIMEOUT_BLOCKS = 10        # Bloques antes de timeout
        self.DISPUTE_BLOCKS = 5         # Bloques para resolver disputa
        self.MEDIATOR_FEE = 0.01        # 1% para el mediador
        self.INITIAL_MINING_FEE = 0.001  # 0.1% para el minero en la transacción inicial
        self.RELEASE_MINING_FEE = 0.001  # 0.1% para el minero en cada liberación de fondos
        self.address = "escrow_contract"  # Dirección del contrato para recibir fondos

    def create_agreement(self, agreement_id: str, buyer: str, seller: str, amount: float, description: str, buyer_private_key: str):
        """Crea un nuevo acuerdo donde el comprador paga todas las comisiones"""
        
        # Calcular todas las comisiones
        mediator_fee = amount * self.MEDIATOR_FEE           # Comisión para el mediador
        initial_mining_fee = amount * self.INITIAL_MINING_FEE  # Comisión para el minero inicial
        release_fees = self.RELEASE_MINING_FEE * 2          # Comisiones para las dos transacciones finales
        
        # Total que debe pagar el comprador
        total_amount = amount + mediator_fee + initial_mining_fee + release_fees
        
        # Verificar fondos suficientes
        if self.blockchain.get_balance(buyer) < total_amount:
            raise ValueError(f"""Fondos insuficientes. Se requiere {total_amount} BBC:
                             - Monto principal: {amount} BBC
                             - Comisión mediador: {mediator_fee} BBC
                             - Comisión minero inicial: {initial_mining_fee} BBC
                             - Comisiones minero finales: {release_fees} BBC""")
        
        # Crear la transacción de transferencia de fondos
        transfer_transaction = {
            'sender': buyer,
            'recipient': self.address,
            'amount': amount + mediator_fee + release_fees,  # Incluye fondos para comisiones futuras
            'fee': initial_mining_fee,                       # Comisión para el minero actual
            'timestamp': time()
        }

        # Firmar la transacción
        signature = self.blockchain.sign_transaction(buyer_private_key, transfer_transaction)
        transfer_transaction['signature'] = signature.hex()

        # Añadir a la mempool
        self.blockchain.mempool.append(transfer_transaction)

        # Actualizar estado del contrato
        current_block = len(self.blockchain.chain)
        self.state['agreements'][agreement_id] = {
            'buyer': buyer,
            'seller': seller,
            'amount': amount,
            'mediator_fee': mediator_fee,
            'reserved_mining_fees': release_fees,  # Guardar las comisiones reservadas
            'description': description,
            'status': 'PENDING_SELLER_CONFIRMATION',
            'created_at_block': current_block,
            'timeout_block': current_block + self.TIMEOUT_BLOCKS,
            'shipped': False,
            'delivery_confirmed': False,
            'timestamp': time()
        }
        
        return agreement_id

    def confirm_seller_participation(self, agreement_id: str, seller: str):
        """Confirmación del vendedor para participar en el acuerdo"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['seller'] != seller:
            raise ValueError("Solo el vendedor puede confirmar participación")
            
        if agreement['status'] != 'PENDING_SELLER_CONFIRMATION':
            raise ValueError("Estado inválido para confirmar participación")
            
        # Actualizar estado
        agreement['status'] = 'AWAITING_SHIPMENT'
        return True

    def process_escrow_transaction(self, transaction):
        """Procesa una transacción de escrow cuando es minada"""
        # Solo procesar si es una transacción del smart contract
        if transaction.get('sender') == self.address or transaction.get('recipient') == self.address:
            # Actualizar balances según sea necesario
            if transaction['recipient'] == self.address:
                # Fondos recibidos por el contrato
                if transaction['sender'] not in self.state['locked_funds']:
                    self.state['locked_funds'][transaction['sender']] = 0
                self.state['locked_funds'][transaction['sender']] += transaction['amount'] + transaction.get('fee', 0)
            
            elif transaction['sender'] == self.address:
                # Fondos liberados por el contrato
                for agreement in self.state['agreements'].values():
                    if agreement['seller'] == transaction['recipient']:
                        buyer = agreement['buyer']
                        if buyer in self.state['locked_funds']:
                            self.state['locked_funds'][buyer] -= transaction['amount']
                            if self.state['locked_funds'][buyer] <= 0:
                                del self.state['locked_funds'][buyer]
            
    def confirm_delivery(self, agreement_id: str, buyer: str):
        """Confirma la entrega y libera los fondos incluyendo las comisiones pre-pagadas"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['buyer'] != buyer:
            raise ValueError("Solo el comprador puede confirmar entrega")
        
        current_time = time()
        mining_fee = self.RELEASE_MINING_FEE  # Usar comisión pre-pagada

        # Transacción principal al vendedor (monto completo)
        transfer_to_seller = {
            'sender': self.address,
            'recipient': agreement['seller'],
            'amount': agreement['amount'],
            'fee': mining_fee,  # Usando comisión pre-pagada
            'timestamp': current_time,
            'type': 'contract_transfer',
            'signature': 'VALID'
        }

        # Transacción de comisión al mediador (monto completo)
        mediator_fee_transaction = {
            'sender': self.address,
            'recipient': 'mediator',
            'amount': agreement['mediator_fee'],
            'fee': mining_fee,  # Usando comisión pre-pagada
            'timestamp': current_time,
            'type': 'contract_transfer',
            'signature': 'VALID'
        }

        # Añadir a la mempool
        self.blockchain.mempool.append(transfer_to_seller)
        self.blockchain.mempool.append(mediator_fee_transaction)
        
        # Actualizar estado
        agreement['status'] = 'COMPLETED'
        agreement['delivery_confirmed'] = True
        
        return True
            
    def check_timeouts(self):
        """Verifica timeouts y ejecuta acciones automáticas"""
        current_block = len(self.blockchain.chain)
        
        for agreement_id, agreement in list(self.state['agreements'].items()):
            # Si pasó el timeout y no hay disputa abierta
            if (current_block > agreement['timeout_block'] and 
                agreement['status'] not in ['COMPLETED', 'RESOLVED', 'DISPUTED']):
                
                # Reembolso automático al comprador
                buyer = agreement['buyer']
                amount = agreement['amount']
                mediator_fee = agreement['mediator_fee']
                
                # Desbloquear fondos y devolver al comprador
                if buyer in self.state['locked_funds']:
                    self.state['locked_funds'][buyer] -= (amount + mediator_fee)
                    if self.state['locked_funds'][buyer] <= 0:
                        del self.state['locked_funds'][buyer]
                
                self.blockchain.balances[buyer] += (amount + mediator_fee)
                agreement['status'] = 'REFUNDED'
                print(f"Acuerdo {agreement_id} reembolsado por timeout")
                
            # Si hay disputa abierta que expiró
            if agreement_id in self.state['disputes']:
                dispute = self.state['disputes'][agreement_id]
                if (current_block > dispute.get('resolution_block', 0) and 
                    dispute.get('status') == 'OPEN'):
                    # Reembolso automático por disputa no resuelta
                    buyer = agreement['buyer']
                    amount = agreement['amount']
                    mediator_fee = agreement['mediator_fee']
                    
                    # Desbloquear fondos y devolver al comprador
                    if buyer in self.state['locked_funds']:
                        self.state['locked_funds'][buyer] -= (amount + mediator_fee)
                        if self.state['locked_funds'][buyer] <= 0:
                            del self.state['locked_funds'][buyer]
                    
                    self.blockchain.balances[buyer] += (amount + mediator_fee)
                    agreement['status'] = 'REFUNDED'
                    dispute['status'] = 'EXPIRED'
                    print(f"Acuerdo {agreement_id} reembolsado por disputa expirada")
                    
    def confirm_shipment(self, agreement_id: str, seller: str, tracking_info: str = None):
        """
        Confirma el envío del producto por parte del vendedor
        
        Args:
            agreement_id (str): ID del acuerdo
            seller (str): Dirección del vendedor
            tracking_info (str, optional): Información de seguimiento del envío
        
        Returns:
            bool: True si se confirmó exitosamente
        """
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['seller'] != seller:
            raise ValueError("Solo el vendedor puede confirmar envío")
            
        if agreement['status'] != 'AWAITING_SHIPMENT':
            raise ValueError("Estado inválido para confirmar envío")
            
        # Actualizar directamente el estado sin crear transacción
        agreement['shipped'] = True
        agreement['tracking_info'] = tracking_info
        agreement['status'] = 'SHIPPED'
        agreement['shipping_timestamp'] = time()
        
        return True

class Blockchain:
    def __init__(self):
        self.chain = []
        self.mempool = []
        self.nodes = set()
        self.balances = {}  # Initialize empty balances
        self.public_keys = {}  # Initialize empty public keys
        self.last_block_hash = '1'
        self.block_reward = 10
        self.halving_blocks = 2
        
        # Inicializar smart contract
        self.escrow_contract = SecureEscrowContract(self)
        
        # Inicializar balance del contrato
        self.balances[self.escrow_contract.address] = 0

        # Crear bloque génesis
        genesis_block = {
            'index': 1,
            'timestamp': time(),
            'transactions': [],
            'previous_hash': self.last_block_hash,
            'nonce': 0,
            'hash': None,
            'merkle_root': self.calculate_merkle_root([])
        }
        
        # Calcular hash para el bloque génesis
        genesis_block['nonce'], genesis_block['hash'] = self.calculate_hash(genesis_block)
        self.last_block_hash = genesis_block['hash']
        
        # Inicializar cuenta del mediador
        self.balances['mediator'] = 0
        
        # Añadir bloque génesis
        self.chain.append(genesis_block)

    def calculate_hash(self, block):
        """Calcula el hash del bloque con prueba de trabajo"""
        nonce = 0
        block_copy = block.copy()
        block_copy.pop('hash', None)
        
        while True:
            block_copy['nonce'] = nonce
            block_string = json.dumps(block_copy, sort_keys=True).encode()
            hash_result = hashlib.sha256(block_string).hexdigest()
            
            if hash_result.startswith('0000'):  # Dificultad fija de 4 ceros
                return nonce, hash_result
            
            nonce += 1
            
    def sign_transaction(self, private_key, transaction):
        """
        Firma una transacción usando la llave privada proporcionada.
        
        Args:
            private_key (str): Llave privada en formato hexadecimal
            transaction (dict): Transacción a firmar
            
        Returns:
            bytes: Firma de la transacción
        """
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

    def validate_chain(self):
        """Valida la cadena completa"""
        if len(self.chain) == 1:
            print("Solo bloque génesis - válido")
            return True

        for i, block in enumerate(self.chain):
            print(f"Verificando bloque {block['index']}")
            
            if block['index'] > 1 and not self.verify_block(block):
                print(f"Bloque {block['index']} falló en verify_block")
                return False
            
            block_copy = block.copy()
            block_copy.pop('hash', None)
            block_copy.pop('nonce', None)
            _, calculated_hash = self.calculate_hash(block_copy)
            
            if block['hash'] != calculated_hash:
                print(f"Hash incorrecto en bloque {block['index']}")
                print(f"Hash esperado: {calculated_hash}")
                print(f"Hash actual: {block['hash']}")
                return False

            if i > 0:
                previous_block = self.chain[i - 1]
                if block['previous_hash'] != previous_block['hash']:
                    print(f"Previous hash incorrecto en bloque {block['index']}")
                    print(f"Hash esperado: {previous_block['hash']}")
                    print(f"Hash actual: {block['previous_hash']}")
                    return False
        
        print("Cadena válida")
        return True

    def verify_block(self, block):
        """Verifica todas las transacciones en un bloque"""
        try:
            if block['index'] == 1:
                print("Bloque génesis - válido")
                return True

            print(f"\nVerificando bloque {block['index']}:")
            
            required_fields = ['index', 'timestamp', 'transactions', 'previous_hash', 'merkle_root', 'nonce', 'hash']
            for field in required_fields:
                if field not in block:
                    print(f"Error: Falta el campo {field} en el bloque")
                    return False

            if not block['transactions']:
                print("Error: No hay transacciones en el bloque")
                return False
                
            if block['transactions'][0].get('type') != 'coinbase':
                print("Error: Primera transacción no es coinbase")
                return False

            print("Verificando transacciones...")
            for i, transaction in enumerate(block['transactions'][1:], 1):
                print(f"Verificando transacción {i}: {transaction.get('type', 'normal')}")
                
                # Verificación especial para transacciones del contrato
                if transaction.get('type') == 'contract_transfer':
                    print(f"Verificando transacción del contrato {i}")
                    
                    # Verificar campos requeridos para transacción del contrato
                    contract_fields = ['sender', 'recipient', 'amount', 'timestamp', 'signature']
                    if not all(field in transaction for field in contract_fields):
                        print(f"Error: Faltan campos en la transacción del contrato")
                        return False
                    
                    # Verificar que el remitente sea el contrato
                    if transaction['sender'] != self.escrow_contract.address:
                        print(f"Error: Remitente inválido para transacción del contrato")
                        return False
                    
                    # Verificar que el destinatario sea válido (vendedor o mediador)
                    recipient = transaction['recipient']
                    if recipient != 'mediator' and recipient not in self.balances:
                        print(f"Error: Destinatario inválido para transacción del contrato")
                        return False
                    
                    # Verificar la firma especial del contrato
                    if transaction['signature'] != 'VALID':
                        print(f"Error: Firma inválida para transacción del contrato")
                        return False
                    
                    continue
                
                # Verificación normal para otras transacciones
                if 'signature' not in transaction:
                    print(f"Error: Transacción {i} no tiene firma")
                    return False

                sender = transaction['sender']
                if sender not in self.public_keys:
                    print(f"Error: Clave pública no encontrada para {sender}")
                    return False

                transaction_copy = transaction.copy()
                signature = transaction_copy.pop('signature')
                
                if not verify_signature(self.public_keys[sender], transaction_copy, signature):
                    print(f"Error: Firma inválida en transacción {i}")
                    return False
            
            calculated_merkle = self.calculate_merkle_root(block['transactions'])
            if calculated_merkle != block['merkle_root']:
                print("Error: Merkle root no coincide")
                return False
                
            print("Verificación exitosa!")
            return True
            
        except Exception as e:
            print(f"Error durante la verificación del bloque: {str(e)}")
            return False

    def process_transaction(self, transaction):
        """Procesa una transacción actualizando los balances"""
        if transaction.get('type') != 'coinbase':
            sender = transaction['sender']
            recipient = transaction['recipient']
            amount = transaction['amount']
            fee = transaction.get('fee', 0)
            
            # Verificar balance suficiente
            if self.get_balance(sender) < amount + fee:
                raise ValueError(f"Balance insuficiente para {sender}")
            
            # Actualizar balances
            self.balances[sender] = self.get_balance(sender) - (amount + fee)
            self.balances[recipient] = self.get_balance(recipient) + amount

            # Si es una transacción al contrato de custodia, actualizar los fondos bloqueados
            if recipient == self.escrow_contract.address:
                print(f"Fondos recibidos en contrato: {amount} BBC")
                # Asegurarse de que el contrato tenga una entrada en balances
                if self.escrow_contract.address not in self.balances:
                    self.balances[self.escrow_contract.address] = 0
                # Actualizar el balance del contrato
                self.balances[self.escrow_contract.address] += amount

            # Si es una transacción desde el contrato, verificar que tenga los fondos
            if sender == self.escrow_contract.address:
                if self.escrow_contract.address not in self.balances:
                    raise ValueError("El contrato no tiene balance inicializado")
                if self.get_balance(self.escrow_contract.address) < amount:
                    raise ValueError(f"Balance insuficiente en el contrato: {self.get_balance(self.escrow_contract.address)} BBC")

    def mine(self, miner_address: str, selected_transactions=None):
        """Mina un nuevo bloque"""
        try:
            print("\nIniciando proceso de minado...")
            
            transactions = []
            total_fees = 0
            
            print("Verificando timeouts de contratos...")
            self.escrow_contract.check_timeouts()
            
            if selected_transactions and self.mempool:
                print(f"Procesando {len(selected_transactions)} transacciones seleccionadas...")
                selected_transactions = selected_transactions[:3]
                
                temp_mempool = self.mempool.copy()
                selected_txs = []
                
                for tx_index in selected_transactions:
                    if 0 <= tx_index < len(temp_mempool):
                        tx = temp_mempool[tx_index]
                        print(f"Procesando transacción: {tx.get('type', 'normal')}")
                        selected_txs.append(tx)
                        if 'fee' in tx:
                            total_fees += tx['fee']
                
                # Remover transacciones seleccionadas de mempool
                for tx in selected_txs:
                    self.mempool.remove(tx)
                
                transactions.extend(selected_txs)

            print("Creando nuevo bloque...")
            block_reward = self.calculate_block_reward()
            total_reward = block_reward + total_fees

            # Crear transacción coinbase
            coinbase_transaction = {
                'sender': "0",
                'recipient': miner_address,
                'amount': total_reward,
                'type': 'coinbase'
            }
            transactions.insert(0, coinbase_transaction)
            
            block = {
                'index': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': transactions,
                'previous_hash': self.last_block['hash'],
                'merkle_root': self.calculate_merkle_root(transactions),
                'nonce': None,
                'hash': None
            }
            
            print("Calculando proof of work...")
            block['nonce'], block['hash'] = self.calculate_hash(block)

            print("Procesando transacciones...")
            for tx in transactions[1:]:  # Procesar todas excepto la coinbase
                if tx.get('type') and tx['type'].startswith('escrow_'):
                    print(f"Procesando transacción de escrow: {tx['type']}")
                    self.escrow_contract.process_escrow_transaction(tx)
                else:
                    print("Procesando transacción normal")
                    self.process_transaction(tx)

            print("Actualizando balance del minero...")
            self.balances[miner_address] = self.get_balance(miner_address) + total_reward

            print("Verificando bloque antes de añadirlo...")
            if not self.verify_block(block):
                raise ValueError("Bloque inválido")
            
            print("Añadiendo bloque a la cadena...")
            self.chain.append(block)
            
            print("Minado completado exitosamente!")
            return block
            
        except Exception as e:
            print(f"Error durante el minado: {str(e)}")
            raise

    def get_balance(self, address):
        """Obtiene el balance de una dirección"""
        return self.balances.get(address, 0)

    def calculate_block_reward(self):
        """Calcula la recompensa actual por bloque basada en halvings"""
        halvings = (len(self.chain) - 1) // self.halving_blocks
        return self.block_reward / (2 ** halvings)

    def get_mempool(self):
        """Retorna las transacciones pendientes en la mempool"""
        return sorted(self.mempool, key=lambda x: x.get('fee', 0), reverse=True)

    def calculate_merkle_root(self, transactions):
        """Calcula el Merkle Root de las transacciones"""
        if not transactions:
            return hashlib.sha256(''.encode()).hexdigest()
        
        tx_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                    for tx in transactions]
        
        if len(tx_hashes) % 2 == 1:
            tx_hashes.append(tx_hashes[-1])
        
        while len(tx_hashes) > 1:
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i+1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            tx_hashes = new_hashes
        
        return tx_hashes[0]

    @property
    def last_block(self):
        """Retorna el último bloque de la cadena"""
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """Crea un hash SHA-256 de un bloque"""
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()