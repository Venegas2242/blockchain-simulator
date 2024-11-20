# 🔗 Simulador de Blockchain

Un simulador de blockchain educativo que implementa los conceptos fundamentales de la tecnología blockchain, incluyendo minería, transacciones, firma digital y prueba de trabajo. Desarrollado con Python (Flask) en el backend y React en el frontend.

## ⭐ Características Principales

### 🌐 Funcionalidades Core
- Generación de claves siguiendo el estándar BIP39 (frases mnemotécnicas)
- Sistema completo de Proof of Work (PoW) para minería de bloques
- Transacciones seguras con firmas digitales ECDSA
- Mempool para gestión de transacciones pendientes
- Smart Contract de Escrow implementado
- Dificultad de minado ajustable (0-4 ceros)

### 🔐 Seguridad
- Generación de claves privadas mediante derivación BIP32
- Cifrado AES-256-CBC para protección de claves privadas
- Verificación completa de integridad en la cadena
- Sistema de firmas digitales con curva secp256k1
- Validación de transacciones y bloques

### 💼 Gestión de Wallets
- Generación automática de carteras con frases mnemónicas
- Balance inicial de 10 BBC
- Sistema de cifrado de claves privadas con contraseña
- Derivación segura de claves usando PBKDF2
- Soporte para múltiples direcciones por wallet
- Sistema de login mediante clave privada cifrada

### 🤝 Smart Contract de Custodia
- Sistema de depósito seguro entre compradores y vendedores
- Gestión automática de estados del contrato
- Sistema de disputas y reembolsos
- Verificación de firmas para todas las operaciones

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
│   ├── app.py                      # Servidor Flask y endpoints API
│   ├── blockchain.py               # Lógica principal de la blockchain
│   ├── crypto_utils.py             # Utilidades criptográficas
│   ├── secure_escrow_contract.py   # Implementación del smart contract
│   ├── wallet_generator.py         # Generación de carteras BIP39
│   └── requirements.txt            # Dependencias de Python
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Block.js/.css          # Componente de bloque individual
│   │   │   ├── Blockchain.js/.css     # Visualización de la cadena
│   │   │   ├── Escrow.js/.css         # Smart Contract UI
│   │   │   ├── Mempool.js/.css        # Gestión de transacciones pendientes
│   │   │   ├── MiningProgress.js      # Visualización de progreso de minado
│   │   │   ├── Settings.js            # Configuración del simulador
│   │   │   ├── Transaction.js         # Formulario de transacciones
│   │   │   ├── VerifyBlock.js/.css    # Verificación de bloques
│   │   │   └── Wallet.js/.css         # Gestión de billetera
│   │   ├── App.js                     # Componente principal
│   │   ├── App.css                    # Estilos principales
│   │   └── index.js                   # Punto de entrada React
│   ├── .env                           # Variables de entorno
│   └── package.json                   # Dependencias de Node.js
├── blockchain-analysis.md             # Análisis técnico detallado
└── README.md                          # Documentación principal
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
## 💡 Uso

### Generación de Wallet
1. Clic en "Nueva Wallet" o "Iniciar Sesión"
2. Para nueva wallet: guarda la clave privada cifrada
3. Para login: usa la clave privada cifrada guardada

### Envío de Transacciones
1. Navega a la pestaña "Transacción"
2. Ingresa dirección destino, cantidad y comisión
3. Firma con tu clave privada
4. La transacción aparecerá en la mempool

### Minado de Bloques
1. Ve a la pestaña "Mempool"
2. Selecciona hasta 3 transacciones
3. Inicia el minado
4. Observa el progreso en tiempo real

### Smart Contract de Custodia
1. Accede a la pestaña "Smart Contract"
2. Como comprador: crea nuevo acuerdo
3. Como vendedor: confirma participación
4. Sigue el flujo de envío y confirmación

### Configuración
1. Ajusta la dificultad de minado (0-4 ceros)
2. Verifica bloques y transacciones
3. Gestiona múltiples direcciones

## 🔍 Análisis y Documentación

Para un análisis detallado de la implementación, arquitectura y características técnicas, consulta:
[BLOCKCHAIN-ANALYSIS.md](BLOCKCHAIN-ANALYSIS.md)

## 📚 Referencias

[Tus referencias actuales]

---
<div align="center">

![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-000000?style=for-the-badge&logo=flask&logoColor=white)
![React](https://img.shields.io/badge/React-20232A?style=for-the-badge&logo=react&logoColor=61DAFB)
![Node.js](https://img.shields.io/badge/Node.js-43853D?style=for-the-badge&logo=node.js&logoColor=white)

</div>
