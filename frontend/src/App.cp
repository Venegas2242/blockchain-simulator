import React, { useState, useEffect } from 'react';
import Blockchain from './components/Blockchain';
import Transaction from './components/Transaction';
import Wallet from './components/Wallet';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

function App() {
  const [blockchain, setBlockchain] = useState([]);
  const [wallet, setWallet] = useState(null);
  const [balance, setBalance] = useState(null);
  const [error, setError] = useState(null);

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

    // Configurar actualizaciones periódicas
    const intervalId = setInterval(() => {
      fetchBlockchain();
      if (wallet) {
        fetchBalance(wallet.public_key);
      }
    }, 5000); // Actualizar cada 5 segundos

    return () => clearInterval(intervalId); // Limpiar el intervalo cuando el componente se desmonte
  }, []);

  const fetchBlockchain = async () => {
    try {
      const response = await fetch(`${API_URL}/chain`);
      if (!response.ok) {
        throw new Error('Network response was not ok');
      }
      const data = await response.json();
      setBlockchain(data.chain);
    } catch (error) {
      console.error('Error fetching blockchain:', error);
      setError('Failed to fetch blockchain data');
    }
  };

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
    } catch (error) {
      console.error('Error generating keys:', error);
      setError('Failed to generate wallet keys');
    }
  };

  const fetchBalance = async (address) => {
    try {
      const response = await fetch(`${API_URL}/balance?address=${encodeURIComponent(address)}`);
      if (!response.ok) {
        throw new Error('Failed to fetch balance');
      }
      const data = await response.json();
      setBalance(data.balance);
    } catch (error) {
      console.error('Error fetching balance:', error);
      setError(`Failed to fetch balance: ${error.message}`);
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
      
      // Actualizar blockchain y balance después de la transacción
      await fetchBlockchain();
      await fetchBalance(wallet.public_key);
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
        body: JSON.stringify({ miner_address: wallet.public_key }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to mine block');
      }
      const data = await response.json();
      console.log('Mined block:', data);
      
      // Actualizar blockchain y balance después de minar
      await fetchBlockchain();
      await fetchBalance(wallet.public_key);
    } catch (error) {
      console.error('Error mining:', error);
      setError(`Failed to mine block: ${error.message}`);
    }
  };

  if (error) {
    return <div>Error: {error}</div>;
  }

  return (
    <div className="App">
      <h1>Blockchain Simulator</h1>
      <div>
        <h3>Instructions:</h3>
        <ol>
          <li>Your wallet is automatically generated when you first load the page.</li>
          <li>Use the "Download Keys" button to save your keys securely.</li>
          <li>Mine blocks to earn initial coins.</li>
          <li>To make a transaction, enter the recipient's public key and the amount.</li>
          <li>Click "Send Transaction" to add the transaction to the blockchain.</li>
          <li>The blockchain will update automatically to show new blocks and transactions.</li>
        </ol>
      </div>
      {wallet && <Wallet wallet={wallet} balance={balance} />}
      <button onClick={handleMine}>Mine a Block</button>
      <Transaction onNewTransaction={handleNewTransaction} publicKey={wallet?.public_key} />
      <Blockchain chain={blockchain} />
    </div>
  );
}

export default App;
