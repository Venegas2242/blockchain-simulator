import React from 'react';
import './Block.css'; // Asegúrate de que este archivo contiene los estilos actualizados

const Block = ({ block, isLast }) => {
  return (
    <div className="block">
      <h3><strong>Block</strong> {block.index}</h3>
      <p><strong>Nonce:</strong> {block.nonce}</p>
      <p><strong>Timestamp:</strong> {new Date(block.timestamp * 1000).toLocaleString()}</p>
      <p className="hash">
        <strong>Previous Hash:</strong> {block.previous_hash}
      </p>
      <p className="hash">
        <strong>Current Hash:</strong> {block.hash}
      </p>
      
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
