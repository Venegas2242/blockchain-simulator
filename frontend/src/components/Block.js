import React from 'react';
import './Block.css';

const Block = ({ block, isLast }) => {
  const isGenesisBlock = block.index === 1;

  const renderTransaction = (transaction, index) => {
    const isCoinbase = transaction.sender === "0" || transaction.type === 'coinbase';

    return (
      <div 
        key={index} 
        className={`transaction ${isCoinbase ? 'transaction-coinbase' : 'transaction-regular'}`}
      >
        <div className="transaction-header">
          {isCoinbase ? '💰 Transacción Coinbase (Recompensa de Minado)' : `📝 Transacción #${index}`}
        </div>
        
        <div className="transaction-data">
          <strong>De:</strong> {transaction.sender}
        </div>
        
        <div className="transaction-data">
          <strong>Para:</strong> {transaction.recipient}
        </div>
        
        <div className="transaction-data">
          <strong>Cantidad:</strong> <span className="transaction-amount">{transaction.amount} BBC</span>
          {!isCoinbase && transaction.fee && (
            <span className="transaction-amount"> + {transaction.fee} BBC (comisión)</span>
          )}
        </div>

        {transaction.timestamp && (
          <div className="transaction-data">
            <strong>Timestamp:</strong> {new Date(transaction.timestamp * 1000).toLocaleString()}
          </div>
        )}

        {transaction.signature && (
          <div className="transaction-data">
            <strong>Firma:</strong> {transaction.signature}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`block ${isGenesisBlock ? 'genesis' : ''}`}>
      <h3>
        {isGenesisBlock ? '🌟 Bloque Génesis' : `⛓️ Bloque ${block.index}`}
      </h3>
      
      <div className="block-info">
        <p><strong>🎲 Nonce:</strong> {block.nonce}</p>
        <p><strong>🕒 Timestamp:</strong> {new Date(block.timestamp * 1000).toLocaleString()}</p>
        <p><strong>↩️ Hash Anterior:</strong> {block.previous_hash}</p>
        <p><strong>🔐 Hash Actual:</strong> {block.hash}</p>
      </div>

      <div>
        <h4>📋 Transacciones</h4>
        {block.transactions.length === 0 ? (
          <p className="no-transactions">No hay transacciones en este bloque</p>
        ) : (
          <div className="transactions-list">
            {block.transactions.map((transaction, index) => 
              renderTransaction(transaction, index)
            )}
          </div>
        )}
      </div>

      {!isLast && <div className="arrow">➡️</div>}
    </div>
  );
};

export default Block;