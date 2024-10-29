import React, { useState, useEffect } from 'react';
import './VerifyBlock.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const VerifyBlock = ({ onVerifyBlock }) => {
  const [blockIndex, setBlockIndex] = useState('');
  const [sender, setSender] = useState('');
  const [recipient, setRecipient] = useState('');
  const [fee, setFee] = useState('');
  const [signature, setSignature] = useState('');
  const [publicKey, setPublicKey] = useState('');
  const [verificationResult, setVerificationResult] = useState('');
  const [blockList, setBlockList] = useState([]);
  const [amount, setAmount] = useState('');

  const clearForm = () => {
    setBlockIndex('');
    setSender('');
    setRecipient('');
    setFee('');
    setSignature('');
    setPublicKey('');
    setAmount('');
    setVerificationResult('');
  };

  useEffect(() => {
    const fetchBlockList = async () => {
      try {
        const response = await fetch(`${API_URL}/chain`);
        if (!response.ok) {
          throw new Error('Error al obtener la lista de bloques');
        }
        const data = await response.json();
        const blockIndexes = data.chain.map((block) => block.index);
        setBlockList(blockIndexes);
      } catch (error) {
        console.error('Error al obtener la lista de bloques:', error);
      }
    };

    fetchBlockList();
  }, []);

  const handleVerifyBlock = async () => {
    if (blockIndex === '' || sender === '' || recipient === '' || amount === '' || fee === '' || signature === '' || publicKey === '') {
      alert('Por favor, complete todos los campos.');
      return;
    }
    
    try {
      const indexToVerify = parseInt(blockIndex, 10) - 1;
      
      const transaction = {
        sender,
        recipient,
        amount: amount,
        fee: fee,
      };
      
      const response = await fetch(`${API_URL}/verify_block`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          block_index: indexToVerify, 
          transaction, 
          signature,
          public_key: publicKey 
        }),
      });
      
      const data = await response.json();
      setVerificationResult(data.message);
      if (typeof onVerifyBlock === 'function') {
        onVerifyBlock(data.message);
      }
    } catch (error) {
      setVerificationResult('Error');
      if (typeof onVerifyBlock === 'function') {
        onVerifyBlock('Error');
      }
    }
  };
  
  return (
    <div className="verify-block">
      <div className="verify-header">
        <h2>Verificar Bloque</h2>
        <button onClick={clearForm} className="clear-button">Limpiar</button>
      </div>
      <select
        value={blockIndex}
        onChange={(e) => setBlockIndex(e.target.value)}
      >
        <option value="">Seleccione un bloque</option>
        {blockList.map((index) => (
          <option key={index} value={index}>
            Bloque {index}
          </option>
        ))}
      </select>
      <input
        type="text"
        placeholder="Dirección del Remitente"
        value={sender}
        onChange={(e) => setSender(e.target.value)}
      />
      <input
        type="text"
        placeholder="Llave Pública del Remitente"
        value={publicKey}
        onChange={(e) => setPublicKey(e.target.value)}
      />
      <input
        type="text"
        placeholder="Dirección del Destinatario"
        value={recipient}
        onChange={(e) => setRecipient(e.target.value)}
      />
      <input
        type="number"
        placeholder="Cantidad"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
      />
      <input
        type="number"
        placeholder="Comisión"
        value={fee}
        onChange={(e) => setFee(e.target.value)}
      />
      <input
        type="text"
        placeholder="Firma"
        value={signature}
        onChange={(e) => setSignature(e.target.value)}
      />
      <button onClick={handleVerifyBlock} className="verify-button">Verificar Bloque</button>
      {verificationResult && (
        <div className={`result-container ${verificationResult === 'Error' ? 'error' : 'valid'}`}>
          {verificationResult}
        </div>
      )}
    </div>
  );
};

export default VerifyBlock;