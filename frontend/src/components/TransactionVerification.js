import React, { useState, useEffect } from 'react';
import { ec as EC } from 'elliptic';

const ec = new EC('secp256k1');
const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const TransactionVerification = () => {
  const [blockchain, setBlockchain] = useState([]);
  const [selectedBlockIndex, setSelectedBlockIndex] = useState('');
  const [verificationResults, setVerificationResults] = useState([]);
  const [error, setError] = useState('');
  const [publicKeys, setPublicKeys] = useState({});

  useEffect(() => {
    fetchBlockchain();
  }, []);

  const fetchBlockchain = async () => {
    try {
      const response = await fetch(`${API_URL}/chain`);
      if (!response.ok) {
        throw new Error('Failed to fetch blockchain data');
      }
      const data = await response.json();
      setBlockchain(data.chain);
    } catch (error) {
      console.error('Error fetching blockchain:', error);
      setError('Failed to fetch blockchain data. Please try again.');
    }
  };

  const handlePublicKeyChange = (transactionIndex, publicKey) => {
    setPublicKeys(prev => ({ ...prev, [transactionIndex]: publicKey }));
  };

  const normalizePublicKey = (publicKey) => {
    // Remove any whitespace and '0x' prefix if present
    publicKey = publicKey.replace(/\s+/g, '').replace(/^0x/, '');
    
    // If the key doesn't start with '04', prepend it
    // '04' indicates an uncompressed public key
    if (!publicKey.startsWith('04')) {
      publicKey = '04' + publicKey;
    }
    
    return publicKey;
  };

  const verifyTransactions = () => {
    if (!selectedBlockIndex) {
      setError('Please select a block to verify');
      return;
    }

    const block = blockchain[selectedBlockIndex];
    const results = block.transactions.map((transaction, index) => {
      if (transaction.sender === "0") {
        return { index, valid: true, message: "Mining reward transaction" };
      }

      const { sender, recipient, amount, signature } = transaction;
      let publicKey = publicKeys[index];

      if (!publicKey) {
        return { index, valid: false, message: "Sender's public key not provided" };
      }

      try {
        publicKey = normalizePublicKey(publicKey);
        const key = ec.keyFromPublic(publicKey, 'hex');
        const message = `${sender}${recipient}${amount}`;
        const msgHash = ec.hash().update(message).digest('hex');
        
        let signatureObj;
        try {
          signatureObj = {
            r: signature.slice(0, 64),
            s: signature.slice(64, 128)
          };
        } catch (error) {
          return { index, valid: false, message: `Invalid signature format: ${error.message}` };
        }

        const isValid = key.verify(msgHash, signatureObj);
        return { index, valid: isValid, message: isValid ? "Valid signature" : "Invalid signature" };
      } catch (error) {
        return { index, valid: false, message: `Error: ${error.message}. Please check the public key format.` };
      }
    });

    setVerificationResults(results);
    setError('');
  };

  return (
    <div className="transaction-verification">
      <h3>Verify Block Transactions</h3>
      <div className="instructions">
        <h4>Instructions:</h4>
        <ol>
          <li>Select a block from the dropdown menu.</li>
          <li>For each transaction in the block (except mining rewards), paste the sender's public key.</li>
          <li>The public key should be in hexadecimal format, with or without the '0x' prefix.</li>
          <li>Click "Verify Transactions" to check the validity of each transaction's signature.</li>
        </ol>
        <p>Note: Mining reward transactions (sender address "0") are automatically considered valid.</p>
      </div>
      {error && <div className="error">{error}</div>}
      <div>
        <label htmlFor="blockSelect">Select Block:</label>
        <select
          id="blockSelect"
          value={selectedBlockIndex}
          onChange={(e) => setSelectedBlockIndex(e.target.value)}
        >
          <option value="">Select a block</option>
          {blockchain.map((block, index) => (
            <option key={index} value={index}>
              Block {block.index} - Hash: {block.hash.substring(0, 10)}...
            </option>
          ))}
        </select>
      </div>
      {selectedBlockIndex !== '' && (
        <div className="transactions">
          <h4>Transactions in Block {blockchain[selectedBlockIndex].index}:</h4>
          {blockchain[selectedBlockIndex].transactions.map((transaction, index) => (
            <div key={index} className="transaction">
              <p>Transaction {index}: {transaction.sender} → {transaction.recipient} ({transaction.amount})</p>
              {transaction.sender !== "0" && (
                <div>
                  <label htmlFor={`publicKey-${index}`}>Sender's Public Key (hex format):</label>
                  <input
                    type="text"
                    id={`publicKey-${index}`}
                    value={publicKeys[index] || ''}
                    onChange={(e) => handlePublicKeyChange(index, e.target.value)}
                    placeholder="Paste sender's public key here (hex format)"
                  />
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      <button onClick={verifyTransactions}>Verify Transactions</button>
      {verificationResults.length > 0 && (
        <div className="verification-results">
          <h4>Verification Results:</h4>
          {verificationResults.map((result, index) => (
            <div key={index} className={`verification-result ${result.valid ? 'valid' : 'invalid'}`}>
              <p>Transaction {result.index}: {result.message}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default TransactionVerification;