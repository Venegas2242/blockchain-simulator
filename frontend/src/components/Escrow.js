import React, { useState, useEffect } from 'react';
import './Escrow.css';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000';

const Escrow = ({ wallet, onError, onBalanceUpdate }) => {
    const [tab, setTab] = useState('create');
    const [agreements, setAgreements] = useState([]);
    const [loading, setLoading] = useState(false);
    const [privateKey, setPrivateKey] = useState('');
    const [trackingInfo, setTrackingInfo] = useState('');
    const [disputeReason, setDisputeReason] = useState('');
    const [formData, setFormData] = useState({
        seller: '',
        amount: '',
        description: ''
    });

    useEffect(() => {
        if (wallet?.address) {
            fetchAgreements();
        }
    }, [wallet]);

    const fetchAgreements = async () => {
        try {
            const response = await fetch(`${API_URL}/escrow/agreements/${wallet.address}`);
            const data = await response.json();
            if (response.ok) {
                setAgreements(data.agreements);
            } else {
                onError(data.error);
            }
        } catch (err) {
            onError('Error al cargar acuerdos');
        }
    };

    const handleCreateEscrow = async (e) => {
        e.preventDefault();
        setLoading(true);
        if (onError) onError('');

        try {
            const response = await fetch(`${API_URL}/escrow/create`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    buyer: wallet.address,
                    ...formData,
                    amount: parseFloat(formData.amount),
                    privateKey: privateKey
                }),
            });

            const data = await response.json();
            if (response.ok) {
                alert('Acuerdo creado exitosamente!');
                setFormData({ seller: '', amount: '', description: '' });
                setPrivateKey('');
                fetchAgreements();
                if (onBalanceUpdate) onBalanceUpdate();
            } else {
                if (onError) onError(data.error);
            }
        } catch (err) {
            if (onError) onError('Error al crear el acuerdo');
        } finally {
            setLoading(false);
        }
    };

    const handleConfirmSeller = async (agreementId) => {
        try {
            const response = await fetch(`${API_URL}/escrow/confirm-seller`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agreement_id: agreementId,
                    seller: wallet.address
                }),
            });

            const data = await response.json();
            if (response.ok) {
                alert('Participación confirmada exitosamente!');
                fetchAgreements();
            } else {
                if (onError) onError(data.error);
            }
        } catch (err) {
            if (onError) onError('Error al confirmar participación');
        }
    };

    const handleConfirmShipment = async (agreementId) => {
        try {
            const response = await fetch(`${API_URL}/escrow/confirm-shipment`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agreement_id: agreementId,
                    seller: wallet.address,
                    tracking_info: trackingInfo
                }),
            });

            const data = await response.json();
            if (response.ok) {
                alert('Envío confirmado exitosamente!');
                setTrackingInfo('');
                fetchAgreements();
            } else {
                if (onError) onError(data.error);
            }
        } catch (err) {
            if (onError) onError('Error al confirmar envío');
        }
    };

    const handleConfirmDelivery = async (agreementId) => {
        try {
            const response = await fetch(`${API_URL}/escrow/confirm-delivery`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agreement_id: agreementId,
                    buyer: wallet.address
                }),
            });

            const data = await response.json();
            if (response.ok) {
                alert('Entrega confirmada exitosamente!');
                fetchAgreements();
                if (onBalanceUpdate) onBalanceUpdate();
            } else {
                if (onError) onError(data.error);
            }
        } catch (err) {
            if (onError) onError('Error al confirmar entrega');
        }
    };

    const handleOpenDispute = async (agreementId) => {
        try {
            const response = await fetch(`${API_URL}/escrow/open-dispute`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    agreement_id: agreementId,
                    buyer: wallet.address,  // Cambiado de 'party' a 'buyer'
                    reason: disputeReason
                }),
            });
    
            const data = await response.json();
            if (response.ok) {
                alert('Disputa abierta y reembolso iniciado exitosamente!');  // Mensaje actualizado
                setDisputeReason('');
                fetchAgreements();
                if (onBalanceUpdate) onBalanceUpdate();  // Actualizar balance después del reembolso
            } else {
                if (onError) onError(data.error);
            }
        } catch (err) {
            if (onError) onError('Error al abrir disputa');
        }
    };

    return (
        <div className="escrow-container">
            <div className="tabs">
                <button 
                    className={tab === 'create' ? 'active' : ''} 
                    onClick={() => setTab('create')}
                >
                    Crear Acuerdo
                </button>
                <button 
                    className={tab === 'list' ? 'active' : ''} 
                    onClick={() => setTab('list')}
                >
                    Mis Acuerdos
                </button>
            </div>

            {tab === 'create' && (
                <div className="create-form">
                    <h3>Crear Nuevo Acuerdo de Custodia</h3>
                    <form onSubmit={handleCreateEscrow}>
                        <div>
                            <label>Dirección del Vendedor:</label>
                            <input
                                type="text"
                                value={formData.seller}
                                onChange={e => setFormData({...formData, seller: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <label>Cantidad (BBC):</label>
                            <input
                                type="number"
                                step="0.01"
                                value={formData.amount}
                                onChange={e => setFormData({...formData, amount: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <label>Descripción:</label>
                            <textarea
                                value={formData.description}
                                onChange={e => setFormData({...formData, description: e.target.value})}
                                required
                            />
                        </div>
                        <div>
                            <label>Llave Privada:</label>
                            <input
                                type="password"
                                value={privateKey}
                                onChange={e => setPrivateKey(e.target.value)}
                                required
                            />
                        </div>
                        <button type="submit" disabled={loading}>
                            {loading ? 'Creando...' : 'Crear Acuerdo'}
                        </button>
                    </form>
                </div>
            )}

            {tab === 'list' && (
                <div className="agreements-list">
                    <h3>Mis Acuerdos</h3>
                    {agreements.map(agreement => (
                        <div key={agreement.id} className="agreement-card">
                            <h4>Acuerdo #{agreement.id.substring(0, 8)}</h4>
                            <div className="agreement-details">
                                <p><strong>Estado:</strong> {agreement.status}</p>
                                <p><strong>Descripción:</strong> {agreement.description}</p>
                                <p><strong>Cantidad:</strong> {agreement.amount} BBC</p>
                                <p><strong>Comprador:</strong> {agreement.buyer}</p>
                                <p><strong>Vendedor:</strong> {agreement.seller}</p>
                                {agreement.tracking_info && (
                                    <p><strong>Tracking:</strong> {agreement.tracking_info}</p>
                                )}
                            </div>

                            <div className="agreement-actions">
                                {agreement.seller === wallet.address && 
                                 agreement.status === 'PENDING_SELLER_CONFIRMATION' && (
                                    <button onClick={() => handleConfirmSeller(agreement.id)}>
                                        Confirmar Participación
                                    </button>
                                )}

                                {agreement.seller === wallet.address && 
                                 agreement.status === 'AWAITING_SHIPMENT' && (
                                    <div>
                                        <input
                                            type="text"
                                            placeholder="Información de tracking"
                                            value={trackingInfo}
                                            onChange={e => setTrackingInfo(e.target.value)}
                                        />
                                        <button onClick={() => handleConfirmShipment(agreement.id)}>
                                            Confirmar Envío
                                        </button>
                                    </div>
                                )}

                                {agreement.buyer === wallet.address && 
                                 agreement.status === 'SHIPPED' && (
                                    <button onClick={() => handleConfirmDelivery(agreement.id)}>
                                        Confirmar Recepción
                                    </button>
                                )}

                                {agreement.buyer === wallet.address && 
                                ['PENDING_SELLER_CONFIRMATION', 'SHIPPED', 'AWAITING_SHIPMENT'].includes(agreement.status) && (
                                    <div>
                                        <textarea
                                            placeholder="Razón de la disputa"
                                            value={disputeReason}
                                            onChange={e => setDisputeReason(e.target.value)}
                                        />
                                        <button 
                                            onClick={() => handleOpenDispute(agreement.id)}
                                            className="dispute-button"  // Opcional: para darle un estilo distintivo
                                        >
                                            Solicitar Reembolso
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default Escrow;