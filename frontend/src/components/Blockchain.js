import React from 'react';
import Block from './Block';
import './Blockchain.css';

const Blockchain = ({ chain }) => {
  return (
    <div className="blockchain-container">
      <h2>Blockchain</h2>
      <div className="blockchain">
        {chain.map((block, index) => (
          <Block 
            key={block.index} 
            block={block} 
            previousBlock={index > 0 ? chain[index - 1] : null}
            isLast={index === chain.length - 1} 
          />
        ))}
      </div>
    </div>
  );
};

export default Blockchain;
