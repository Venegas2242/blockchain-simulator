import React, { useState, useEffect } from 'react';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const MiningProcess = ({ isVisible, onMiningComplete, selectedTransactions, wallet }) => {
  const [nonce, setNonce] = useState(0);
  const [currentHash, setCurrentHash] = useState('');
  const [isMining, setIsMining] = useState(false);

  useEffect(() => {
    let isCancelled = false;
    let timeoutId = null;

    const mineBlock = async () => {
      if (!isVisible || !wallet || selectedTransactions.length === 0) return;

      try {
        const response = await fetch(`${API_URL}/mine/progress`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            miner_address: wallet.address,
            selected_transactions: selectedTransactions,
          }),
        });

        if (!response.ok) throw new Error('Mining request failed');
        const data = await response.json();

        if (!isCancelled) {
          setNonce(data.nonce);
          setCurrentHash(data.hash);

          if (data.found) {
            setIsMining(false);
            if (onMiningComplete) {
              onMiningComplete(data.nonce, data.hash);
            }
          } else {
            timeoutId = setTimeout(mineBlock, 100);
          }
        }
      } catch (error) {
        console.error('Mining error:', error);
        setIsMining(false);
      }
    };

    if (isVisible && !isMining) {
      setIsMining(true);
      mineBlock();
    }

    return () => {
      isCancelled = true;
      if (timeoutId) clearTimeout(timeoutId);
    };
  }, [isVisible, wallet, selectedTransactions, onMiningComplete, isMining]);

  if (!isVisible) return null;

  return (
    <div className="min-w-full p-4 bg-gray-100 rounded-lg shadow-md">
      <div className="space-y-4">
        <h3 className="text-lg font-semibold text-gray-800">
          Proceso de Minado {isMining ? '⚒️' : '✅'}
        </h3>
        
        <div className="space-y-2">
          <div className="flex items-center space-x-2">
            <span className="font-medium text-gray-700">Nonce actual:</span>
            <span className="font-mono bg-white px-2 py-1 rounded border">
              {nonce}
            </span>
          </div>
          
          <div className="flex items-center space-x-2">
            <span className="font-medium text-gray-700">Hash actual:</span>
            <span className="font-mono bg-white px-2 py-1 rounded border break-all">
              {currentHash}
            </span>
          </div>
        </div>

        {!isMining && currentHash.startsWith('0000') && (
          <div className="bg-green-100 border-l-4 border-green-500 p-4">
            <p className="text-green-700">
              ¡Hash válido encontrado! Cumple con la dificultad requerida (4 ceros iniciales)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MiningProcess;