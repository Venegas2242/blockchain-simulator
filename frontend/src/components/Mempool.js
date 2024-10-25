import React, { useState, useEffect } from 'react';
import './Mempool.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Mempool = ({ onRefresh, wallet, onError }) => {
  const [mempool, setMempool] = useState([]);
  const [blockReward, setBlockReward] = useState(0);
  const [loading, setLoading] = useState(false);

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

  const handleMine = async (transaction) => {
    if (!wallet?.address) {
      onError('Necesitas una billetera para minar');
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
          miner_address: wallet.address 
        }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.message || 'Failed to mine block');
      }

      await fetchMempool();
      onRefresh(); // Para actualizar la blockchain y balances
    } catch (error) {
      console.error('Error mining:', error);
      onError(`Error al minar: ${error.message}`);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="mempool-container">
      <h2>Transacciones Pendientes</h2>
      <div className="block-reward">
        <h3>Recompensa actual por bloque: {blockReward} BBC</h3>
      </div>
      {mempool.length === 0 ? (
        <p>No hay transacciones pendientes</p>
      ) : (
        <div className="transactions-list">
          {mempool.map((tx, index) => (
            <div key={index} className="transaction-item">
              <div><strong>De:</strong> {tx.sender}</div>
              <div><strong>Para:</strong> {tx.recipient}</div>
              <div><strong>Cantidad:</strong> {tx.amount} BBC</div>
              <div><strong>Comisión:</strong> {tx.fee} BBC</div>
              <div><strong>Ganancia potencial:</strong> {tx.fee + blockReward} BBC</div>
              <button
                onClick={() => handleMine(tx)}
                disabled={loading || !wallet?.address}
                className="mine-button"
              >
                {loading ? 'Minando...' : 'Minar esta transacción'}
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Mempool;