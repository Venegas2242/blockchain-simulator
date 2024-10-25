import React, { useState, useEffect } from 'react';
import './Mempool.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Mempool = ({ onRefresh, wallet, onError }) => {
  const [mempool, setMempool] = useState([]);
  const [blockReward, setBlockReward] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedTransactions, setSelectedTransactions] = useState([]);

  const fetchMempool = async () => {
    try {
      const response = await fetch(`${API_URL}/mempool`);
      if (!response.ok) throw new Error('Failed to fetch mempool');
      
      const data = await response.json();
      setMempool(data.pending_transactions);
      setBlockReward(data.current_block_reward);
    } catch (error) {
      console.error('Error fetching mempool:', error);
      onError('Error loading mempool data');
    }
  };

  useEffect(() => {
    fetchMempool();
    const interval = setInterval(fetchMempool, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleTransactionSelect = (index) => {
    setSelectedTransactions(prev => {
      if (prev.includes(index)) {
        return prev.filter(i => i !== index);
      } else if (prev.length < 3) {
        return [...prev, index];
      }
      return prev;
    });
  };

  const handleMine = async () => {
    if (!wallet?.address) {
      onError('Necesitas una billetera para minar');
      return;
    }

    if (selectedTransactions.length === 0) {
      onError('Selecciona al menos una transacción para minar');
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/mine`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ 
          miner_address: wallet.address,
          selected_transactions: selectedTransactions
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to mine block');
      }

      setSelectedTransactions([]);
      await fetchMempool();
      onRefresh();
    } catch (error) {
      console.error('Error mining:', error);
      onError(`Error al minar: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Calcular la recompensa total (block reward + fees de transacciones seleccionadas)
  const calculateTotalReward = () => {
    const selectedFees = selectedTransactions.reduce((total, index) => {
      return total + (mempool[index]?.fee || 0);
    }, 0);
    return blockReward + selectedFees;
  };

  return (
    <div className="mempool-container">
      <h2>Transacciones Pendientes</h2>
      <div className="block-reward">
        <h3>Recompensa actual por bloque: {blockReward} BBC</h3>
        {selectedTransactions.length > 0 && (
          <h4>Recompensa total esperada: {calculateTotalReward()} BBC</h4>
        )}
      </div>
      <div>
        <p>Transacciones seleccionadas: {selectedTransactions.length}/3</p>
        {selectedTransactions.length > 0 && (
          <button
            onClick={handleMine}
            disabled={loading || !wallet?.address}
            className="mine-button"
          >
            {loading ? 'Minando...' : 'Minar transacciones seleccionadas'}
          </button>
        )}
      </div>
      {mempool.length === 0 ? (
        <p>No hay transacciones pendientes</p>
      ) : (
        <div className="transactions-list">
          {mempool.map((tx, index) => (
            <div 
              key={index} 
              className={`transaction-item ${selectedTransactions.includes(index) ? 'selected' : ''}`}
              onClick={() => handleTransactionSelect(index)}
            >
              <div><strong>De:</strong> {tx.sender}</div>
              <div><strong>Para:</strong> {tx.recipient}</div>
              <div><strong>Cantidad:</strong> {tx.amount} BBC</div>
              <div><strong>Comisión:</strong> {tx.fee} BBC</div>
              <div><strong>Estado:</strong> {selectedTransactions.includes(index) ? 'Seleccionada' : 'No seleccionada'}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Mempool;