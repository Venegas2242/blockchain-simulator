import React, { useState } from 'react';
import './Wallet.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Wallet = ({ wallet, balance }) => {
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

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

  const handleDownloadPrivateKey = async (e) => {
    e.preventDefault();
    if (!password) {
      setError('Please enter a password');
      return;
    }

    if (!wallet || !wallet.private_key) {
      setError('Wallet not initialized');
      return;
    }

    try {
      const response = await fetch(`${API_URL}/download_private_key`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          private_key: wallet.private_key,
          password: password,
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to generate PKCS#5 key');
      }

      const blob = await response.blob();
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.style.display = 'none';
      a.href = url;
      a.download = 'private_key.pem';
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      setError('');
      setPassword('');
    } catch (error) {
      console.error('Error downloading private key:', error);
      setError('Failed to download private key. Please try again.');
    }
  };

  if (!wallet) {
    return <div>Loading wallet...</div>;
  }

  return (
    <div className="wallet">
      <h2>Your Wallet</h2>
      <p>
        Address: {wallet.address || 'Not available'}
        <button onClick={() => copyToClipboard(wallet.address)}>Copy</button>
      </p>
      <p>
        Public Key: {truncateKey(wallet.public_key)}
        <button onClick={() => copyToClipboard(wallet.public_key)}>Copy</button>
      </p>
      <p>
        Private Key: {truncateKey(wallet.private_key)}
        <button onClick={() => copyToClipboard(wallet.private_key)}>Copy</button>
      </p>
      <p>Balance: {balance !== null ? balance : 'Loading...'}</p>
      
      <div className="key-management">
        <h3>Download Private Key (PKCS#5 format)</h3>
        {error && <div className="error">{error}</div>}
        <form onSubmit={handleDownloadPrivateKey}>
          <div>
            <label htmlFor="password">Password:</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <button type="submit">Download Private Key</button>
        </form>
      </div>
    </div>
  );
};

export default Wallet;