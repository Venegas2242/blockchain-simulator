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
  const [wallets, setWallets] = useState([]);
  const [activeWallet, setActiveWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [blockchain, setBlockchain] = useState([]);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('wallet');
  const [verifyResult, setVerifyResult] = useState(null);
  const [showLoginModal, setShowLoginModal] = useState(false);
  const [loginKey, setLoginKey] = useState('');

  const fetchBalance = useCallback(async (address) => {
    if (!address) return;
    try {
      const response = await fetch(`${API_URL}/balance?address=${encodeURIComponent(address)}`);
      if (!response.ok) throw new Error('Failed to fetch balance');
      const data = await response.json();
      setBalance(data.balance);
      setError(null);
    } catch (error) {
      setError('Failed to fetch balance');
    }
  }, []);

  const fetchBlockchain = useCallback(async () => {
    try {
      const response = await fetch(`${API_URL}/chain`);
      if (!response.ok) throw new Error('Network response was not ok');
      const data = await response.json();
      setBlockchain(data.chain);
    } catch (error) {
      setError('Failed to fetch blockchain data');
    }
  }, []);

  useEffect(() => {
    const storedWallets = localStorage.getItem('wallets');
    if (storedWallets) {
      const parsedWallets = JSON.parse(storedWallets);
      setWallets(parsedWallets);
      const activeWalletData = localStorage.getItem('activeWallet');
      if (activeWalletData) {
        const activeWallet = parsedWallets.find(w => w.address === JSON.parse(activeWalletData).address);
        if (activeWallet) {
          setActiveWallet(activeWallet);
          fetchBalance(activeWallet.address);
        }
      }
    }
    fetchBlockchain();
  }, [fetchBalance, fetchBlockchain]);

  useEffect(() => {
    const intervalId = setInterval(() => {
      if (activeWallet?.address) {
        fetchBalance(activeWallet.address);
      }
      fetchBlockchain();
    }, 10000);

    return () => clearInterval(intervalId);
  }, [activeWallet, fetchBalance, fetchBlockchain]);

  const generateWallet = async () => {
    try {
      const response = await fetch(`${API_URL}/generate_wallet`);
      if (!response.ok) throw new Error('Network response was not ok');
      
      const data = await response.json();
      const newWallet = {
        ...data,
        addresses: [data.address]
      };
      
      // Guardar solo la wallet nueva
      setWallets([newWallet]);
      setActiveWallet(newWallet);
      localStorage.setItem('wallets', JSON.stringify([newWallet]));
      localStorage.setItem('activeWallet', JSON.stringify(newWallet));
      
      fetchBalance(newWallet.address);
      setError(null);
    } catch (error) {
      setError('Failed to generate wallet');
    }
  };

  const handleLogin = async () => {
    try {
      const decryptResponse = await fetch(`${API_URL}/decrypt_private_key`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          encrypted_private_key: loginKey,
          password: "1234"
        })
      });

      if (!decryptResponse.ok) throw new Error('Invalid key');
      const decryptData = await decryptResponse.json();
      
      // Crear objeto wallet con los datos del servidor
      const wallet = {
        address: decryptData.address,
        public_key: decryptData.public_key,
        encrypted_key: loginKey
      };

      // Actualizar solo la wallet actual
      setActiveWallet(wallet);
      setWallets([wallet]); // Solo mantener la wallet activa
      localStorage.setItem('activeWallet', JSON.stringify(wallet));
      localStorage.setItem('wallets', JSON.stringify([wallet]));
      
      fetchBalance(wallet.address);
      setShowLoginModal(false);
      setLoginKey('');
      setError(null);
    } catch (error) {
      setError('Invalid private key or wallet not found');
    }
  };
  
  const switchWallet = (wallet) => {
    setActiveWallet(wallet);
    localStorage.setItem('activeWallet', JSON.stringify(wallet));
    fetchBalance(wallet.address);
  };

  const loadWallet = () => {
    const storedWallets = localStorage.getItem('wallets');
    if (storedWallets) {
      const parsedWallets = JSON.parse(storedWallets);
      setWallets(parsedWallets);
      const activeWalletData = localStorage.getItem('activeWallet');
      if (activeWalletData) {
        const activeWallet = parsedWallets.find(w => w.address === JSON.parse(activeWalletData).address);
        if (activeWallet) {
          setActiveWallet(activeWallet);
          fetchBalance(activeWallet.address);
        }
      }
    }
  };

  const logout = () => {
    setActiveWallet(null);
    setWallets([]);
    localStorage.clear(); // Limpiar todo el localStorage
    setBalance(null);
  };

  const handleNewAddress = async (address) => {
    if (activeWallet) {
      const updatedWallet = {
        ...activeWallet,
        addresses: [...(activeWallet.addresses || [activeWallet.address]), address]
      };
      
      const updatedWallets = wallets.map(w => 
        w.address === activeWallet.address ? updatedWallet : w
      );
      
      setWallets(updatedWallets);
      setActiveWallet(updatedWallet);
      localStorage.setItem('wallets', JSON.stringify(updatedWallets));
      localStorage.setItem('activeWallet', JSON.stringify(updatedWallet));
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
      console.log('Transaction added to mempool:', data);
      
      await fetchBlockchain();
      if (activeWallet?.address) {
        await fetchBalance(activeWallet.address);
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
        
        <div className="wallet-management">
          {activeWallet ? (
            <div className="active-wallet-controls">
              <select 
                value={activeWallet.address}
                onChange={(e) => {
                  const selected = wallets.find(w => w.address === e.target.value);
                  if (selected) switchWallet(selected);
                }}
              >
                {wallets.map(w => (
                  <option key={w.address} value={w.address}>
                    {w.address.substring(0, 8)}...
                  </option>
                ))}
              </select>
              <button onClick={logout}>Cerrar Sesión</button>
              <button onClick={() => setShowLoginModal(true)}>Cambiar Wallet</button>
              <button onClick={generateWallet}>Nueva Wallet</button>
            </div>
          ) : (
            <div className="wallet-login">
              <button onClick={() => setShowLoginModal(true)}>Iniciar Sesión</button>
              <button onClick={generateWallet}>Generar Nueva Wallet</button>
            </div>
          )}
        </div>

        {showLoginModal && (
          <div className="modal">
            <div className="modal-content">
              <h3>Iniciar Sesión con Wallet</h3>
              <input
                type="password"
                placeholder="Encrypted Private Key"
                value={loginKey}
                onChange={(e) => setLoginKey(e.target.value)}
              />
              <button onClick={handleLogin}>Iniciar Sesión</button>
              <button onClick={() => setShowLoginModal(false)}>Cancelar</button>
            </div>
          </div>
        )}

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
          {activeWallet && <Wallet wallet={activeWallet} balance={balance} onNewAddress={handleNewAddress}/>}
        </div>
        
        <div className={`tab-content ${activeTab === 'transaction' ? 'active' : ''}`}>
          <Transaction onNewTransaction={handleNewTransaction} address={activeWallet?.address} />
        </div>

        <div className={`tab-content ${activeTab === 'mempool' ? 'active' : ''}`}>
          <Mempool 
            wallet={activeWallet}
            onRefresh={() => {
              fetchBlockchain();
              if (activeWallet?.address) fetchBalance(activeWallet.address);
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
            wallet={activeWallet} 
            onError={setError}
            onBalanceUpdate={() => {
              if (activeWallet?.address) fetchBalance(activeWallet.address);
            }}
          />
        </div>
      </main>
    </div>
  );
}

export default App;