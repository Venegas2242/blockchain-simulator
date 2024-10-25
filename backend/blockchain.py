import hashlib
import json
from time import time
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import math

def verify_signature(public_key, transaction, signature):
    vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
    transaction_string = json.dumps(transaction, sort_keys=True)
    try:
        vk.verify(bytes.fromhex(signature), transaction_string.encode())
        return True
    except:
        return False

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
        
        # Crear bloque génesis
        genesis_block = {
            'index': 1,
            'timestamp': time(),
            'transactions': [],
            'previous_hash': self.last_block_hash,
            'nonce': 0,
            'hash': None
        }
        
        # Calcular hash para el bloque génesis
        genesis_block['nonce'], genesis_block['hash'] = self.calculate_hash(genesis_block)
        self.last_block_hash = genesis_block['hash']
        
        # Añadir bloque génesis
        self.chain.append(genesis_block)

    def calculate_hash(self, block):
        """
        Calcula el hash del bloque con prueba de trabajo
        """
        nonce = 0
        block_copy = block.copy()
        # Asegurarse de que nonce y hash no estén en el bloque al calcular
        block_copy.pop('hash', None)
        
        while True:
            block_copy['nonce'] = nonce
            block_string = json.dumps(block_copy, sort_keys=True).encode()
            hash_result = hashlib.sha256(block_string).hexdigest()
            
            if hash_result.startswith('0000'):  # Dificultad fija de 4 ceros
                return nonce, hash_result
            
            nonce += 1
            
    def validate_chain(self):
        """
        Verifica la integridad de toda la cadena
        """
        print("Validando cadena...")
        
        # Si solo tenemos el bloque génesis, la cadena es válida
        if len(self.chain) == 1:
            print("Solo bloque génesis - válido")
            return True

        for i, block in enumerate(self.chain):
            print(f"Verificando bloque {block['index']}")
            
            # Verificar el bloque (excepto el génesis)
            if block['index'] > 1 and not self.verify_block(block):
                print(f"Bloque {block['index']} falló en verify_block")
                return False
            
            # Verificar el hash del bloque
            block_copy = block.copy()
            block_copy.pop('hash', None)  # Removemos el hash actual
            block_copy.pop('nonce', None)  # Removemos el nonce actual
            _, calculated_hash = self.calculate_hash(block_copy)
            
            if block['hash'] != calculated_hash:
                print(f"Hash incorrecto en bloque {block['index']}")
                print(f"Hash esperado: {calculated_hash}")
                print(f"Hash actual: {block['hash']}")
                return False

            # Verificar cadena de bloques (excepto para el génesis)
            if i > 0:  # Para todos los bloques excepto el génesis
                previous_block = self.chain[i - 1]
                if block['previous_hash'] != previous_block['hash']:
                    print(f"Previous hash incorrecto en bloque {block['index']}")
                    print(f"Hash esperado: {previous_block['hash']}")
                    print(f"Hash actual: {block['previous_hash']}")
                    return False
        
        print("Cadena válida")
        return True

    def new_block(self, previous_hash):
        """
        Crea un nuevo bloque en la blockchain
        """
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': [],
            'previous_hash': previous_hash,
            'nonce': None,
            'hash': None
        }
        
        block['nonce'], block['hash'] = self.calculate_hash(block)
        self.last_block_hash = block['hash']

        if len(self.chain) > 0:
            if not self.verify_block(block):
                raise ValueError("Block contains invalid transactions")
            
        self.chain.append(block)
        return block

    def add_to_mempool(self, transaction):
        """
        Añade una transacción a la mempool
        """
        if not self.verify_transaction(transaction):
            raise ValueError("Invalid transaction")
        
        sender = transaction['sender']
        total_amount = transaction['amount'] + transaction['fee']
        if self.get_balance(sender) < total_amount:
            raise ValueError("Insufficient funds")

        self.mempool.append(transaction)
        return True

    def verify_transaction(self, transaction):
        """
        Verifica una transacción antes de añadirla a la mempool
        """
        if transaction['sender'] == "0":
            return True

        if 'signature' not in transaction:
            return False

        public_key = self.public_keys.get(transaction['sender'])
        if not public_key:
            return False

        transaction_copy = transaction.copy()
        signature = transaction_copy.pop('signature')
        return verify_signature(public_key, transaction_copy, signature)

    def get_mempool(self):
        """
        Retorna las transacciones pendientes en la mempool
        """
        return sorted(self.mempool, key=lambda x: x['fee'], reverse=True)

    def calculate_block_reward(self):
        """
        Calcula la recompensa actual por bloque basada en halvings
        """
        halvings = (len(self.chain) - 1) // self.halving_blocks
        return self.block_reward / (2 ** halvings)

    def mine(self, miner_address, selected_transactions=None):
        """
        Mina un nuevo bloque con las transacciones seleccionadas
        
        Args:
            miner_address (str): Dirección del minero
            selected_transactions (list): Lista de índices de las transacciones seleccionadas de la mempool
        """
        # Inicializar variables
        transactions = []
        total_fees = 0
        
        # Si se proporcionaron transacciones seleccionadas, procesarlas
        if selected_transactions and self.mempool:
            # Limitar a 3 transacciones máximo
            selected_transactions = selected_transactions[:3]
            
            # Obtener las transacciones seleccionadas y calcular fees
            temp_mempool = self.mempool.copy()
            selected_txs = []
            
            for tx_index in selected_transactions:
                if 0 <= tx_index < len(temp_mempool):
                    tx = temp_mempool[tx_index]
                    selected_txs.append(tx)
                    total_fees += tx['fee']
            
            # Remover las transacciones seleccionadas de la mempool
            for tx in selected_txs:
                self.mempool.remove(tx)
            
            transactions.extend(selected_txs)

        # Calcular recompensa total (recompensa de bloque + comisiones)
        block_reward = self.calculate_block_reward()
        total_reward = block_reward + total_fees

        # Crear transacción coinbase
        coinbase_transaction = {
            'sender': "0",
            'recipient': miner_address,
            'amount': total_reward,
            'type': 'coinbase'
        }

        # Coinbase siempre es la primera transacción
        transactions.insert(0, coinbase_transaction)

        # Crear y minar el bloque
        previous_hash = self.last_block['hash']
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': transactions,
            'previous_hash': previous_hash,
            'merkle_root': self.calculate_merkle_root(transactions),
            'nonce': None,
            'hash': None
        }
        
        # Encontrar nonce válido (PoW)
        block['nonce'], block['hash'] = self.calculate_hash(block)

        # Verificar y procesar transacciones
        for tx in transactions[1:]:  # Procesar todas excepto la coinbase
            self.balances[tx['sender']] = self.get_balance(tx['sender']) - (tx['amount'] + tx['fee'])
            self.balances[tx['recipient']] = self.get_balance(tx['recipient']) + tx['amount']

        # Procesar la recompensa del minero (coinbase)
        self.balances[miner_address] = self.get_balance(miner_address) + total_reward

        self.chain.append(block)
        return block
    
    def calculate_merkle_root(self, transactions):
        """
        Calcula el Merkle Root de las transacciones (simplificado)
        """
        if not transactions:
            return hashlib.sha256(''.encode()).hexdigest()
        
        # Convertir transacciones a hashes
        tx_hashes = [hashlib.sha256(json.dumps(tx, sort_keys=True).encode()).hexdigest() 
                    for tx in transactions]
        
        # Si hay un número impar de transacciones, duplicar la última
        if len(tx_hashes) % 2 == 1:
            tx_hashes.append(tx_hashes[-1])
        
        # Combinar hashes en pares hasta tener un único hash (merkle root)
        while len(tx_hashes) > 1:
            new_hashes = []
            for i in range(0, len(tx_hashes), 2):
                combined = tx_hashes[i] + tx_hashes[i+1]
                new_hash = hashlib.sha256(combined.encode()).hexdigest()
                new_hashes.append(new_hash)
            tx_hashes = new_hashes
        
        return tx_hashes[0]

    def verify_block(self, block):
        """
        Verifica todas las transacciones en un bloque
        """
        # Si es el bloque génesis, siempre es válido
        if block['index'] == 1:
            return True

        # La primera transacción debe ser una coinbase
        if not block['transactions'] or block['transactions'][0].get('type') != 'coinbase':
            print("Primera transacción no es coinbase")
            return False

        # Verificar transacciones normales (no coinbase)
        for transaction in block['transactions'][1:]:
            sender = transaction['sender']
            
            if 'signature' not in transaction:
                return False

            public_key = self.public_keys.get(sender)
            if not public_key:
                return False

            transaction_copy = transaction.copy()
            signature = transaction_copy.pop('signature')
            
            if not verify_signature(public_key, transaction_copy, signature):
                return False
        
        # Verificar merkle root
        calculated_merkle = self.calculate_merkle_root(block['transactions'])
        if calculated_merkle != block['merkle_root']:
            return False
            
        return True

    def get_balance(self, address):
        """
        Obtiene el balance de una dirección
        """
        return self.balances.get(address, 0)  # Retorna 0 si la dirección no existe

    @property
    def last_block(self):
        """
        Retorna el último bloque de la cadena
        """
        return self.chain[-1]

    @staticmethod
    def hash(block):
        """
        Crea un hash SHA-256 de un bloque
        """
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()