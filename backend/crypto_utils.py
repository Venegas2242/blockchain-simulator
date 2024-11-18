from ecdsa import SigningKey, VerifyingKey, SECP256k1
import json
import traceback

def verify_signature(public_key, transaction, signature):
    print("\n===== INICIO DE VERIFICACIÓN DE FIRMA =====")
    try:
        # Crear la clave de verificación
        print("1. Creando clave de verificación...")
        vk = VerifyingKey.from_string(bytes.fromhex(public_key), curve=SECP256k1)
        
        # Preparar los datos para verificar
        print("2. Preparando datos para verificar...")
        transaction_string = json.dumps(transaction, sort_keys=True)
        print(f"   Datos serializados: {transaction_string}")
        
        # Verificar la firma
        print("3. Verificando firma...")
        result = vk.verify(bytes.fromhex(signature), transaction_string.encode())
        print(f"   Resultado: {'Válido' if result else 'Inválido'}")
        
        print("===== FIN DE VERIFICACIÓN DE FIRMA =====")
        return True
    except Exception as e:
        print(f"ERROR en verify_signature: {str(e)}")
        print(traceback.format_exc())
        return False

def sign_transaction(private_key, transaction):
    try:
        # Crear la clave de firma a partir de la clave privada
        sk = SigningKey.from_string(bytes.fromhex(private_key), curve=SECP256k1)
        transaction_string = json.dumps(transaction, sort_keys=True)
        
        # Generar la firma
        signature = sk.sign(transaction_string.encode())
        return signature
    except Exception as e:
        print(f"Error al firmar la transacción: {str(e)}")
        raise