import hashlib
import json
from time import time
from ecdsa import SigningKey, VerifyingKey, SECP256k1
import binascii
import logging

logger = logging.getLogger(__name__)

class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_transactions = []
        self.nodes = set()
        self.balances = {}
        self.last_block_hash = '1'
        self.new_block(previous_hash=self.last_block_hash)  # GENESIS
        self.address_to_public_key = {}  # New dictionary to store address-public key mappings

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
            
            if sender != "0":  # Skip balance deduction for mining rewards
                self.balances[sender] = self.get_balance(sender) - amount
            self.balances[recipient] = self.get_balance(recipient) + amount
            
            logger.info(f"Updated balances: Sender ({sender}): {self.balances[sender]}, Recipient ({recipient}): {self.balances[recipient]}")

        self.current_transactions = []
        self.chain.append(block)
        return block

    def new_transaction_and_mine(self, sender, recipient, amount, signature):
        if self.get_balance(sender) < amount:
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
        balance = self.balances.get(address, 0)
        logger.info(f"Get balance for address {address}: {balance}")
        return balance

    def set_balance(self, address, amount):
        self.balances[address] = amount
        logger.info(f"Set balance for address {address}: {amount}")

    def mine(self, miner_address):
        self.current_transactions.append({
            'sender': "0",
            'recipient': miner_address,
            'amount': 1,
            'signature': None
        })
        
        previous_hash = self.last_block['hash']
        new_block = self.new_block(previous_hash)
        logger.info(f"Mined new block. Miner: {miner_address}, Reward: 1, New balance: {self.get_balance(miner_address)}")
        return new_block

    def generate_wallet(self):
        sk = SigningKey.generate(curve=SECP256k1)
        vk = sk.get_verifying_key()
        
        private_key = sk.to_string().hex()
        public_key = vk.to_string().hex()
        address = self.generate_address(vk.to_string())
        
        self.address_to_public_key[address] = public_key
        self.set_balance(address, 100)  # Set initial balance
        
        return {
            'private_key': private_key,
            'public_key': public_key,
            'address': address
        }

    @staticmethod
    def generate_address(public_key):
        public_key_bytes = public_key if isinstance(public_key, bytes) else bytes.fromhex(public_key)
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).hexdigest()
        return ripemd160_hash