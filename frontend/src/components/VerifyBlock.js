import React, { useState, useEffect } from 'react';
import './VerifyBlock.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const VerifyBlock = ({ onVerifyBlock }) => {
  const [blockIndex, setBlockIndex] = useState('');
  const [verificationResult, setVerificationResult] = useState('');
  const [blockList, setBlockList] = useState([]);

  // Obtener la lista de bloques cuando el componente se monta
  useEffect(() => {
    const fetchBlockList = async () => {
      try {
        const response = await fetch(`${API_URL}/chain`, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
          },
        });
        if (!response.ok) {
          throw new Error('Error al obtener la lista de bloques');
        }
        const data = await response.json();
        // Crear una lista de índices de bloques
        const blockIndexes = data.chain.map((block) => block.index);
        setBlockList(blockIndexes);
      } catch (error) {
        console.error('Error al obtener la lista de bloques:', error);
      }
    };

    fetchBlockList();
  }, []);

  const handleVerifyBlock = async () => {
    if (blockIndex === '') {
      alert('Por favor, seleccione un índice de bloque.');
      return;
    }
  
    try {
      // Calcular el índice a enviar restándole 1 al valor seleccionado
      const indexToVerify = parseInt(blockIndex, 10) - 1;
  
      const response = await fetch(`${API_URL}/verify_block`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ block_index: indexToVerify }),
      });
  
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Error al verificar el bloque');
      }
  
      const data = await response.json();
      // Mostrar el mensaje con el índice original (blockIndex) en pantalla
      setVerificationResult(`El bloque ${blockIndex} es válido.`);
      if (typeof onVerifyBlock === 'function') {
        onVerifyBlock(`El bloque ${blockIndex} es válido.`);
      }
    } catch (error) {
      console.error('Error al verificar el bloque:', error);
      // Mostrar el mensaje con el índice original (blockIndex) en pantalla
      setVerificationResult(`Error al verificar el bloque: ${error.message}`);
      if (typeof onVerifyBlock === 'function') {
        onVerifyBlock(`Error al verificar el bloque: ${error.message}`);
      }
    }
  };
  

  return (
    <div className="verify-block">
      <h2>Verificar Bloque</h2>
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
      <button onClick={handleVerifyBlock}>Verificar Bloque</button>
      {verificationResult && <p className="verification-result">{verificationResult}</p>}
    </div>
  );
};

export default VerifyBlock;
