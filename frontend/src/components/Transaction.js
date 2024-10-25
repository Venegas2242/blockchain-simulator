import React, { useState } from 'react';

function Transaction({ onNewTransaction, address }) {
  const [recipient, setRecipient] = useState('');
  const [amount, setAmount] = useState('');
  const [fee, setFee] = useState('');  // Añadido estado para fee
  const [privateKey, setPrivateKey] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    const transaction = {
      sender: address,
      recipient,
      amount: parseFloat(amount),
      fee: parseFloat(fee),  // Incluido fee en la transacción
      privateKey
    };
    console.log("Transacción a realizar: ", transaction);
    onNewTransaction(transaction);
    
    // Limpiar el formulario
    setRecipient('');
    setAmount('');
    setFee('');
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
          <label htmlFor="fee">Comisión:</label>
          <input
            id="fee"
            type="number"
            step="0.01"
            value={fee}
            onChange={(e) => setFee(e.target.value)}
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