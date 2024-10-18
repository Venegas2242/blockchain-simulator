import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Wallet from './components/Wallet';
import Transaction from './components/Transaction';
import Blockchain from './components/Blockchain';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [wallet, setWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [blockchain, setBlockchain] = useState([]);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('wallet');

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
  }, [fetchBalance, fetchBlockchain]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (wallet?.public_key) {
        fetchBalance(wallet.public_key);
      }
      fetchBlockchain();
    }, 10000);

    return () => clearInterval(intervalId);
  }, [wallet, fetchBalance, fetchBlockchain]);

  const generateWallet = async () => {
    try {
      const response = await fetch(`${API_URL}/generate_wallet`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setWallet(data);
      localStorage.setItem('wallet', JSON.stringify(data));
      fetchBalance(data.public_key);
      setError(null);
    } catch (error) {
      console.error('Error generating wallet:', error);
      setError('Failed to generate wallet. Please try again.');
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
    <div className="container">
      <header className="header">
        <h1>Simulador Blockchain</h1>
      </header>
      <main className="main-content">
        {error && <div className="error">{error}</div>}
        <div className="tab-container">
          <button className={`tab ${activeTab === 'wallet' ? 'active' : ''}`} onClick={() => setActiveTab('wallet')}>Billetera</button>
          <button className={`tab ${activeTab === 'transaction' ? 'active' : ''}`} onClick={() => setActiveTab('transaction')}>Transacción</button>
          <button className={`tab ${activeTab === 'mining' ? 'active' : ''}`} onClick={() => setActiveTab('mining')}>Minado</button>
          <button className={`tab ${activeTab === 'blockchain' ? 'active' : ''}`} onClick={() => setActiveTab('blockchain')}>Blockchain</button>
        </div>
        
        <div className={`tab-content ${activeTab === 'wallet' ? 'active' : ''}`}>
          {wallet && <Wallet wallet={wallet} balance={balance} />}
          {!wallet && <button onClick={generateWallet}>Generate Wallet</button>}
        </div>
        
        <div className={`tab-content ${activeTab === 'transaction' ? 'active' : ''}`}>
          <h2>New Transaction</h2>
          <Transaction onNewTransaction={handleNewTransaction} publicKey={wallet?.public_key} />
        </div>
        
        <div className={`tab-content ${activeTab === 'mining' ? 'active' : ''}`}>
          <h2>Mining</h2>
          <button onClick={handleMine}>Mine a Block</button>
        </div>
        
        <div className={`tab-content ${activeTab === 'blockchain' ? 'active' : ''}`}>
          <Blockchain chain={blockchain} />
        </div>
      </main>
    </div>
  );
}

export default App;
