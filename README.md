# Blockchain Simulator

Este proyecto es un simulador de blockchain que incluye un backend en Python y un frontend en React. Simula las operaciones básicas de una blockchain, incluyendo minería de bloques, transacciones, y visualización de la cadena.

## Características

- Simulación de blockchain con prueba de trabajo (PoW)
- Generación de wallets con claves públicas y privadas
- Realización de transacciones entre wallets
- Minería de bloques con recompensa
- Visualización interactiva de la cadena de bloques
- Verificación de integridad de bloques (hash previo y prueba de trabajo)

## Requisitos previos

- Python 3.8+
- Node.js 14+
- npm 6+

## Configuración

### Backend

1. Navega al directorio del backend:
   ```
   cd blockchain-simulator/backend
   ```

2. Crea un entorno virtual:
   ```
   python -m venv venv
   ```

3. Activa el entorno virtual:
   - En Windows:
     ```
     venv\Scripts\activate
     ```
   - En macOS y Linux:
     ```
     source venv/bin/activate
     ```

4. Instala las dependencias:
   ```
   pip install -r requirements.txt
   ```

### Frontend

1. Navega al directorio del frontend:
   ```
   cd blockchain-simulator/frontend
   ```

2. Instala las dependencias:
   ```
   npm install
   ```

## Ejecución

1. Inicia el backend:
   ```
   cd blockchain-simulator/backend
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   python app.py
   ```

2. En otra terminal, inicia el frontend:
   ```
   cd blockchain-simulator/frontend
   npm start
   ```

3. Abre un navegador y ve a `http://localhost:3000` para ver la aplicación.

## Estructura del proyecto

```
blockchain-simulator/
├── backend/
│   ├── app.py
│   ├── blockchain.py
│   └── requirements.txt
├── frontend/
│   ├── public/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Block.js
│   │   │   ├── Blockchain.js
│   │   │   ├── Transaction.js
│   │   │   └── Wallet.js
│   │   ├── App.js
│   │   └── index.js
│   ├── package.json
│   └── .env
└── README.md
```
