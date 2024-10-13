import React, { useState } from 'react';

function Transaction({ onNewTransaction, publicKey }) {
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onNewTransaction({
      sender: publicKey,
      recipient,
      amount: parseFloat(amount),
      signature: 'dummy_signature', // En una app real, firmarías la transacción aquí
    });
    setRecipient('');
    setAmount('');
  };

  return (
    <div>
      <h2>New Transaction</h2>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="recipient">Recipient's public key:</label>
          <input
            id="recipient"
            type="text"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="amount">Amount:</label>
          <input
            id="amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <button type="submit">Send Transaction</button>
      </form>
    </div>
  );
}

export default Transaction;
