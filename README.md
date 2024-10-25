# 🔗 Simulador de Blockchain

Un simulador de blockchain educativo que implementa los conceptos fundamentales de la tecnología blockchain, incluyendo minería, transacciones, firma digital y prueba de trabajo. Desarrollado con Python (Flask) en el backend y React en el frontend.

## ⭐ Características

- Simulación completa de una blockchain con prueba de trabajo (PoW)
- Billeteras digitales con pares de claves criptográficas (pública/privada)
- Sistema de transacciones con firmas digitales
- Mempool para transacciones pendientes
- Minería de bloques con recompensas y comisiones
- Interfaz web interactiva para visualización de la cadena
- Verificación de integridad de bloques y transacciones
- Encriptación AES para claves privadas

## 🔧 Requisitos Previos

- Python 3.8 o superior
- Node.js 14 o superior
- npm 6 o superior

## 📁 Estructura del Proyecto

```
blockchain-simulator/
├── backend/
│   ├── app.py                 # Servidor Flask y endpoints API
│   ├── blockchain.py          # Lógica principal de la blockchain
│   └── requirements.txt       # Dependencias de Python
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Block.js/.css       # Componente de bloque individual
│   │   │   ├── Blockchain.js/.css  # Visualización de la cadena
│   │   │   ├── Mempool.js/.css     # Gestión de transacciones pendientes
│   │   │   ├── Transaction.js      # Formulario de transacciones
│   │   │   ├── VerifyBlock.js/.css # Verificación de bloques
│   │   │   └── Wallet.js/.css      # Gestión de billetera
│   │   ├── App.js                  # Componente principal
│   │   └── App.css                 # Estilos principales
│   └── package.json                # Dependencias de Node.js
└── README.md
```

## 🚀 Instalación y Configuración

### Backend

1. Crear y activar entorno virtual:
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate

# Linux/macOS
source venv/bin/activate
```

2. Instalar dependencias:
```bash
pip install -r requirements.txt
```

### Frontend

1. Instalar dependencias:
```bash
cd frontend
npm install
```

## 🎮 Ejecución

1. Iniciar el backend (en una terminal):
```bash
cd backend
source venv/bin/activate  # o venv\Scripts\activate en Windows
python app.py
```

2. Iniciar el frontend (en otra terminal):
```bash
cd frontend
npm start
```

3. Abrir http://localhost:3000 en el navegador

## 💡 Guía de Uso

### 👛 Billetera Digital
- Las billeteras se generan automáticamente al iniciar
- Reciben 10 BBC (BlockchainCoin) iniciales
- La clave privada está encriptada (contraseña por defecto: 1234)

### 💸 Transacciones
1. Ir a la pestaña "Transacción"
2. Ingresar la dirección del destinatario
3. Especificar cantidad y comisión
4. Usar la clave privada para firmar

### ⛏️ Minería
1. Acceder a la pestaña "Mempool"
2. Seleccionar hasta 3 transacciones para incluir en el bloque
3. Hacer clic en "Minar" para iniciar el proceso
4. La recompensa incluye comisiones + recompensa base

## 📚 Tecnologías Utilizadas

### Backend
- Flask (API REST)
- PyCrypto (Criptografía)
- ECDSA (Firmas digitales)

### Frontend
- React
- CSS3
- Fetch API