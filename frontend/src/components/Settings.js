import React, { useState, useEffect } from 'react';

const Settings = ({ onError }) => {
  const [difficulty, setDifficulty] = useState(4);

  // Cargar la dificultad actual al montar el componente
  useEffect(() => {
    fetchCurrentDifficulty();
  }, []);

  const fetchCurrentDifficulty = async () => {
    try {
      const response = await fetch('http://localhost:5000/settings/difficulty');
      if (!response.ok) {
        throw new Error('Failed to fetch difficulty');
      }
      const data = await response.json();
      setDifficulty(data.difficulty);
    } catch (error) {
      onError('Error fetching mining difficulty');
    }
  };

  const handleDifficultyChange = async (newDifficulty) => {
    try {
      const response = await fetch('http://localhost:5000/settings/difficulty', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ difficulty: newDifficulty }),
      });

      if (!response.ok) {
        throw new Error('Failed to update difficulty');
      }

      setDifficulty(newDifficulty);
    } catch (error) {
      onError('Error updating mining difficulty');
    }
  };

  return (
    <div className="settings-container">
      <h2>Configuración</h2>
      <div className="difficulty-settings">
        <h3>Dificultad de Minado</h3>
        <p>Número de ceros requeridos: {difficulty}</p>
        <div className="difficulty-buttons">
          {[0, 1, 2, 3, 4].map((level) => (
            <button
              key={level}
              onClick={() => handleDifficultyChange(level)}
              className={`difficulty-button ${difficulty === level ? 'active' : ''}`}
            >
              {level}
            </button>
          ))}
        </div>
      </div>
    </div>
  );
};

export default Settings;