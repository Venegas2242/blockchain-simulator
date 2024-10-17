import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Wallet from './components/Wallet';
import Transaction from './components/Transaction';
import Blockchain from './components/Blockchain';
import KeyManagement from './components/KeyManagement';
import TransactionVerification from './components/TransactionVerification';

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
      console.log("Fetched balance:", data.balance);
      setBalance(data.balance);
      setError(null);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setError('Failed to fetch balance. Please try again.');
    }
  }, []);

  const fetchBlockchain = useCallback(async () => {
    try {
      console.log("Fetching blockchain data...");
      const response = await fetch(`${API_URL}/chain`);
      console.log("Response status:", response.status);
      console.log("Response headers:", response.headers);
      
      if (!response.ok) {
        const errorText = await response.text();
        console.error("Error response body:", errorText);
        throw new Error(`HTTP error! status: ${response.status}, body: ${errorText}`);
      }
      
      const data = await response.json();
      console.log("Received blockchain data:", data);
      setBlockchain(data.chain);
      setError(null);
    } catch (error) {
      console.error('Error fetching blockchain:', error);
      setError(`Failed to fetch blockchain data: ${error.message}. Please try again.`);
    }
  }, []);

  useEffect(() => {
    const storedWallet = localStorage.getItem('wallet');
    if (storedWallet) {
      const parsedWallet = JSON.parse(storedWallet);
      setWallet(parsedWallet);
      fetchBalance(parsedWallet.address);
    } else {
      generateWallet();
    }
    fetchBlockchain();
  }, [fetchBalance, fetchBlockchain]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (wallet?.address) {
        fetchBalance(wallet.address);
      }
      fetchBlockchain();
    }, 10000);

    return () => clearInterval(intervalId);
  }, [wallet, fetchBalance, fetchBlockchain]);

  const generateWallet = async () => {
    try {
      console.log("Starting wallet generation process");
      const response = await fetch(`${API_URL}/generate_keys`);
      console.log("Response received from server");
      
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Network response was not ok');
      }
      
      const data = await response.json();
      console.log("Wallet data received:", data);
      
      setWallet(data);
      localStorage.setItem('wallet', JSON.stringify(data));
      console.log("Wallet saved to local storage");
      
      fetchBalance(data.address);
      setError(null);
    } catch (error) {
      console.error('Error generating keys:', error);
      setError(`Failed to generate wallet keys: ${error.message}. Please check the server logs for more details.`);
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
      if (wallet?.address) {
        await fetchBalance(wallet.address);
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
        body: JSON.stringify({ miner_address: wallet?.address }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to mine block');
      }
      const data = await response.json();
      console.log('Mined block:', data);
      
      await fetchBlockchain();
      if (wallet?.address) {
        await fetchBalance(wallet.address);
      }
    } catch (error) {
      console.error('Error mining:', error);
      setError(`Failed to mine block: ${error.message}`);
    }
  };

  return (
    <div className="container">
      <header className="header">
        <h1>Blockchain Simulator</h1>
      </header>
      <main className="main-content">
        {error && <div className="error">{error}</div>}
        <div className="tab-container">
          <button className={`tab ${activeTab === 'wallet' ? 'active' : ''}`} onClick={() => setActiveTab('wallet')}>Wallet</button>
          <button className={`tab ${activeTab === 'transaction' ? 'active' : ''}`} onClick={() => setActiveTab('transaction')}>Transaction</button>
          <button className={`tab ${activeTab === 'mining' ? 'active' : ''}`} onClick={() => setActiveTab('mining')}>Mining</button>
          <button className={`tab ${activeTab === 'blockchain' ? 'active' : ''}`} onClick={() => setActiveTab('blockchain')}>Blockchain</button>
          <button className={`tab ${activeTab === 'keymanagement' ? 'active' : ''}`} onClick={() => setActiveTab('keymanagement')}>Key Management</button>
          <button className={`tab ${activeTab === 'verify' ? 'active' : ''}`} onClick={() => setActiveTab('verify')}>Verify Transaction</button>
        </div>
        
        <div className={`tab-content ${activeTab === 'wallet' ? 'active' : ''}`}>
          <h2>Your Wallet</h2>
          {wallet && <Wallet wallet={wallet} balance={balance} />}
        </div>
        
        <div className={`tab-content ${activeTab === 'transaction' ? 'active' : ''}`}>
          <h2>New Transaction</h2>
          <Transaction onNewTransaction={handleNewTransaction} wallet={wallet} />
        </div>
        
        <div className={`tab-content ${activeTab === 'mining' ? 'active' : ''}`}>
          <h2>Mining</h2>
          <button onClick={handleMine}>Mine a Block</button>
        </div>
        
        <div className={`tab-content ${activeTab === 'blockchain' ? 'active' : ''}`}>
          <h2>Blockchain</h2>
          <Blockchain chain={blockchain} />
        </div>

        <div className={`tab-content ${activeTab === 'keymanagement' ? 'active' : ''}`}>
          <h2>Key Management</h2>
          <KeyManagement wallet={wallet} />
        </div>

        <div className={`tab-content ${activeTab === 'verify' ? 'active' : ''}`}>
          <h2>Verify Transaction</h2>
          <TransactionVerification />
        </div>
      </main>
    </div>
  );
}

export default App;