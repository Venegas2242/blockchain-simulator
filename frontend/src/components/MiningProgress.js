import React from 'react';

const MiningProgress = ({ isVisible, progress }) => {
  if (!isVisible) return null;

  // Mostrar el proceso de minado si está en progreso y no se ha encontrado un hash válido
  const showMiningProcess = progress.status === 'mining' || progress.status === 'starting';
  const hasValidHash = progress.final_hash?.startsWith('0000') || progress.hash?.startsWith('0000');

  return (
    <div className="w-full max-w-2xl mx-auto p-6 bg-white rounded-xl shadow-lg">
      {/* Título con animación durante el minado */}
      <div className="flex items-center justify-between mb-6 border-b pb-4">
        <h3 className="text-2xl font-bold text-gray-800 flex items-center gap-3">
          Proceso de Minado
          {showMiningProcess && !hasValidHash && (
            <span className="animate-pulse text-yellow-500">⚒️</span>
          )}
          {hasValidHash && (
            <span className="text-green-500">✅</span>
          )}
        </h3>
      </div>

      {/* Contenido principal */}
      <div className="space-y-6">
        {/* Mostrar proceso de minado actual */}
        {showMiningProcess && !hasValidHash && (
          <div className="bg-blue-50 p-4 rounded-lg border-l-4 border-blue-500">
            <div className="text-lg text-blue-800 font-semibold">
              Buscando hash válido...
            </div>
            <div className="mt-2 font-mono text-sm">
              <div>Nonce actual: {progress.nonce}</div>
              {progress.hash && (
                <div className="mt-1 break-all">
                  Hash actual: {progress.hash}
                </div>
              )}
            </div>
          </div>
        )}

        {/* Mostrar resultado final cuando se encuentra un hash válido */}
        {hasValidHash && (
          <div className="bg-green-50 p-6 rounded-lg border-l-4 border-green-500 animate-fadeIn">
            <div className="space-y-4">
              <div className="flex items-center gap-2 text-green-800">
                <span className="text-2xl">🎉</span>
                <h4 className="text-xl font-bold">¡Hash válido encontrado!</h4>
              </div>
              
              <div className="bg-white p-4 rounded-lg shadow-inner">
                <div className="grid gap-3">
                  <div>
                    <span className="font-bold text-gray-700">Nonce encontrado:</span>
                    <span className="ml-2 font-mono text-green-600">
                      {progress.final_nonce || progress.nonce}
                    </span>
                  </div>
                  
                  <div>
                    <span className="font-bold text-gray-700">Hash válido:</span>
                    <div className="mt-1 font-mono text-sm bg-gray-50 p-3 rounded-md break-all text-green-700 border border-green-100">
                      {progress.final_hash || progress.hash}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Mostrar error si ocurre */}
        {progress.status === 'error' && (
          <div className="bg-red-50 p-4 rounded-lg border-l-4 border-red-500">
            <p className="text-red-700 font-semibold">
              Error durante el minado: {progress.error}
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default MiningProgress;