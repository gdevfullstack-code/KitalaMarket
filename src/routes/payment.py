from flask import Blueprint, request, jsonify, session
from src.models.user import db, Order, User
import requests
import uuid
import time
from datetime import datetime, timedelta
import hashlib
import hmac
import base64
import json

payment_bp = Blueprint('payment', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

# MTN Mobile Money API Configuration (simulation)
MTN_API_CONFIG = {
    'base_url': 'https://sandbox.momodeveloper.mtn.com',
    'collection_primary_key': 'your_collection_primary_key',
    'collection_user_id': 'your_collection_user_id',
    'collection_api_secret': 'your_collection_api_secret',
    'disbursement_primary_key': 'your_disbursement_primary_key',
    'disbursement_user_id': 'your_disbursement_user_id',
    'disbursement_api_secret': 'your_disbursement_api_secret'
}

# Airtel Money API Configuration (simulation)
AIRTEL_API_CONFIG = {
    'base_url': 'https://openapiuat.airtel.africa',
    'client_id': 'your_airtel_client_id',
    'client_secret': 'your_airtel_client_secret',
    'grant_type': 'client_credentials',
    'x_country': 'CM',  # Cameroon
    'x_currency': 'XAF'  # Central African Franc
}

def detect_mobile_provider(phone_number):
    """Detect mobile provider based on phone number prefix"""
    # Remove country code and spaces
    clean_number = phone_number.replace('+', '').replace(' ', '').replace('-', '')
    
    # Cameroon prefixes
    if clean_number.startswith('237'):
        clean_number = clean_number[3:]  # Remove country code
    
    # MTN prefixes: 06, 67, 650-659, 680-689
    mtn_prefixes = ['06', '67']
    for prefix in mtn_prefixes:
        if clean_number.startswith(prefix):
            return 'mtn'
    
    # Check for longer MTN prefixes
    if clean_number.startswith('65') and len(clean_number) >= 3:
        third_digit = clean_number[2]
        if third_digit in '0123456789':
            return 'mtn'
    
    if clean_number.startswith('68') and len(clean_number) >= 3:
        third_digit = clean_number[2]
        if third_digit in '0123456789':
            return 'mtn'
    
    # Airtel prefixes: 05, 04, 75, 76, 77, 78
    airtel_prefixes = ['05', '04', '75', '76', '77', '78']
    for prefix in airtel_prefixes:
        if clean_number.startswith(prefix):
            return 'airtel'
    
    # Default to MTN if unknown
    return 'mtn'

def generate_mtn_token(user_id, api_secret):
    """Generate MTN API token (simulation)"""
    try:
        # In real implementation, this would call MTN API
        # For simulation, we'll generate a mock token
        timestamp = str(int(time.time()))
        token_data = f"{user_id}:{timestamp}"
        token = base64.b64encode(token_data.encode()).decode()
        
        return {
            'access_token': f"mtn_token_{token}",
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    except Exception as e:
        return None

def simulate_mtn_request_to_pay(amount, phone_number, external_id, payer_message="Payment for Kitalamarket order"):
    """Simulate MTN Mobile Money request to pay"""
    try:
        # Generate mock response
        transaction_id = str(uuid.uuid4())
        
        # Simulate API call delay
        time.sleep(1)
        
        # Simulate success/failure based on phone number pattern
        # For testing: numbers ending in 0-7 succeed, 8-9 fail
        last_digit = int(phone_number[-1]) if phone_number[-1].isdigit() else 0
        
        if last_digit >= 8:
            return {
                'success': False,
                'error': 'PAYER_NOT_FOUND',
                'message': 'Le numéro de téléphone n\'est pas enregistré pour Mobile Money'
            }
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'external_id': external_id,
            'amount': amount,
            'currency': 'EUR',  # or XAF for Central Africa
            'phone_number': phone_number,
            'status': 'PENDING',
            'message': 'Demande de paiement envoyée avec succès'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }

def simulate_mtn_transaction_status(transaction_id):
    """Simulate checking MTN transaction status"""
    try:
        # Simulate API call delay
        time.sleep(0.5)
        
        # Simulate different statuses based on transaction ID
        hash_value = int(hashlib.md5(transaction_id.encode()).hexdigest()[:8], 16)
        status_options = ['PENDING', 'SUCCESSFUL', 'FAILED']
        status = status_options[hash_value % len(status_options)]
        
        response = {
            'transaction_id': transaction_id,
            'status': status,
            'amount': 100.0,  # This would come from the original request
            'currency': 'EUR',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if status == 'SUCCESSFUL':
            response['financial_transaction_id'] = f"FT{int(time.time())}"
            response['message'] = 'Paiement effectué avec succès'
        elif status == 'FAILED':
            response['reason'] = 'INSUFFICIENT_FUNDS'
            response['message'] = 'Fonds insuffisants'
        else:
            response['message'] = 'Paiement en cours de traitement'
        
        return response
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e)
        }

def generate_airtel_token():
    """Generate Airtel Money API token (simulation)"""
    try:
        # In real implementation, this would call Airtel API
        # For simulation, we'll generate a mock token
        timestamp = str(int(time.time()))
        token_data = f"airtel_token:{timestamp}"
        token = base64.b64encode(token_data.encode()).decode()
        
        return {
            'access_token': f"airtel_bearer_{token}",
            'token_type': 'Bearer',
            'expires_in': 3600
        }
    except Exception as e:
        return None

def simulate_airtel_request_to_pay(amount, phone_number, external_id, reference="Payment for Kitalamarket order"):
    """Simulate Airtel Money request to pay"""
    try:
        # Generate mock response
        transaction_id = str(uuid.uuid4())
        
        # Simulate API call delay
        time.sleep(1)
        
        # Simulate success/failure based on phone number pattern
        # For testing: numbers ending in 0-7 succeed, 8-9 fail
        last_digit = int(phone_number[-1]) if phone_number[-1].isdigit() else 0
        
        if last_digit >= 8:
            return {
                'success': False,
                'error': 'INVALID_MSISDN',
                'message': 'Le numéro de téléphone n\'est pas valide pour Airtel Money'
            }
        
        return {
            'success': True,
            'transaction_id': transaction_id,
            'external_id': external_id,
            'amount': amount,
            'currency': 'XAF',
            'phone_number': phone_number,
            'status': 'PENDING',
            'message': 'Demande de paiement Airtel Money envoyée avec succès'
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': 'INTERNAL_ERROR',
            'message': str(e)
        }

def simulate_airtel_transaction_status(transaction_id):
    """Simulate checking Airtel transaction status"""
    try:
        # Simulate API call delay
        time.sleep(0.5)
        
        # Simulate different statuses based on transaction ID
        hash_value = int(hashlib.md5(transaction_id.encode()).hexdigest()[:8], 16)
        status_options = ['PENDING', 'SUCCESS', 'FAILED']
        status = status_options[hash_value % len(status_options)]
        
        response = {
            'transaction_id': transaction_id,
            'status': status,
            'amount': 100.0,  # This would come from the original request
            'currency': 'XAF',
            'created_at': datetime.utcnow().isoformat(),
            'updated_at': datetime.utcnow().isoformat()
        }
        
        if status == 'SUCCESS':
            response['airtel_transaction_id'] = f"AM{int(time.time())}"
            response['message'] = 'Paiement Airtel Money effectué avec succès'
        elif status == 'FAILED':
            response['reason'] = 'INSUFFICIENT_BALANCE'
            response['message'] = 'Solde insuffisant sur le compte Airtel Money'
        else:
            response['message'] = 'Paiement Airtel Money en cours de traitement'
        
        return response
        
    except Exception as e:
        return {
            'status': 'ERROR',
            'message': str(e)
        }

@payment_bp.route('/methods', methods=['GET'])
def get_payment_methods():
    """Get available payment methods"""
    try:
        methods = [
            {
                'id': 'mtn_mobile_money',
                'name': 'MTN Mobile Money',
                'description': 'Payez avec votre compte MTN Mobile Money',
                'icon': 'mtn-logo.png',
                'enabled': True,
                'countries': ['CM', 'CI', 'GH', 'UG', 'ZM', 'RW']
            },
            {
                'id': 'orange_money',
                'name': 'Orange Money',
                'description': 'Payez avec votre compte Orange Money',
                'icon': 'orange-logo.png',
                'enabled': False,  # Not implemented yet
                'countries': ['CM', 'CI', 'SN', 'ML', 'BF']
            },
            {
                'id': 'card',
                'name': 'Carte bancaire',
                'description': 'Payez par carte Visa ou Mastercard',
                'icon': 'card-icon.png',
                'enabled': False,  # Not implemented yet
                'countries': ['ALL']
            }
        ]
        
        return jsonify({'payment_methods': methods}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/mobile-money/request-to-pay', methods=['POST'])
def mobile_money_request_to_pay():
    """Initiate Mobile Money payment (MTN or Airtel based on phone number)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        phone_number = data.get('phone_number')
        
        if not order_id or not phone_number:
            return jsonify({'error': 'ID de commande et numéro de téléphone requis'}), 400
        
        # Validate phone number format
        if not phone_number.startswith('+') or len(phone_number) < 10:
            return jsonify({'error': 'Format de numéro de téléphone invalide'}), 400
        
        # Detect mobile provider
        provider = detect_mobile_provider(phone_number)
        
        # Get order
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        if order.buyer_id != current_user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        if order.payment_status != 'pending':
            return jsonify({'error': 'Cette commande a déjà été payée ou annulée'}), 400
        
        # Generate external ID for tracking
        external_id = f"KM_{order_id}_{int(time.time())}"
        
        # Call appropriate API based on provider
        if provider == 'mtn':
            api_response = simulate_mtn_request_to_pay(
                amount=order.total_price,
                phone_number=phone_number,
                external_id=external_id,
                payer_message=f"Paiement pour commande #{order.tracking_number}"
            )
        else:  # airtel
            api_response = simulate_airtel_request_to_pay(
                amount=order.total_price,
                phone_number=phone_number,
                external_id=external_id,
                reference=f"Paiement pour commande #{order.tracking_number}"
            )
        
        if not api_response['success']:
            return jsonify({
                'error': api_response['error'],
                'message': api_response['message']
            }), 400
        
        # Store payment information in session
        payment_data = {
            'transaction_id': api_response['transaction_id'],
            'external_id': external_id,
            'order_id': order_id,
            'amount': order.total_price,
            'phone_number': phone_number,
            'provider': provider,
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat()
        }
        
        # Store in session for tracking
        if 'pending_payments' not in session:
            session['pending_payments'] = {}
        
        session['pending_payments'][api_response['transaction_id']] = payment_data
        session.modified = True
        
        return jsonify({
            'message': api_response['message'],
            'transaction_id': api_response['transaction_id'],
            'external_id': external_id,
            'amount': order.total_price,
            'provider': provider.upper(),
            'status': 'PENDING',
            'instructions': f'Vérifiez votre téléphone {provider.upper()} et confirmez le paiement'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/mobile-money/status/<transaction_id>', methods=['GET'])
def check_mobile_money_payment_status(transaction_id):
    """Check Mobile Money payment status (MTN or Airtel)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Check if transaction exists in session
        pending_payments = session.get('pending_payments', {})
        if transaction_id not in pending_payments:
            return jsonify({'error': 'Transaction non trouvée'}), 404
        
        payment_data = pending_payments[transaction_id]
        provider = payment_data.get('provider', 'mtn')
        
        # Call appropriate API based on provider
        if provider == 'mtn':
            status_response = simulate_mtn_transaction_status(transaction_id)
        else:  # airtel
            status_response = simulate_airtel_transaction_status(transaction_id)
        
        # Update payment status
        payment_data['status'] = status_response['status']
        payment_data['updated_at'] = datetime.utcnow().isoformat()
        
        if status_response['status'] in ['SUCCESSFUL', 'SUCCESS']:
            # Update order payment status
            order = Order.query.get(payment_data['order_id'])
            if order:
                order.payment_status = 'paid'
                order.order_status = 'confirmed'
                order.payment_method = f'{provider}_mobile_money'
                order.updated_at = datetime.utcnow()
                db.session.commit()
            
            # Store transaction reference
            if provider == 'mtn':
                payment_data['financial_transaction_id'] = status_response.get('financial_transaction_id')
            else:
                payment_data['airtel_transaction_id'] = status_response.get('airtel_transaction_id')
            
            # Remove from pending payments
            del session['pending_payments'][transaction_id]
            session.modified = True
            
        elif status_response['status'] == 'FAILED':
            # Update order payment status
            order = Order.query.get(payment_data['order_id'])
            if order:
                order.payment_status = 'failed'
                db.session.commit()
            
            payment_data['failure_reason'] = status_response.get('reason')
            
            # Remove from pending payments
            del session['pending_payments'][transaction_id]
            session.modified = True
        
        # Update session data
        if transaction_id in session.get('pending_payments', {}):
            session['pending_payments'][transaction_id] = payment_data
            session.modified = True
        
        return jsonify({
            'transaction_id': transaction_id,
            'status': status_response['status'],
            'message': status_response.get('message', ''),
            'amount': payment_data['amount'],
            'provider': provider.upper(),
            'order_id': payment_data['order_id'],
            'updated_at': payment_data['updated_at']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/pending-payments', methods=['GET'])
def get_pending_payments():
    """Get user's pending payments"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        pending_payments = session.get('pending_payments', {})
        
        # Filter payments for current user and clean up old ones
        user_payments = {}
        current_time = datetime.utcnow()
        
        for transaction_id, payment_data in pending_payments.items():
            # Check if payment is older than 1 hour
            created_at = datetime.fromisoformat(payment_data['created_at'])
            if current_time - created_at > timedelta(hours=1):
                continue  # Skip old payments
            
            # Check if order belongs to current user
            order = Order.query.get(payment_data['order_id'])
            if order and order.buyer_id == current_user.id:
                user_payments[transaction_id] = payment_data
        
        # Update session with cleaned data
        session['pending_payments'] = user_payments
        session.modified = True
        
        return jsonify({'pending_payments': user_payments}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/cancel-payment', methods=['POST'])
def cancel_payment():
    """Cancel a pending payment"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        
        if not transaction_id:
            return jsonify({'error': 'ID de transaction requis'}), 400
        
        pending_payments = session.get('pending_payments', {})
        
        if transaction_id not in pending_payments:
            return jsonify({'error': 'Transaction non trouvée'}), 404
        
        payment_data = pending_payments[transaction_id]
        
        # Verify ownership
        order = Order.query.get(payment_data['order_id'])
        if not order or order.buyer_id != current_user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        # Remove from pending payments
        del session['pending_payments'][transaction_id]
        session.modified = True
        
        return jsonify({'message': 'Paiement annulé'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/webhook/mtn', methods=['POST'])
def mtn_webhook():
    """Handle MTN Mobile Money webhooks (for real implementation)"""
    try:
        # In real implementation, verify webhook signature
        data = request.get_json()
        
        transaction_id = data.get('referenceId')
        status = data.get('status')
        
        if not transaction_id or not status:
            return jsonify({'error': 'Invalid webhook data'}), 400
        
        # Find and update order
        # This would require storing transaction IDs in database
        # For now, just log the webhook
        print(f"MTN Webhook received: {transaction_id} - {status}")
        
        return jsonify({'message': 'Webhook processed'}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/simulate-callback', methods=['POST'])
def simulate_payment_callback():
    """Simulate payment callback for testing"""
    try:
        data = request.get_json()
        transaction_id = data.get('transaction_id')
        status = data.get('status', 'SUCCESSFUL')
        
        if not transaction_id:
            return jsonify({'error': 'ID de transaction requis'}), 400
        
        # Find transaction in all sessions (for testing only)
        # In real implementation, this would be stored in database
        
        return jsonify({
            'message': 'Callback simulé',
            'transaction_id': transaction_id,
            'status': status
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@payment_bp.route('/payment-history', methods=['GET'])
def get_payment_history():
    """Get user's payment history"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        # Get orders with payment information
        pagination = Order.query.filter_by(buyer_id=current_user.id).order_by(
            Order.created_at.desc()
        ).paginate(page=page, per_page=per_page, error_out=False)
        
        payment_history = []
        for order in pagination.items:
            payment_info = {
                'order_id': order.id,
                'tracking_number': order.tracking_number,
                'amount': order.total_price,
                'payment_method': order.payment_method,
                'payment_status': order.payment_status,
                'order_status': order.order_status,
                'created_at': order.created_at.isoformat(),
                'updated_at': order.updated_at.isoformat(),
                'product': order.product.to_dict() if order.product else None,
                'seller': order.seller.to_dict() if order.seller else None
            }
            payment_history.append(payment_info)
        
        return jsonify({
            'payment_history': payment_history,
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': pagination.total,
                'pages': pagination.pages,
                'has_next': pagination.has_next,
                'has_prev': pagination.has_prev
            }
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

