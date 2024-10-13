import React, { useState, useEffect, useCallback } from 'react';
import Blockchain from './components/Blockchain';
import Transaction from './components/Transaction';
import Wallet from './components/Wallet';
import './App.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [blockchain, setBlockchain] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [error, setError] = useState(null);

  const fetchBlockchain = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/chain`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setBlockchain(data.chain);
      setError(null);
    } catch (error) {
      console.error('Error fetching blockchain:', error);
      setError('Failed to fetch blockchain data. Please try again.');
    }
  }, []);

  const fetchBalance = useCallback(async (address) => {
    if (!address) return;
    try {
      const response = await fetch(`${API_URL}/balance?address=${encodeURIComponent(address)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }
      const data = await response.json();
      setBalance(data.balance);
      setError(null);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setError('Failed to fetch balance. Please try again.');
    }
  }, []);

  useEffect(() => {
    const storedWallet = localStorage.getItem('wallet');
    if (storedWallet) {
      const parsedWallet = JSON.parse(storedWallet);
      setWallet(parsedWallet);
      fetchBalance(parsedWallet.public_key);
    } else {
      generateWallet();
    }
    fetchBlockchain();

    const intervalId = setInterval(() => {
      fetchBlockchain();
      if (wallet?.public_key) {
        fetchBalance(wallet.public_key);
      }
    }, 10000);  // Actualizar cada 10 segundos en lugar de 5

    return () => clearInterval(intervalId);
  }, [fetchBlockchain, fetchBalance]);

  const generateWallet = async () => {
    try {
      const response = await fetch(`${API_URL}/generate_keys`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setWallet(data);
      localStorage.setItem('wallet', JSON.stringify(data));
      fetchBalance(data.public_key);
      setError(null);
    } catch (error) {
      console.error('Error generating keys:', error);
      setError('Failed to generate wallet keys. Please try again.');
    }
  };

  const handleNewTransaction = async (transaction) => {
    try {
      const response = await fetch(`${API_URL}/transactions/new`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(transaction),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to create transaction');
      }
      const data = await response.json();
      console.log('Transaction created:', data);
      
      await fetchBlockchain();
      if (wallet?.public_key) {
        await fetchBalance(wallet.public_key);
      }
    } catch (error) {
      console.error('Error creating transaction:', error);
      setError(`Failed to create transaction: ${error.message}`);
    }
  };

  const handleMine = async () => {
    try {
      const response = await fetch(`${API_URL}/mine`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ miner_address: wallet?.public_key }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to mine block');
      }
      const data = await response.json();
      console.log('Mined block:', data);
      
      await fetchBlockchain();
      if (wallet?.public_key) {
        await fetchBalance(wallet.public_key);
      }
    } catch (error) {
      console.error('Error mining:', error);
      setError(`Failed to mine block: ${error.message}`);
    }
  };

  return (
    <div className="App">
      <h1>Blockchain Simulator</h1>
      {error && <div className="error">{error}</div>}
      {wallet && <Wallet wallet={wallet} balance={balance} />}
      <div className="actions">
        <button onClick={handleMine}>Mine a Block</button>
        <Transaction onNewTransaction={handleNewTransaction} publicKey={wallet?.public_key} />
      </div>
      <Blockchain chain={blockchain} />
    </div>
  );
}

export default App;
