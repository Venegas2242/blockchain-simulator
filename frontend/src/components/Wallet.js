import React, { useState } from 'react';
import './Wallet.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Wallet = ({ wallet, balance, onNewAddress }) => {
 const [showPublicKey, setShowPublicKey] = useState(false);
 const [password, setPassword] = useState('');
 const [showPasswordInput, setShowPasswordInput] = useState(false);
 const addresses = wallet.addresses || [wallet.address];

 const truncateKey = (key) => key ? `${key.substr(0, 16)}...${key.substr(-8)}` : '';

 const copyToClipboard = (text) => {
   navigator.clipboard.writeText(text)
     .then(() => alert('Copied to clipboard!'));
 };

 const generateNewAddress = async () => {
   try {
     const response = await fetch(`${API_URL}/generate_address`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({ public_key: wallet.public_key })
     });

     if (!response.ok) throw new Error('Failed to generate address');
     const data = await response.json();
     
     if (onNewAddress) {
       onNewAddress(data.address);
     }
   } catch (error) {
     alert('Error generating new address');
   }
 };

 const handleDecryptPrivateKey = async () => {
   try {
     const response = await fetch(`${API_URL}/decrypt_private_key`, {
       method: 'POST',
       headers: { 'Content-Type': 'application/json' },
       body: JSON.stringify({
         encrypted_private_key: wallet.encrypted_key,
         password: password
       })
     });

     if (!response.ok) throw new Error('Decryption failed');
     
     const data = await response.json();
     copyToClipboard(data.decrypted_private_key);
     setShowPasswordInput(false);
     setPassword('');
   } catch (error) {
     alert('Failed to decrypt private key');
   }
 };

 if (!wallet) return <div>Loading wallet...</div>;

 return (
   <div className="wallet">
     <div className="wallet-info">
       <h3>Información de Wallet</h3>
       <p>
         <strong>Llave Pública: </strong>
         {showPublicKey ? (
           <>
             {truncateKey(wallet.public_key)}
             <button onClick={() => copyToClipboard(wallet.public_key)}>Copiar</button>
           </>
         ) : (
           <button onClick={() => setShowPublicKey(true)}>Mostrar llave pública</button>
         )}
       </p>
       <p>
         <strong>Llave Privada (Cifrada):</strong> {truncateKey(wallet.encrypted_key)}
         <button onClick={() => setShowPasswordInput(true)}>Decifrar y copiar</button>
         <button onClick={() => copyToClipboard(wallet.encrypted_key)}>Copiar encriptada</button>
       </p>
       {showPasswordInput && (
         <div className="decrypt-input">
           <input
             type="password"
             value={password}
             onChange={(e) => setPassword(e.target.value)}
             placeholder="Enter password (1234)"
           />
           <button onClick={handleDecryptPrivateKey}>Submit</button>
         </div>
       )}
     </div>

     <div className="addresses-section">
       <h3>
         Direcciones 
         <button onClick={generateNewAddress} className="new-address-btn">
           + Nueva Dirección
         </button>
       </h3>
       <div className="addresses-list">
         {addresses.map((addr, index) => (
           <div key={addr} className="address-item">
             <span className="address-index">{index + 1}.</span>
             <span className="address-value">{truncateKey(addr)}</span>
             <button onClick={() => copyToClipboard(addr)}>Copiar</button>
           </div>
         ))}
       </div>
       <p className="balance-info">
         <strong>Balance Total:</strong> {balance} BBC
       </p>
     </div>
   </div>
 );
};

export default Wallet;