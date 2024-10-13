import React from 'react';
import './Block.css';

const Block = ({ block, previousBlock, isLast }) => {
  const verifyProof = (previousHash, proof) => {
    // Si no hay bloque anterior (es el bloque génesis), consideramos la prueba válida
    if (!previousBlock) return true;

    const guess = `${previousBlock.proof}${proof}${previousHash}`;
    const guessHash = calculateHash(guess);
    return guessHash.startsWith('0000');  // Ajusta según la dificultad en el backend
  };

  const calculateHash = (str) => {
    // Implementación simple de SHA-256 para fines de demostración
    // En una aplicación real, usa una biblioteca criptográfica adecuada
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convierte a un entero de 32 bits
    }
    return hash.toString(16).padStart(64, '0');
  };

  const isProofValid = verifyProof(block.previous_hash, block.proof);
  const isPreviousHashValid = previousBlock ? (block.previous_hash === previousBlock.hash) : true;

  return (
    <div className={`block ${isProofValid && isPreviousHashValid ? 'valid' : 'invalid'}`}>
      <h3>Block {block.index}</h3>
      <p>Timestamp: {new Date(block.timestamp * 1000).toLocaleString()}</p>
      <p>Previous Hash: {block.previous_hash}</p>
      <p>Current Hash: {block.hash}</p>
      <p>Proof: {block.proof}</p>
      <p>Proof Valid: {isProofValid ? 'Yes' : 'No'}</p>
      <p>Previous Hash Valid: {isPreviousHashValid ? 'Yes' : 'No'}</p>
      <h4>Transactions:</h4>
      <ul>
        {block.transactions.map((transaction, index) => (
          <li key={index}>
            From: {transaction.sender.substring(0, 10)}...
            To: {transaction.recipient.substring(0, 10)}...
            Amount: {transaction.amount}
          </li>
        ))}
      </ul>
      {!isLast && <div className="arrow">→</div>}
    </div>
  );
};

export default Block;
