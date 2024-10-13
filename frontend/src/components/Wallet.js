import React from 'react';
import './Wallet.css';

const Wallet = ({ wallet, balance }) => {
  const truncateKey = (key) => {
    if (key) {
      return key.substr(0, 32) + '...';
    }
    return '';
  };

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text).then(() => {
      alert('Copied to clipboard!');
    });
  };

  if (!wallet) {
    return <div>Loading wallet...</div>;
  }

  return (
    <div className="wallet">
      <h2>Your Wallet</h2>
      <p>
        Public Key: {truncateKey(wallet.public_key)}
        <button onClick={() => copyToClipboard(wallet.public_key)}>Copy</button>
      </p>
      <p>
        Private Key: {truncateKey(wallet.private_key)}
        <button onClick={() => copyToClipboard(wallet.private_key)}>Copy</button>
      </p>
      <p>Balance: {balance}</p>
    </div>
  );
};

export default Wallet;
