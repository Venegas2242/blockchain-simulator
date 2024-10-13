import React from 'react';
import './Block.css'; // Asegúrate de que este archivo contiene los estilos actualizados

const Block = ({ block, isLast }) => {
  return (
    <div className="block">
      <h3>Block {block.index}</h3>
      <p>Nonce: {block.nonce}</p>
      <p>Timestamp: {new Date(block.timestamp * 1000).toLocaleString()}</p>
      <p className="hash">
        <strong>Previous Hash:</strong> {block.previous_hash}
      </p>
      <p className="hash">
        <strong>Current Hash:</strong> {block.hash}
      </p>
      <p>Previous Hash Valid: {block.previous_hash_valid ? 'Yes' : 'No'}</p>
      <h4>Transactions:</h4>
      <ul>
        {block.transactions.map((transaction, index) => (
          <li key={index}>
            <div className="address">
              <strong>From:</strong> {transaction.sender}
            </div>
            <div className="address">
              <strong>To:</strong> {transaction.recipient}
            </div>
            <div>
              <strong>Amount:</strong> {transaction.amount}
            </div>
          </li>
        ))}
      </ul>
      {!isLast && <div className="arrow">→</div>}
    </div>
  );
};

export default Block;
