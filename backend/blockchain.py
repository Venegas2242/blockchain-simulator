import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.balances = {}
        self.last_block_hash = 0, 
        self.new_block(previous_hash=self.last_block_hash) # GENESIS

    def new_block(self, previous_hash):
        print()
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'previous_hash': previous_hash,
            'nonce': None,
            'hash': None
        }
        
        # Calcular el hash actual del bloque
        block['nonce'], block['hash'] = self.calculate_hash(block)
        
        # Actualizar hash de ultimo bloque
        self.last_block_chain = block['hash']
        
        # Procesar transacciones y actualizar balances
        for transaction in self.current_transactions:
            sender = transaction['sender']
            recipient = transaction['recipient']
            amount = transaction['amount']
            
            if sender != "0":  # No descontar si es una recompensa de minado
                self.balances[sender] = self.get_balance(sender) - amount
            self.balances[recipient] = self.get_balance(recipient) + amount

        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction(self, sender, recipient, amount, signature):
        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        })
        return self.last_block['index'] + 1

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        # Asegúrate de ordenar las claves del diccionario para obtener un hash consistente
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def calculate_hash(self, block):
        nonce = 0
        while True:
            # Crear el string del bloque y codificarlo
            block_string = json.dumps(block, sort_keys=True).encode() + str(nonce).encode()
            # Calcular hash
            hash_resultado = hashlib.sha256(block_string).hexdigest()
            # Inicio de ceros
            if hash_resultado.startswith('0000'):
                return nonce, hash_resultado
            nonce += 1

    def mine(self, miner_address):
        # Añade la transacción de recompensa
        self.new_transaction(
            sender="0",
            recipient=miner_address,
            amount=1,
            signature=None  # Las transacciones de recompensa no necesitan firma
        )
        
        block = self.new_block(previous_hash=self.last_block_chain)

        return block

    def get_balance(self, address):
        return self.balances.get(address, 0)
