import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.balances = {}
        self.difficulty = 4  # Número de ceros iniciales requeridos
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        
        # Calcular el hash actual del bloque
        block['hash'] = self.calculate_hash(block, proof)
        
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

    def proof_of_work(self, last_block):
        last_proof = last_block['proof']
        last_hash = self.hash(last_block)

        proof = 0
        while self.valid_proof(last_proof, proof, last_hash) is False:
            proof += 1

        return proof

    def valid_proof(self, last_proof, proof, last_hash):
        guess = f'{last_proof}{proof}{last_hash}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:self.difficulty] == "0" * self.difficulty

    def calculate_hash(self, block, proof):
        block_string = json.dumps(block, sort_keys=True)
        return hashlib.sha256(f"{block_string}{proof}".encode()).hexdigest()

    def mine(self, miner_address):
        # Añade la transacción de recompensa
        self.new_transaction(
            sender="0",
            recipient=miner_address,
            amount=1,
            signature=None  # Las transacciones de recompensa no necesitan firma
        )

        # Obtener el último bloque
        last_block = self.last_block

        # Encontrar el nuevo proof
        proof = self.proof_of_work(last_block)

        # Crear el nuevo bloque
        previous_hash = self.hash(last_block)
        block = self.new_block(proof, previous_hash)

        return block

    def get_balance(self, address):
        return self.balances.get(address, 0)
