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
  const [isContractTransaction, setIsContractTransaction] = useState(false);

  const clearForm = () => {
    setBlockIndex('');
    setSender('');
    setRecipient('');
    setFee('');
    setSignature('');
    setPublicKey('');
    setAmount('');
    setVerificationResult('');
    setIsContractTransaction(false);
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
    // Validación diferente según el tipo de transacción
    if (isContractTransaction) {
        // Para transacciones del contrato, solo validar campos necesarios
        if (blockIndex === '' || sender === '' || recipient === '' || amount === '' || fee === '') {
            alert('Por favor, complete todos los campos requeridos.');
            return;
        }
    } else {
        // Para transacciones normales, validar todos los campos
        if (blockIndex === '' || sender === '' || recipient === '' || amount === '' || fee === '' || signature === '' || publicKey === '') {
            alert('Por favor, complete todos los campos.');
            return;
        }
    }
    
    try {
        const indexToVerify = parseInt(blockIndex, 10) - 1;
        
        const transaction = {
            sender,
            recipient,
            amount: amount,
            fee: fee,
            type: isContractTransaction ? 'contract_transfer' : 'normal'
        };
        
        const response = await fetch(`${API_URL}/verify_block`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                block_index: indexToVerify, 
                transaction, 
                signature: isContractTransaction ? 'VALID' : signature,
                public_key: isContractTransaction ? '' : publicKey 
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
        onChange={(e) => {
          setSender(e.target.value);
          // Activar modo contrato si el remitente es escrow_contract
          if (e.target.value === 'escrow_contract') {
            setIsContractTransaction(true);
            setSignature('VALID');
          } else {
            setIsContractTransaction(false);
            setSignature('');
          }
        }}
      />
      {!isContractTransaction && (
        <input
          type="text"
          placeholder="Llave Pública del Remitente"
          value={publicKey}
          onChange={(e) => setPublicKey(e.target.value)}
        />
      )}
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
      {!isContractTransaction ? (
        <input
          type="text"
          placeholder="Firma"
          value={signature}
          onChange={(e) => setSignature(e.target.value)}
        />
      ) : (
        <div className="contract-transaction-info">
          <p className="contract-note">Transacción del Smart Contract</p>
          <input
            type="text"
            value="VALID"
            disabled
            className="contract-signature"
          />
          <p className="helper-text">Las transacciones del contrato usan una firma especial</p>
        </div>
      )}
      <button onClick={handleVerifyBlock} className="verify-button">
        Verificar Bloque
      </button>
      {verificationResult && (
        <div className={`result-container ${verificationResult === 'Error' ? 'error' : 'valid'}`}>
          {verificationResult}
        </div>
      )}
    </div>
  );
};

export default VerifyBlock;