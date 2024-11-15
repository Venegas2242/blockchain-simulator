# 🔗 Simulador de Blockchain

Un simulador de blockchain educativo que implementa los conceptos fundamentales de la tecnología blockchain, incluyendo minería, transacciones, firma digital y prueba de trabajo. Desarrollado con Python (Flask) en el backend y React en el frontend.

## ⭐ Características Principales

### 🌐 Funcionalidades Core
- Generación de claves siguiendo el estándar BIP39 (frases mnemotécnicas)
- Sistema completo de Proof of Work (PoW) para minería de bloques
- Transacciones seguras con firmas digitales ECDSA
- Mempool para gestión de transacciones pendientes
- Smart Contract de Escrow implementado

### 🔐 Seguridad
- Generación de claves privadas mediante derivación BIP32
- Cifrado AES-256-CBC para protección de claves privadas
- Verificación completa de integridad en la cadena
- Sistema de firmas digitales con curva secp256k1

### 💼 Gestión de Wallets
- Generación automática de carteras con frases mnemónicas
- Balance inicial de 10 BBC (BlockchainCoin)
- Sistema de cifrado de claves privadas con contraseña
- Derivación segura de claves usando PBKDF2

## 🛠️ Requisitos Técnicos

### Backend
- Python 3.8+
- Flask
- PyCrypto
- ECDSA
- Hashlib
- HMAC

### Frontend
- Node.js 14+
- React 18+
- npm 6+

## 📁 Estructura del Proyecto

```
blockchain-simulator/
├── backend/
│   ├── app.py                 # Servidor Flask y endpoints API
│   ├── blockchain.py          # Lógica principal de la blockchain
|   ├── wallet_generator.py     # Generación de carteras BIP39
│   └── requirements.txt       # Dependencias de Python
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Block.js/.css       # Componente de bloque individual
│   │   │   ├── Blockchain.js/.css  # Visualización de la cadena
|   |   |   ├── Escrow.js/.css      # Smart Contract
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

## 🔍 Guía Detallada

### 📱 Proceso de Generación de Wallet

1. **Generación de Entropía**
   - 16 bytes de entropía segura
   - Uso de secrets para aleatoriedad criptográfica

2. **Creación de Frase Mnemónica**
   - Implementación BIP39
   - 12 palabras de respaldo
   - Checksum SHA256 para verificación

3. **Derivación de Claves**
   - Semilla generada con PBKDF2
   - Derivación BIP32 para clave maestra
   - Generación de par de claves ECDSA

### 💸 Sistema de Transacciones

1. **Creación**
   - Especificación de destinatario
   - Monto y comisión de minería
   - Firma digital ECDSA

2. **Verificación**
   - Validación de firmas
   - Comprobación de balances
   - Verificación de nonce

3. **Minería**
   - Selección de transacciones
   - Proof of Work (4 ceros)
   - Recompensas y comisiones

### 🔒 Smart Contract de Escrow

1. **Funcionalidades**
   - Custodia segura de fondos
   - Sistema de confirmaciones
   - Gestión de disputas
   - Comisiones automáticas

2. **Comisiones**
   - Mediador: 1%
   - Minería: 0.1% × 3
   - Total: ~1.3%

## 📚 Referencias

- [BIP39 - Mnemonic Code](https://github.com/bitcoin/bips/blob/master/bip-0039.mediawiki)
- [BIP32 - HD Wallets](https://github.com/bitcoin/bips/blob/master/bip-0032.mediawiki)
- [Curva secp256k1](https://en.bitcoin.it/wiki/Secp256k1)