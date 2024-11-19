import React, { useState, useEffect, useCallback } from 'react';
import './Mempool.css';
import MiningProgress from './MiningProgress';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Mempool = ({ onRefresh, wallet, onError }) => {
  const [mempool, setMempool] = useState([]);
  const [blockReward, setBlockReward] = useState(0);
  const [loading, setLoading] = useState(false);
  const [selectedTransactions, setSelectedTransactions] = useState([]);
  const [showMiningProgress, setShowMiningProgress] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [miningProgress, setMiningProgress] = useState({
    status: 'not_started',
    nonce: 0,
    hash: '',
    found: false,
    final_nonce: null,
    final_hash: null
  });

  const fetchMempool = useCallback(async () => {
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
  }, [onError]);

  useEffect(() => {
    fetchMempool();
    const interval = setInterval(fetchMempool, 5000);
    return () => clearInterval(interval);
  }, [fetchMempool]);

  useEffect(() => {
    let pollInterval;
    if (isPolling) {
      pollInterval = setInterval(async () => {
        try {
          const response = await fetch(`${API_URL}/mine/progress`);
          if (!response.ok) throw new Error('Failed to fetch mining progress');
          
          const data = await response.json();
          console.log('Mining progress:', data);  // Para debugging
          
          setMiningProgress(data);
          
          if (data.status === 'completed' || data.found) {
            clearInterval(pollInterval);
            setIsPolling(false);
            setLoading(false);
            await fetchMempool();
            if (onRefresh) onRefresh();
          }
        } catch (error) {
          console.error('Error polling progress:', error);
          setIsPolling(false);
          clearInterval(pollInterval);
        }
      }, 1000);
    }
    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
    };
  }, [isPolling, fetchMempool, onRefresh]);

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

  const calculateTotalReward = () => {
    const selectedFees = selectedTransactions.reduce((total, index) => {
      return total + (mempool[index]?.fee || 0);
    }, 0);
    return blockReward + selectedFees;
  };

  const resetMiningState = () => {
    setShowMiningProgress(false);
    setSelectedTransactions([]);
    setMiningProgress({
      status: 'not_started',
      nonce: 0,
      hash: '',
      found: false,
      final_nonce: null,
      final_hash: null
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
    setShowMiningProgress(true);
    setIsPolling(true);
    
    // Establecer estado inicial de minado
    setMiningProgress({
      status: 'starting',
      nonce: 0,
      hash: '',
      found: false,
      final_nonce: null,
      final_hash: null
    });
  
    try {
      // Iniciar el minado
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
  
      const data = await response.json();
      console.log('Mining completed:', data);
  
      // Actualizar el estado con el resultado final
      setMiningProgress(prev => ({
        ...prev,
        status: 'completed',
        found: true,
        final_nonce: data.nonce,
        final_hash: data.hash
      }));
  
      // Actualizar la interfaz
      await fetchMempool();
      if (onRefresh) onRefresh();
      
      setLoading(false);
      setIsPolling(false);
      setSelectedTransactions([]);
  
    } catch (error) {
      console.error('Mining error:', error);
      onError(`Error al minar: ${error.message}`);
      setLoading(false);
      setIsPolling(false);
      setMiningProgress(prev => ({
        ...prev,
        status: 'error',
        error: error.message
      }));
    }
  };

  return (
    <div className="mempool-container">
      <h2>Transacciones Pendientes ({mempool.length})</h2>
      
      <div className="block-reward">
        <h3>Recompensa actual por bloque: {blockReward} BBC</h3>
        {selectedTransactions.length > 0 && (
          <h4>Recompensa total esperada: {calculateTotalReward()} BBC</h4>
        )}
      </div>

      {showMiningProgress && (
        <div className="mining-progress-container">
          <MiningProgress 
            isVisible={showMiningProgress}
            progress={miningProgress}
          />
          <button 
            onClick={resetMiningState}
            className="close-progress-button"
          >
            Cerrar
          </button>
        </div>
      )}

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
              key={`${tx.sender}-${tx.recipient}-${tx.amount}-${index}`}
              className={`transaction-item ${selectedTransactions.includes(index) ? 'selected' : ''}`}
              onClick={() => handleTransactionSelect(index)}
            >
              <div><strong>De:</strong> {tx.sender}</div>
              <div><strong>Para:</strong> {tx.recipient}</div>
              <div><strong>Cantidad:</strong> {tx.amount} BBC</div>
              <div><strong>Comisión:</strong> {tx.fee} BBC</div>
              <div>
                <strong>Estado:</strong> 
                {selectedTransactions.includes(index) ? 'Seleccionada' : 'No seleccionada'}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default Mempool;