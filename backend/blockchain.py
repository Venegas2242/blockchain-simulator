import hashlib
import json
from time import time
from ecdsa import SigningKey, VerifyingKey, SECP256k1

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
        self.current_transactions = []
        self.nodes = set()
        self.balances = {}
        self.public_keys = {}
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

        if not self.verify_block(block):  # Nuevo Verificar el bloque antes de permitir la transaccion
            raise ValueError("Block contains invalid transactions")
        
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
    
    # Nuevo Verificacion por bloque 
    def verify_block(self, block):
        for transaction in block['transactions']:
            sender = transaction['sender']
            
            # Si el remitente es "0", es una transacción de recompensa y no requiere verificación de firma
            if sender == "0":
                return True

            signature = transaction['signature']


            public_key = self.public_keys.get(sender)
            if not public_key:
                return False  

            transaction_copy = transaction.copy()
            transaction_copy.pop('signature')
            if not verify_signature(public_key, transaction_copy, signature):
                return False
            
        return True

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
        print(f"Retrieving balance for {address}")  
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
    
    # Nuevo para verficar la cadena completa
    def validate_chain(self):
        for block in self.chain:
            if not self.verify_block(block):
                return False
        return True
    

