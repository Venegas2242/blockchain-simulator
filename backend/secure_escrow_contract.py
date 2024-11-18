# secure_escrow_contract.py

from time import time

class SecureEscrowContract:
    def __init__(self, blockchain):
        self.blockchain = blockchain
        self.address = "escrow_contract"
        self.state = {
            'agreements': {},      # Detalles de acuerdos
            'locked_funds': {},    # Fondos bloqueados
        }
        
        # Comisiones del contrato
        self.MEDIATOR_FEE = 0.01        # 1% para el mediador
        self.INITIAL_MINING_FEE = 0.001  # 0.1% para el minero en la transacción inicial
        self.RELEASE_MINING_FEE = 0.001  # 0.1% para el minero en cada liberación de fondos

    def process_escrow_transaction(self, transaction):
        """Procesa una transacción del contrato cuando es minada"""
        # Solo procesar si es una transacción del smart contract
        if transaction.get('sender') == self.address or transaction.get('recipient') == self.address:
            # Actualizar locked_funds según tipo de transacción
            if transaction['recipient'] == self.address:
                # Fondos recibidos por el contrato
                sender = transaction['sender']
                if sender not in self.state['locked_funds']:
                    self.state['locked_funds'][sender] = 0
                self.state['locked_funds'][sender] += transaction['amount']
            
            elif transaction['sender'] == self.address:
                # Fondos liberados por el contrato
                for agreement in self.state['agreements'].values():
                    if agreement['seller'] == transaction['recipient']:
                        buyer = agreement['buyer']
                        if buyer in self.state['locked_funds']:
                            self.state['locked_funds'][buyer] -= transaction['amount']
                            if self.state['locked_funds'][buyer] <= 0:
                                del self.state['locked_funds'][buyer]

    def create_agreement(self, agreement_id: str, buyer: str, seller: str, amount: float, description: str, buyer_private_key: str):
        """Crea un nuevo acuerdo donde el comprador paga todas las comisiones"""
        
        # Calcular comisiones
        mediator_fee = amount * self.MEDIATOR_FEE
        initial_mining_fee = amount * self.INITIAL_MINING_FEE
        release_fees = self.RELEASE_MINING_FEE * 2
        
        total_amount = amount + mediator_fee + initial_mining_fee + release_fees
        
        # Verificar fondos suficientes
        if self.blockchain.get_balance(buyer) < total_amount:
            raise ValueError(f"Fondos insuficientes. Se requiere {total_amount} BBC")
        
        # Crear transacción de depósito
        transfer_transaction = {
            'sender': buyer,
            'recipient': self.address,
            'amount': amount + mediator_fee + release_fees,
            'fee': initial_mining_fee,
            'timestamp': time(),
            'type': 'escrow_deposit'
        }

        # Firmar y enviar a mempool
        signature = self.blockchain.sign_transaction(buyer_private_key, transfer_transaction)
        transfer_transaction['signature'] = signature.hex()
        self.blockchain.mempool.append(transfer_transaction)

        # Registrar acuerdo
        self.state['agreements'][agreement_id] = {
            'buyer': buyer,
            'seller': seller,
            'amount': amount,
            'mediator_fee': mediator_fee,
            'reserved_mining_fees': release_fees,
            'description': description,
            'status': 'PENDING_SELLER_CONFIRMATION',
            'shipped': False,
            'delivery_confirmed': False,
            'timestamp': time()
        }
        
        print(f"\n=== NUEVO ACUERDO CREADO ===")
        print(f"ID: {agreement_id}")
        print(f"Comprador: {buyer}")
        print(f"Vendedor: {seller}")
        print(f"Monto: {amount} BBC")
        print(f"Estado: PENDING_SELLER_CONFIRMATION")
        
        return agreement_id

    def confirm_seller_participation(self, agreement_id: str, seller: str):
        """Confirmación del vendedor para participar"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['seller'] != seller:
            raise ValueError("Solo el vendedor puede confirmar participación")
            
        if agreement['status'] != 'PENDING_SELLER_CONFIRMATION':
            raise ValueError("Estado inválido para confirmar participación")
            
        agreement['status'] = 'AWAITING_SHIPMENT'
        print(f"\n=== VENDEDOR CONFIRMÓ PARTICIPACIÓN ===")
        print(f"Acuerdo: {agreement_id}")
        print(f"Estado actualizado: AWAITING_SHIPMENT")
        return True

    def confirm_shipment(self, agreement_id: str, seller: str, tracking_info: str = None):
        """Confirma el envío del producto"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['seller'] != seller:
            raise ValueError("Solo el vendedor puede confirmar envío")
            
        if agreement['status'] != 'AWAITING_SHIPMENT':
            raise ValueError("Estado inválido para confirmar envío")
            
        agreement['shipped'] = True
        agreement['tracking_info'] = tracking_info
        agreement['status'] = 'SHIPPED'
        agreement['shipping_timestamp'] = time()
        
        print(f"\n=== ENVÍO CONFIRMADO ===")
        print(f"Acuerdo: {agreement_id}")
        print(f"Tracking: {tracking_info}")
        print(f"Estado actualizado: SHIPPED")
        return True

    def confirm_delivery(self, agreement_id: str, buyer: str):
        """Confirma la entrega y libera los fondos"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        if agreement['buyer'] != buyer:
            raise ValueError("Solo el comprador puede confirmar entrega")
        
        print(f"\n=== PROCESANDO CONFIRMACIÓN DE ENTREGA ===")
        print(f"Acuerdo: {agreement_id}")
        
        # Crear transacciones de pago
        current_time = time()
        mining_fee = self.RELEASE_MINING_FEE

        # Pago al vendedor
        transfer_to_seller = {
            'sender': self.address,
            'recipient': agreement['seller'],
            'amount': agreement['amount'],
            'fee': mining_fee,
            'timestamp': current_time,
            'type': 'contract_transfer',
            'signature': 'VALID'
        }

        # Pago al mediador
        mediator_fee_transaction = {
            'sender': self.address,
            'recipient': 'mediator',
            'amount': agreement['mediator_fee'],
            'fee': mining_fee,
            'timestamp': current_time,
            'type': 'contract_transfer',
            'signature': 'VALID'
        }

        self.blockchain.mempool.append(transfer_to_seller)
        self.blockchain.mempool.append(mediator_fee_transaction)
        
        agreement['status'] = 'COMPLETED'
        agreement['delivery_confirmed'] = True
        
        print(f"Pago enviado al vendedor: {agreement['amount']} BBC")
        print(f"Comisión al mediador: {agreement['mediator_fee']} BBC")
        print(f"Estado actualizado: COMPLETED")
        return True

    def open_dispute(self, agreement_id: str, buyer: str, reason: str = None):
        """Abre una disputa e inicia el reembolso inmediato"""
        if agreement_id not in self.state['agreements']:
            raise ValueError("Acuerdo no encontrado")
            
        agreement = self.state['agreements'][agreement_id]
        
        if buyer != agreement['buyer']:
            raise ValueError("Solo el comprador puede abrir disputas")
        
        valid_states = ['PENDING_SELLER_CONFIRMATION', 'AWAITING_SHIPMENT', 'SHIPPED']
        current_state = agreement['status']
        
        if current_state not in valid_states:
            raise ValueError(f"No se puede abrir disputa en estado: {current_state}")

        print(f"\n=== PROCESANDO DISPUTA Y REEMBOLSO ===")
        print(f"Acuerdo: {agreement_id}")
        print(f"Comprador: {agreement['buyer']}")
        print(f"Estado actual: {current_state}")
        print(f"Razón: {reason}")
        print(f"Monto a reembolsar: {agreement['amount']} BBC")

        # Crear transacción de reembolso
        refund_transaction = {
            'sender': self.address,
            'recipient': agreement['buyer'],
            'amount': agreement['amount'] + agreement['mediator_fee'],
            'fee': agreement['reserved_mining_fees'],
            'timestamp': time(),
            'type': 'contract_transfer',
            'signature': 'VALID'
        }

        self.blockchain.mempool.append(refund_transaction)
        
        # Guardar información de la cancelación ANTES de cambiar el estado
        agreement['cancellation_details'] = {
            'cancelled_at': time(),
            'cancelled_from_state': current_state,
            'cancelled_by': buyer,
            'reason': reason or 'No se proporcionó razón',
            'type': 'DISPUTE'
        }
        
        # Actualizar estado después de guardar los detalles
        agreement['status'] = 'CANCELLED'
        
        print(f"Reembolso enviado a mempool")
        print(f"Estado previo: {current_state}")
        print(f"Estado actualizado: CANCELLED")
        return True