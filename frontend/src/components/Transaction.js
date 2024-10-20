import React, { useState } from 'react';

function Transaction({ onNewTransaction, address }) {
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [privateKey, setPrivateKey] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    onNewTransaction({
      sender: address,
      recipient,
      amount: parseFloat(amount),
      privateKey
    });
    setRecipient('');
    setAmount('');
    setPrivateKey('');
  };

  return (
    <div>
      <form onSubmit={handleSubmit}>
        <div>
          <label htmlFor="recipient">Dirección receptor:</label>
          <input
            id="recipient"
            type="text"
            value={recipient}
            onChange={(e) => setRecipient(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="amount">Cantidad:</label>
          <input
            id="amount"
            type="number"
            step="0.01"
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            required
          />
        </div>
        <div>
          <label htmlFor="privateKey">Llave privada:</label>
          <input
            id="privateKey"
            type="text"
            value={privateKey}
            onChange={(e) => setPrivateKey(e.target.value)}
            required
          />
        </div>
        <button type="submit">Enviar</button>
      </form>
    </div>
  );
}

export default Transaction;