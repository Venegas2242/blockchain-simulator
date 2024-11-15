import React, { useState, useEffect, useCallback } from 'react';
import './App.css';
import Wallet from './components/Wallet';
import Transaction from './components/Transaction';
import Blockchain from './components/Blockchain';
import VerifyBlock from './components/VerifyBlock';
import Mempool from './components/Mempool';
import Escrow from './components/Escrow'; 

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [wallet, setWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [blockchain, setBlockchain] = useState([]);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('wallet');
  const [verifyResult, setVerifyResult] = useState(null);

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
      const response = await fetch(`${API_URL}/generate_wallet`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setWallet(data);
      localStorage.setItem('wallet', JSON.stringify(data));
      fetchBalance(data.address);
      setError(null);
    } catch (error) {
      console.error('Error generating wallet:', error);
      setError('Failed to generate wallet. Please try again.');
    }
  };

  const handleNewTransaction = async (transaction) => {
    try {
      console.log("Transacción a realizar: ", transaction);
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
      console.log('Transaction added to mempool:', data);
      
      await fetchBlockchain();
      if (wallet?.address) {
        await fetchBalance(wallet.address);
      }
      setError(null);
    } catch (error) {
      console.error('Error creating transaction:', error);
      setError(`Failed to create transaction: ${error.message}`);
    }
  };

  const handleVerifyBlock = async (blockIndex) => {
    setVerifyResult(null);
    try {
      const response = await fetch(`${API_URL}/verify_block`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ block_index: blockIndex }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to verify block');
      }
      const data = await response.json();
      setVerifyResult(`Block ${blockIndex} is valid`);
      console.log('Verify result:', data);
    } catch (error) {
      console.error('Error verifying block:', error);
      setVerifyResult(`Failed to verify block: ${error.message}`);
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
          <button 
            className={`tab ${activeTab === 'wallet' ? 'active' : ''}`} 
            onClick={() => setActiveTab('wallet')}
          >
            Billetera
          </button>
          <button 
            className={`tab ${activeTab === 'transaction' ? 'active' : ''}`} 
            onClick={() => setActiveTab('transaction')}
          >
            Transacción
          </button>
          <button 
            className={`tab ${activeTab === 'mempool' ? 'active' : ''}`} 
            onClick={() => setActiveTab('mempool')}
          >
            Mempool
          </button>
          <button 
            className={`tab ${activeTab === 'blockchain' ? 'active' : ''}`} 
            onClick={() => setActiveTab('blockchain')}
          >
            Blockchain
          </button>
          <button 
            className={`tab ${activeTab === 'verify' ? 'active' : ''}`} 
            onClick={() => setActiveTab('verify')}
          >
            Verificar
          </button>
          <button 
            className={`tab ${activeTab === 'escrow' ? 'active' : ''}`} 
            onClick={() => setActiveTab('escrow')}
          >
            Smart Contract
          </button>
        </div>
        
        <div className={`tab-content ${activeTab === 'wallet' ? 'active' : ''}`}>
          {wallet && <Wallet wallet={wallet} balance={balance} />}
          {!wallet && <button onClick={generateWallet}>Generate Wallet</button>}
        </div>
        
        <div className={`tab-content ${activeTab === 'transaction' ? 'active' : ''}`}>
          <Transaction onNewTransaction={handleNewTransaction} address={wallet?.address} />
        </div>

        <div className={`tab-content ${activeTab === 'mempool' ? 'active' : ''}`}>
          <Mempool 
            wallet={wallet}
            onRefresh={() => {
              fetchBlockchain();
              if (wallet?.address) fetchBalance(wallet.address);
            }}
            onError={setError}
          />
        </div>
        
        <div className={`tab-content ${activeTab === 'blockchain' ? 'active' : ''}`}>
          <Blockchain chain={blockchain} />
        </div>

        <div className={`tab-content ${activeTab === 'verify' ? 'active' : ''}`}>
          <VerifyBlock onVerifyResult={handleVerifyBlock} />
          {verifyResult && <div className="verify-result">{verifyResult}</div>}
        </div>

        <div className={`tab-content ${activeTab === 'escrow' ? 'active' : ''}`}>
          <Escrow 
            wallet={wallet} 
            onError={setError}
            onBalanceUpdate={() => {
              if (wallet?.address) fetchBalance(wallet.address);
            }}
          />
        </div>
      </main>
    </div>
  );
}

export default App;