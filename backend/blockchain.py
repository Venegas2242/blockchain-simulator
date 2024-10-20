import hashlib
import json
from time import time

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.balances = {}
        self.last_block_hash = '1'
        self.new_block(previous_hash=self.last_block_hash)  # GENESIS

    def new_block(self, previous_hash):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'previous_hash': previous_hash,
            'nonce': None,
            'hash': None
        }
        
        block['nonce'], block['hash'] = self.calculate_hash(block)
        self.last_block_hash = block['hash']
        
        for transaction in self.current_transactions:
            sender = transaction['sender']
            recipient = transaction['recipient']
            amount = transaction['amount']
            
            self.balances[sender] = self.get_balance(sender) - amount
            self.balances[recipient] = self.get_balance(recipient) + amount

        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction_and_mine(self, sender, recipient, amount, signature):
        if self.get_balance(sender) < amount:
            balance = self.get_balance(sender)
            raise ValueError("Insufficient funds")

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
            'signature': signature
        })

        previous_hash = self.last_block['hash']
        return self.new_block(previous_hash)

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    def calculate_hash(self, block):
        nonce = 0
        while True:
            block_string = json.dumps(block, sort_keys=True).encode() + str(nonce).encode()
            hash_resultado = hashlib.sha256(block_string).hexdigest()
            if hash_resultado.startswith('0000'):
                return nonce, hash_resultado
            nonce += 1

    def get_balance(self, address):
        return self.balances.get(address, 0)

    # Mantenemos el método mine separado para cuando se quiera minar sin transacción
    def mine(self, miner_address):
        self.current_transactions.append({
            'sender': "0",
            'recipient': miner_address,
            'amount': 1
        })
        
        previous_hash = self.last_block['hash']
        return self.new_block(previous_hash)
