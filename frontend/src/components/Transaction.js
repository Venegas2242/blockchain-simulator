import React, { useState } from 'react';
import { ec as EC } from 'elliptic';

const ec = new EC('secp256k1');
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Transaction = ({ onNewTransaction, wallet }) => {
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [error, setError] = useState('');

  const signTransaction = (sender, recipient, amount, privateKey) => {
    try {
      const key = ec.keyFromPrivate(privateKey, 'hex');
      const message = `${sender}${recipient}${amount}`;
      const msgHash = ec.hash().update(`${sender}${recipient}${amount}`).digest('hex');
      const signature = key.sign(msgHash);
      return signature.r.toString('hex') + signature.s.toString('hex');
    } catch (error) {
      console.error('Error signing transaction:', error);
      throw new Error(`Failed to sign transaction: ${error.message}`);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    if (!recipient || !amount) {
      setError('Please fill in all fields');
      return;
    }

    try {
      console.log('Wallet:', wallet);
      console.log('Recipient:', recipient);
      console.log('Amount:', amount);

      const signature = signTransaction(wallet.address, recipient, amount, wallet.private_key);
      console.log('Signature:', signature);

      const transaction = {
        sender: wallet.address,
        recipient,
        amount: parseFloat(amount),
        signature
      };

      console.log('Sending transaction:', transaction);

      const response = await fetch(`${API_URL}/transactions/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transaction),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create transaction');
      }

      const data = await response.json();
      console.log('Transaction response:', data);

      onNewTransaction(transaction);
      setRecipient('');
      setAmount('');
    } catch (error) {
      console.error('Error creating transaction:', error);
      setError(`Failed to create transaction: ${error.message}`);
    }
  };

  return (
    <div className="transaction-form">
      <h3>Create New Transaction</h3>
      {error && <div className="error">{error}</div>}
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="recipient">Recipient Address:</label>
          <input
            type="text"
            id="recipient"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="amount">Amount:</label>
          <input
            type="number"
            id="amount"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
            min="0"
            step="0.01"
          />
        </div>
        <button type="submit">Send Transaction</button>
      </form>
    </div>
  );
};

export default Transaction;