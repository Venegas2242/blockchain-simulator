import hashlib
import json
from time import time
import threading
from secure_escrow_contract import SecureEscrowContract
from crypto_utils import verify_signature, sign_transaction

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
        self.wallet_addresses = {}  # Almacena direcciones adicionales por wallet
        
        self.mining_stopped = False
        self.mining_lock = threading.Lock()  # Agregar un lock para sincronización
        self.current_mining_progress = {
            'status': 'not_started',
            'nonce': 0,
            'hash': '',
            'found': False,
            'final_nonce': None,
            'final_hash': None
        }
        
        # Inicializar smart contract
        self.escrow_contract = SecureEscrowContract(self)
        self.balances[self.escrow_contract.address] = 1000 # Inicializar balance del contrato
        self.balances['mediator'] = 0 # Inicializar cuenta del mediador

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
        # Añadir bloque génesis
        self.chain.append(genesis_block)

    def stop_mining(self):
        """Detiene el proceso de minado actual"""
        self.mining_stopped = True

    def reset_mining_state(self):
        """Reinicia el estado de minado"""
        self.mining_stopped = False
        self.current_mining_progress = {
            'status': 'not_started',
            'nonce': 0,
            'hash': '',
            'found': False,
            'final_nonce': None,
            'final_hash': None
        }

    def calculate_hash(self, block):
        """Calcula el hash del bloque con prueba de trabajo y emite el progreso"""
        try:
            nonce = 0
            block_copy = block.copy()
            block_copy.pop('hash', None)  # Eliminar el hash si existe
            
            is_genesis = block.get('index') == 1
            
            if not is_genesis:
                print(f"\nBuscando nonce para bloque #{block['index']}")
                self.current_mining_progress = {
                    'status': 'mining',
                    'nonce': 0,
                    'hash': '',
                    'found': False,
                    'final_nonce': None,
                    'final_hash': None
                }
            
            while not self.mining_stopped:
                block_copy['nonce'] = nonce
                block_string = json.dumps(block_copy, sort_keys=True).encode()
                hash_result = hashlib.sha256(block_string).hexdigest()
                
                if not is_genesis:
                    self.current_mining_progress.update({
                        'status': 'mining',
                        'nonce': nonce,
                        'hash': hash_result,
                        'found': hash_result.startswith('0000')
                    })
                    
                    if nonce % 100 == 0:
                        print(f"\rNonce actual: {nonce}, Hash actual: {hash_result}", end="")
                
                if hash_result.startswith('0000'):
                    if not is_genesis:
                        print(f"\n¡Hash válido encontrado!")
                        print(f"Nonce final: {nonce}")
                        print(f"Hash final: {hash_result}")
                        
                        self.current_mining_progress.update({
                            'status': 'completed',
                            'nonce': nonce,
                            'hash': hash_result,
                            'found': True,
                            'final_nonce': nonce,
                            'final_hash': hash_result
                        })
                    return nonce, hash_result
                
                nonce += 1
                
                if nonce > 1000000:  # Añadir un límite máximo para evitar bucles infinitos
                    raise ValueError("No se encontró un hash válido después de 1,000,000 intentos")
            
            if self.mining_stopped:
                print("\nMinado detenido manualmente")
                raise ValueError("Minado detenido manualmente")
                
        except Exception as e:
            print(f"\nError durante el cálculo del hash: {str(e)}")
            self.current_mining_progress.update({
                'status': 'error',
                'error': str(e)
            })
            raise

    def get_mining_progress(self):
        """Retorna el progreso actual del minado"""
        if hasattr(self, 'current_mining_progress'):
            return self.current_mining_progress
        return {
            'status': 'not_started',
            'nonce': 0,
            'hash': '',
            'found': False,
            'final_nonce': None,
            'final_hash': None
        }
            
    def sign_transaction(self, private_key, transaction):
        """
        Wrapper para firmar una transacción usando la utilidad criptográfica.
        
        Args:
            private_key (str): Llave privada en formato hexadecimal
            transaction (dict): Transacción a firmar
            
        Returns:
            bytes: Firma de la transacción
        """
        return sign_transaction(private_key, transaction)

    def validate_chain(self):
        """Valida la cadena completa"""
        if len(self.chain) == 1:
            return True

        for i, block in enumerate(self.chain):
            if block['index'] > 1 and not self.verify_block(block):
                print(f"Bloque {block['index']} falló en verify_block")
                return False
            
            # Verificar el hash del bloque sin usar calculate_hash
            block_copy = block.copy()
            block_copy.pop('hash', None)
            block_string = json.dumps(block_copy, sort_keys=True).encode()
            calculated_hash = hashlib.sha256(block_string).hexdigest()
            
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
        
        return True

    def verify_block_hash(self, block):
        """Verifica el hash de un bloque sin prueba de trabajo"""
        block_copy = block.copy()
        block_copy.pop('hash', None)
        block_string = json.dumps(block_copy, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()
    
    def verify_block(self, block):
        """Verifica todas las transacciones en un bloque"""
        try:
            # Verificar si es el bloque génesis
            if block['index'] == 1:
                print("Bloque génesis - válido")
                return True

            print(f"\nVerificando bloque {block['index']}:")
            
            # Verificar campos requeridos
            required_fields = ['index', 'timestamp', 'transactions', 'previous_hash', 'merkle_root', 'nonce', 'hash']
            for field in required_fields:
                if field not in block:
                    print(f"Error: Falta el campo {field} en el bloque")
                    return False

            # Verificar que haya transacciones
            if not block['transactions']:
                print("Error: No hay transacciones en el bloque")
                return False
                
            # Verificar que la primera transacción sea coinbase
            if block['transactions'][0].get('type') != 'coinbase':
                print("Error: Primera transacción no es coinbase")
                return False

            # Verificar las transacciones (excluyendo la coinbase)
            for i, transaction in enumerate(block['transactions'][1:], 1):
                # Verificar transacciones del contrato
                if transaction.get('type') == 'contract_transfer':
                    # Verificar campos requeridos
                    contract_fields = ['sender', 'recipient', 'amount', 'timestamp', 'signature']
                    if not all(field in transaction for field in contract_fields):
                        print(f"Error: Faltan campos en la transacción del contrato")
                        return False
                    
                    # Verificar que el remitente sea el contrato
                    if transaction['sender'] != self.escrow_contract.address:
                        print(f"Error: Remitente inválido para transacción del contrato")
                        return False
                    
                    # Verificar que el destinatario sea válido
                    recipient = transaction['recipient']
                    if recipient != 'mediator' and recipient not in self.balances:
                        print(f"Error: Destinatario inválido para transacción del contrato")
                        return False
                    
                    # Verificar firma del contrato
                    if transaction['signature'] != 'VALID':
                        print(f"Error: Firma inválida para transacción del contrato")
                        return False
                    
                    continue
                
                # Verificar transacciones normales
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
            
            # Verificar Merkle Root
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
        
        print(f"\nProcesando transacción:")
        print(f"De: {transaction['sender']}")
        print(f"Para: {transaction['recipient']}")
        print(f"Cantidad: {transaction['amount']} BBC")
        print(f"Comisión: {transaction.get('fee', 0)} BBC")
        print(f"Tipo: {transaction.get('type', 'normal')}")
        
        if transaction.get('type') != 'coinbase':
            sender = transaction['sender']
            recipient = transaction['recipient']
            amount = transaction['amount']
            fee = transaction.get('fee', 0)
            tx_type = transaction.get('type', 'normal')

            
            print(f"Balance del remitente antes: {self.get_balance(sender)} BBC")
            print(f"Balance del destinatario antes: {self.get_balance(recipient)} BBC")
            
            # Verificar balance suficiente
            if self.get_balance(sender) < amount + fee:
                raise ValueError(f"Balance insuficiente para {sender}")
            
            # Actualizar balances
            # Para transacciones de depósito al escrow, asegurarse de restar del balance del comprador
            if tx_type == 'escrow_deposit':
                print("Procesando depósito al escrow...")
                # Restar fondos al comprador (incluyendo todas las comisiones)
                self.balances[sender] = self.get_balance(sender) - (amount + fee)
                # Añadir fondos al contrato
                self.balances[recipient] = self.get_balance(recipient) + amount
                print(f"Fondos restados del comprador: {amount + fee} BBC")
            else:
                # Procesamiento normal para otras transacciones
                self.balances[sender] = self.get_balance(sender) - (amount + fee)
                self.balances[recipient] = self.get_balance(recipient) + amount

            
            print(f"Balance del remitente después: {self.get_balance(sender)} BBC")
            print(f"Balance del destinatario después: {self.get_balance(recipient)} BBC")

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

    def calculate_hash(self, block):
        """Calcula el hash del bloque con prueba de trabajo y emite el progreso"""
        try:
            nonce = 0
            block_copy = block.copy()
            block_copy.pop('hash', None)  # Eliminar el hash si existe
            
            is_genesis = block.get('index') == 1
            
            if not is_genesis:
                print(f"\nBuscando nonce para bloque #{block['index']}")
                self.current_mining_progress = {
                    'status': 'mining',
                    'nonce': 0,
                    'hash': '',
                    'found': False,
                    'final_nonce': None,
                    'final_hash': None
                }
            
            while not self.mining_stopped:
                block_copy['nonce'] = nonce
                block_string = json.dumps(block_copy, sort_keys=True).encode()
                hash_result = hashlib.sha256(block_string).hexdigest()
                
                if not is_genesis:
                    self.current_mining_progress.update({
                        'status': 'mining',
                        'nonce': nonce,
                        'hash': hash_result,
                        'found': hash_result.startswith('0000')
                    })
                    
                    if nonce % 100 == 0:
                        print(f"\rNonce actual: {nonce}, Hash actual: {hash_result}", end="")
                
                if hash_result.startswith('0000'):
                    if not is_genesis:
                        print(f"\n¡Hash válido encontrado!")
                        print(f"Nonce final: {nonce}")
                        print(f"Hash final: {hash_result}")
                        
                        self.current_mining_progress.update({
                            'status': 'completed',
                            'nonce': nonce,
                            'hash': hash_result,
                            'found': True,
                            'final_nonce': nonce,
                            'final_hash': hash_result
                        })
                    return nonce, hash_result
                
                nonce += 1
                
                if nonce > 1000000:  # Añadir un límite máximo para evitar bucles infinitos
                    raise ValueError("No se encontró un hash válido después de 1,000,000 intentos")
            
            if self.mining_stopped:
                print("\nMinado detenido manualmente")
                raise ValueError("Minado detenido manualmente")
                
        except Exception as e:
            print(f"\nError durante el cálculo del hash: {str(e)}")
            self.current_mining_progress.update({
                'status': 'error',
                'error': str(e)
            })
            raise

    def get_balance(self, address):
        """Obtiene el balance total de una dirección incluyendo todas sus direcciones asociadas"""
        # Primero verificar si la dirección es una dirección principal
        total_balance = self.balances.get(address, 0)
        
        # Luego buscar en todas las wallets y sus direcciones asociadas
        for wallet_addr, addresses in self.wallet_addresses.items():
            if wallet_addr == address:  # Si es la dirección principal
                # Sumar los balances de todas sus direcciones asociadas
                for addr in addresses:
                    total_balance += self.balances.get(addr, 0)
            elif address in addresses:  # Si es una dirección asociada
                # Devolver el balance específico de esa dirección
                return self.balances.get(address, 0)
                    
        return total_balance                                         

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
    
    def add_to_mempool(self, transaction):
        """
        Añade una transacción a la mempool verificando el balance disponible
        """
        if not self.verify_transaction(transaction):
            raise ValueError("Invalid transaction")
        
        sender = transaction['sender']
        total_amount = transaction['amount'] + transaction['fee']
        
        # Verificar balance disponible considerando transacciones pendientes
        available_balance = self.get_available_balance(sender)
        print(f"\nVerificando balance para nueva transacción:")
        print(f"Remitente: {sender}")
        print(f"Balance disponible: {available_balance} BBC")
        print(f"Cantidad total requerida: {total_amount} BBC")        
        
        if available_balance < total_amount:
            raise ValueError(f"Insufficient funds. Available: {available_balance}, Required: {total_amount}")

        self.mempool.append(transaction)
        return True

    def get_available_balance(self, address):
        """
        Obtiene el balance disponible considerando tanto el balance actual
        como las transacciones pendientes en mempool
        """
        # Obtener balance actual
        current_balance = self.get_balance(address)
        
        # Calcular cantidad comprometida en mempool
        pending_amount = 0
        for tx in self.mempool:
            if tx['sender'] == address:
                pending_amount += tx['amount'] + tx['fee']
        
        # Balance disponible = balance actual - cantidad comprometida
        available_balance = current_balance - pending_amount
        print(f"\nCalculando balance disponible para {address}:")
        print(f"Balance actual: {current_balance}")
        print(f"Cantidad comprometida en mempool: {pending_amount}")
        print(f"Balance disponible: {available_balance}")
        
        return available_balance

    def verify_transaction(self, transaction):
        # Si la transacción es de tipo 'coinbase' no necesita verificación
        if transaction['sender'] == "0":
            return True

        # Verificar que la transacción tenga una firma
        if 'signature' not in transaction:
            return False

        # Obtener la clave pública del remitente
        public_key = self.public_keys.get(transaction['sender'])
        if not public_key:
            return False

        # Hacer una copia de la transacción y eliminar el campo 'signature'
        transaction_copy = transaction.copy()
        signature = transaction_copy.pop('signature')

        # Verificar la firma utilizando los datos de la transacción (sin la firma)
        return verify_signature(public_key, transaction_copy, signature)
    
    def mine(self, miner_address: str, selected_transactions=None):
        print("\nIniciando proceso de minado...")
        self.mining_stopped = False  # Reset mining flag
        
        transactions = []
        total_fees = 0
        
        try:
            if selected_transactions and self.mempool:
                print(f"Procesando {len(selected_transactions)} transacciones seleccionadas...")
                print(f"Estado actual de la mempool: {self.mempool}")
                
                temp_mempool = self.mempool.copy()
                selected_txs = []
                
                for tx_index in selected_transactions:
                    if 0 <= tx_index < len(temp_mempool):
                        tx = temp_mempool[tx_index]
                        print(f"Procesando transacción {tx_index}: {tx}")
                        selected_txs.append(tx)
                        if 'fee' in tx:
                            total_fees += tx['fee']
                    else:
                        print(f"Error: índice {tx_index} fuera de rango")
                
                # Remover transacciones seleccionadas de mempool
                for tx in selected_txs:
                    if tx in self.mempool:
                        self.mempool.remove(tx)
                        print(f"Transacción removida de mempool: {tx}")
                
                transactions.extend(selected_txs)

            print(f"Total de comisiones: {total_fees}")
            print("Creando nuevo bloque...")
            
            block_reward = self.calculate_block_reward()
            total_reward = block_reward + total_fees
            print(f"Recompensa total: {total_reward} (base: {block_reward}, comisiones: {total_fees})")

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
            with self.mining_lock:
                try:
                    block['nonce'], block['hash'] = self.calculate_hash(block)
                    print(f"\nHash encontrado: {block['hash']}")
                    
                    if not self.mining_stopped:
                        print("\nProcesando transacciones...")
                        for tx in transactions[1:]:
                            print(f"Procesando transacción: {tx}")
                            self.process_transaction(tx)
                        
                        print(f"\nActualizando balance del minero {miner_address}")
                        print(f"Balance anterior: {self.get_balance(miner_address)}")
                        self.balances[miner_address] = self.get_balance(miner_address) + total_reward
                        print(f"Balance actualizado: {self.get_balance(miner_address)}")
                        
                        print("\nVerificando bloque antes de añadirlo...")
                        if not self.verify_block(block):
                            raise ValueError("Bloque inválido")
                        
                        print("Añadiendo bloque a la cadena...")
                        self.chain.append(block)
                        print("Minado completado exitosamente!")
                        return block
                    
                except Exception as e:
                    print(f"Error durante el minado: {str(e)}")
                    raise
                
        except Exception as e:
            print(f"Error durante el minado: {str(e)}")
            raise
        finally:
            self.mining_stopped = True
