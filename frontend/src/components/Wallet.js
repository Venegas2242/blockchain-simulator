import React, { useState } from 'react';
import './Wallet.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Wallet = ({ wallet, balance }) => {
  const [showAddress, setShowAddress] = useState(false);
  const [showPublicKey, setShowPublicKey] = useState(false);
  const [password, setPassword] = useState('');
  const [showPasswordInput, setShowPasswordInput] = useState(false);

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

  const handleAddressReveal = () => {
    setShowAddress(true);
  };

  const handlePublicKeyReveal = () => {
    setShowPublicKey(true);
  };

  const handleDecryptPrivateKey = async () => {
    try {
      const response = await fetch(`${API_URL}/decrypt_private_key`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          encrypted_private_key: wallet.encrypted_key,
          password: password,
        }),
      });

      if (!response.ok) {
        throw new Error('Decryption failed');
      }

      const data = await response.json();
      copyToClipboard(data.decrypted_private_key);
      setShowPasswordInput(false);
      setPassword('');
    } catch (error) {
      alert('Failed to decrypt private key. Please check your password and try again.');
    }
  };

  if (!wallet) {
    return <div>Loading wallet...</div>;
  }

  return (
    <div className="wallet">
      <p>
        <strong>Dirección: </strong>
        {showAddress ? (
          <>
            {truncateKey(wallet.address)}
            <button onClick={() => copyToClipboard(wallet.address)}>Copiar</button>
          </>
        ) : (
          <button onClick={handleAddressReveal}>Mostrar dirección</button>
        )}
      </p>
      <p>
        <strong>Llave Pública: </strong>
        {showPublicKey ? (
          <>
            {truncateKey(wallet.public_key)}
            <button onClick={() => copyToClipboard(wallet.public_key)}>Copiar</button>
          </>
        ) : (
          <button onClick={handlePublicKeyReveal}>Mostrar llave pública</button>
        )}
      </p>
      <p>
        <strong>Llave Privada (Cifrada):</strong> {truncateKey(wallet.encrypted_key)}
        <button onClick={() => setShowPasswordInput(true)}>Decifrar y copiar</button>
      </p>
      {showPasswordInput && (
        <div>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            placeholder="Enter password (1234)"
          />
          <button onClick={handleDecryptPrivateKey}>Submit</button>
        </div>
      )}
      <p><strong>Saldo:</strong> {balance} BBC</p>
    </div>
  );
};

export default Wallet;