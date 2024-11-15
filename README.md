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
- La clave privada está encriptada con AES-256 en modo CBC
- Contraseña por defecto: 1234

### 💸 Transacciones
1. Ir a la pestaña "Transacción"
2. Ingresar la dirección del destinatario
3. Especificar cantidad y comisión
4. Usar la clave privada para firmar
5. La transacción se añade a la mempool

### ⛏️ Minería
1. Acceder a la pestaña "Mempool"
2. Seleccionar hasta 3 transacciones para incluir en el bloque
3. La recompensa incluye:
    - Recompensa base (10 BBC)
    - Comisiones de transacciones
    - Halving cada 2 bloques  

## 🔒 Seguridad

### Generación de Claves
- ECDSA con curva SECP256k1 (misma que Bitcoin)
- Direcciones generadas con RIPEMD160(SHA256(public_key))
- Claves privadas cifradas con:
    - PBKDF2 para derivación de clave
    - AES-256-CBC para cifrado
    - Salt aleatorio de 16 bytes
    - IV único por cifrado

### Protección contra Doble Gasto
- Verificación de balance considerando transacciones en mempool
- Sistema de firmas digitales ECDSA
- Verificación de transacciones antes del minado

## Integridad de la Cadena
- Hash SHA256 para bloques
- Merkle Tree para transacciones
- Proof of Work con dificultad de 4 ceros
- Validación de cadena completa

### 📜 Smart Contract (Escrow)

El simulador incluye un contrato inteligente de custodia (escrow) que actúa como intermediario confiable entre compradores y vendedores.

#### 🔄 Flujo del Smart Contract

1. **Creación del Acuerdo**
   ```
   Comprador ----[BBC + Comisiones]----> Smart Contract
   ```
   - El comprador envía:
     * Monto principal (para el vendedor)
     * Comisión del mediador (1%)
     * Comisión de minería inicial (0.1%)
     * Comisiones para transacciones finales (0.1% × 2)

2. **Estados del Contrato**
   ```
   [PENDING_SELLER_CONFIRMATION] -> [AWAITING_SHIPMENT] -> [SHIPPED] -> [COMPLETED]
   ```
   - PENDING_SELLER_CONFIRMATION: Esperando que el vendedor acepte
   - AWAITING_SHIPMENT: Vendedor aceptó, pendiente de envío
   - SHIPPED: Producto enviado, esperando confirmación
   - COMPLETED: Transacción finalizada

3. **Liberación de Fondos**
   ```
   Smart Contract ----[BBC]--------> Vendedor
                 ----[Comisión]----> Mediador
   ```

#### 💰 Estructura de Comisiones

- **Comisión del Mediador**: 1% del monto principal
  * Para resolución de disputas y mantenimiento
  * Pagada por el comprador
  * Liberada al completar la transacción

- **Comisiones de Minería**:
  * Transacción inicial: 0.1% (comprador al contrato)
  * Transacción final al vendedor: 0.1%
  * Transacción final al mediador: 0.1%

#### 🔐 Seguridad del Contrato

- **Fondos Bloqueados**
  * Retenidos por el contrato hasta confirmación
  * No pueden ser retirados sin consenso
  * Sistema de timeouts para protección

- **Verificación de Transacciones**
  * Firma especial 'VALID' para transacciones del contrato
  * Validación de estados y permisos
  * Comprobación de balances y fondos bloqueados

#### 📋 Ejemplo de Uso

1. **Crear Acuerdo**
   ```javascript
   // Ejemplo con monto de 100 BBC
   Monto principal: 100 BBC
   Comisión mediador: 1 BBC (1%)
   Comisión minería inicial: 0.1 BBC (0.1%)
   Comisiones finales: 0.2 BBC (0.1% × 2)
   Total a pagar: 101.3 BBC
   ```

2. **Confirmaciones**
   ```
   Vendedor: Acepta participación
   Vendedor: Confirma envío + tracking
   Comprador: Confirma recepción
   ```

3. **Distribución Final**
   ```
   Vendedor recibe: 100 BBC
   Mediador recibe: 1 BBC
   Mineros reciben: 0.1 BBC + 0.1 BBC + 0.1 BBC
   ```

#### 🛠️ Implementación Técnica

```python
class SecureEscrowContract:
    def __init__(self):
        self.MEDIATOR_FEE = 0.01        # 1% para mediador
        self.INITIAL_MINING_FEE = 0.001  # 0.1% minería inicial
        self.RELEASE_MINING_FEE = 0.001  # 0.1% por liberación
```

#### 🔍 Verificación de Transacciones

1. **Transacciones del Contrato**
   - Identificadas por type: 'contract_transfer'
   - Firma especial: 'VALID'
   - No requieren llave pública

2. **Verificación en Bloque**
   ```python
   if transaction.get('type') == 'contract_transfer':
       # Verificar remitente es el contrato
       # Verificar destinatario válido
       # Verificar firma especial
   ```

#### ⚠️ Manejo de Disputas

- Sistema de timeouts para protección
- Reembolso automático si no hay confirmación
- Mediador puede intervenir en disputas
- Periodo de resolución definido en bloques

#### 🎯 Beneficios

1. **Seguridad**
   - Fondos bloqueados hasta confirmación
   - Verificación en múltiples etapas
   - Sistema de comisiones transparente

2. **Transparencia**
   - Estados claros y definidos
   - Comisiones conocidas de antemano
   - Transacciones verificables en la blockchain

3. **Automatización**
   - Liberación automática de fondos
   - Manejo de timeouts
   - Procesamiento de comisiones

## 📚 Tecnologías Utilizadas

### Backend
- Flask (API REST)
- PyCrypto (Criptografía)
- ECDSA (Firmas digitales)

### Frontend
- React
- CSS3
- Fetch API