from flask import Blueprint, request, jsonify, session
from src.models.user import db, User, Order
from src.routes.payment import detect_mobile_provider, simulate_mtn_request_to_pay, simulate_airtel_request_to_pay, simulate_mtn_transaction_status, simulate_airtel_transaction_status
import uuid
import time
from datetime import datetime, timedelta

premium_bp = Blueprint('premium', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

# Premium plans configuration
PREMIUM_PLANS = {
    'basic': {
        'name': 'Premium Basic',
        'price': 9.99,
        'duration_days': 30,
        'features': [
            'Mise en avant des annonces',
            'Support prioritaire',
            'Statistiques détaillées',
            'Badge premium'
        ]
    },
    'pro': {
        'name': 'Premium Pro',
        'price': 19.99,
        'duration_days': 30,
        'features': [
            'Toutes les fonctionnalités Basic',
            'Annonces illimitées',
            'Promotion sur page d\'accueil',
            'Analytics avancées',
            'API access'
        ]
    },
    'enterprise': {
        'name': 'Premium Enterprise',
        'price': 49.99,
        'duration_days': 30,
        'features': [
            'Toutes les fonctionnalités Pro',
            'Manager dédié',
            'Intégration personnalisée',
            'Support 24/7',
            'Rapports personnalisés'
        ]
    }
}

@premium_bp.route('/plans', methods=['GET'])
def get_premium_plans():
    """Get available premium plans"""
    try:
        return jsonify({
            'plans': PREMIUM_PLANS,
            'currency': 'EUR'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/current-plan', methods=['GET'])
def get_current_plan():
    """Get user's current premium plan"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Check if user has active premium
        premium_info = {
            'has_premium': False,
            'plan': None,
            'expires_at': None,
            'days_remaining': 0
        }
        
        # In a real app, this would come from a premium_subscriptions table
        # For simulation, we'll use user attributes
        if hasattr(current_user, 'premium_plan') and current_user.premium_plan:
            premium_expires = getattr(current_user, 'premium_expires', None)
            if premium_expires and premium_expires > datetime.utcnow():
                days_remaining = (premium_expires - datetime.utcnow()).days
                premium_info = {
                    'has_premium': True,
                    'plan': current_user.premium_plan,
                    'expires_at': premium_expires.isoformat(),
                    'days_remaining': days_remaining
                }
        
        return jsonify(premium_info), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/subscribe', methods=['POST'])
def subscribe_to_premium():
    """Subscribe to premium plan"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        plan_id = data.get('plan_id')
        phone_number = data.get('phone_number')
        
        if not plan_id or not phone_number:
            return jsonify({'error': 'Plan et numéro de téléphone requis'}), 400
        
        if plan_id not in PREMIUM_PLANS:
            return jsonify({'error': 'Plan premium invalide'}), 400
        
        # Validate phone number format
        if not phone_number.startswith('+') or len(phone_number) < 10:
            return jsonify({'error': 'Format de numéro de téléphone invalide'}), 400
        
        plan = PREMIUM_PLANS[plan_id]
        
        # Detect mobile provider
        provider = detect_mobile_provider(phone_number)
        
        # Generate external ID for tracking
        external_id = f"PREMIUM_{current_user.id}_{plan_id}_{int(time.time())}"
        
        # Call appropriate API based on provider
        if provider == 'mtn':
            api_response = simulate_mtn_request_to_pay(
                amount=plan['price'],
                phone_number=phone_number,
                external_id=external_id,
                payer_message=f"Abonnement {plan['name']} - Kitalamarket"
            )
        else:  # airtel
            api_response = simulate_airtel_request_to_pay(
                amount=plan['price'],
                phone_number=phone_number,
                external_id=external_id,
                reference=f"Abonnement {plan['name']} - Kitalamarket"
            )
        
        if not api_response['success']:
            return jsonify({
                'error': api_response['error'],
                'message': api_response['message']
            }), 400
        
        # Store premium payment information in session
        premium_payment_data = {
            'transaction_id': api_response['transaction_id'],
            'external_id': external_id,
            'user_id': current_user.id,
            'plan_id': plan_id,
            'amount': plan['price'],
            'phone_number': phone_number,
            'provider': provider,
            'status': 'PENDING',
            'created_at': datetime.utcnow().isoformat(),
            'type': 'premium_subscription'
        }
        
        # Store in session for tracking
        if 'pending_premium_payments' not in session:
            session['pending_premium_payments'] = {}
        
        session['pending_premium_payments'][api_response['transaction_id']] = premium_payment_data
        session.modified = True
        
        return jsonify({
            'message': f'Demande de paiement {provider.upper()} envoyée pour {plan["name"]}',
            'transaction_id': api_response['transaction_id'],
            'external_id': external_id,
            'amount': plan['price'],
            'plan': plan,
            'provider': provider.upper(),
            'status': 'PENDING',
            'instructions': f'Vérifiez votre téléphone {provider.upper()} et confirmez le paiement de {plan["price"]}€'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/payment-status/<transaction_id>', methods=['GET'])
def check_premium_payment_status(transaction_id):
    """Check premium payment status"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Check if transaction exists in session
        pending_payments = session.get('pending_premium_payments', {})
        if transaction_id not in pending_payments:
            return jsonify({'error': 'Transaction premium non trouvée'}), 404
        
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
            # Activate premium subscription
            plan_id = payment_data['plan_id']
            plan = PREMIUM_PLANS[plan_id]
            
            # Update user premium status (in real app, this would be in a separate table)
            current_user.premium_plan = plan_id
            current_user.premium_expires = datetime.utcnow() + timedelta(days=plan['duration_days'])
            current_user.is_premium = True
            
            # Store transaction reference
            if provider == 'mtn':
                payment_data['financial_transaction_id'] = status_response.get('financial_transaction_id')
            else:
                payment_data['airtel_transaction_id'] = status_response.get('airtel_transaction_id')
            
            db.session.commit()
            
            # Remove from pending payments
            del session['pending_premium_payments'][transaction_id]
            session.modified = True
            
            return jsonify({
                'transaction_id': transaction_id,
                'status': 'SUCCESS',
                'message': f'Abonnement {plan["name"]} activé avec succès !',
                'plan': plan,
                'expires_at': current_user.premium_expires.isoformat(),
                'provider': provider.upper()
            }), 200
            
        elif status_response['status'] == 'FAILED':
            payment_data['failure_reason'] = status_response.get('reason')
            
            # Remove from pending payments
            del session['pending_premium_payments'][transaction_id]
            session.modified = True
            
            return jsonify({
                'transaction_id': transaction_id,
                'status': 'FAILED',
                'message': 'Échec du paiement premium',
                'error': status_response.get('message', 'Paiement échoué'),
                'provider': provider.upper()
            }), 200
        
        # Update session data for pending status
        session['pending_premium_payments'][transaction_id] = payment_data
        session.modified = True
        
        return jsonify({
            'transaction_id': transaction_id,
            'status': status_response['status'],
            'message': status_response.get('message', 'Paiement en cours de traitement'),
            'amount': payment_data['amount'],
            'provider': provider.upper(),
            'updated_at': payment_data['updated_at']
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/cancel-subscription', methods=['POST'])
def cancel_premium_subscription():
    """Cancel premium subscription"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Check if user has premium
        if not hasattr(current_user, 'premium_plan') or not current_user.premium_plan:
            return jsonify({'error': 'Aucun abonnement premium actif'}), 400
        
        # Cancel subscription (in real app, this would update subscription status)
        current_user.premium_plan = None
        current_user.premium_expires = None
        current_user.is_premium = False
        
        db.session.commit()
        
        return jsonify({
            'message': 'Abonnement premium annulé avec succès'
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/features', methods=['GET'])
def get_premium_features():
    """Get premium features for current user"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        features = {
            'has_premium': False,
            'available_features': [],
            'plan_name': None
        }
        
        # Check if user has active premium
        if hasattr(current_user, 'premium_plan') and current_user.premium_plan:
            premium_expires = getattr(current_user, 'premium_expires', None)
            if premium_expires and premium_expires > datetime.utcnow():
                plan = PREMIUM_PLANS.get(current_user.premium_plan)
                if plan:
                    features = {
                        'has_premium': True,
                        'available_features': plan['features'],
                        'plan_name': plan['name'],
                        'expires_at': premium_expires.isoformat()
                    }
        
        return jsonify(features), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/usage-stats', methods=['GET'])
def get_premium_usage_stats():
    """Get premium usage statistics"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Check if user has premium
        if not hasattr(current_user, 'premium_plan') or not current_user.premium_plan:
            return jsonify({'error': 'Abonnement premium requis'}), 403
        
        # Simulate usage stats
        stats = {
            'featured_listings': 5,
            'priority_support_tickets': 2,
            'analytics_views': 1250,
            'api_calls': 150,
            'current_month': datetime.utcnow().strftime('%B %Y')
        }
        
        return jsonify(stats), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@premium_bp.route('/pending-payments', methods=['GET'])
def get_pending_premium_payments():
    """Get user's pending premium payments"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        pending_payments = session.get('pending_premium_payments', {})
        
        # Filter payments for current user and clean up old ones
        user_payments = {}
        current_time = datetime.utcnow()
        
        for transaction_id, payment_data in pending_payments.items():
            # Check if payment is older than 1 hour
            created_at = datetime.fromisoformat(payment_data['created_at'])
            if current_time - created_at > timedelta(hours=1):
                continue  # Skip old payments
            
            # Check if payment belongs to current user
            if payment_data['user_id'] == current_user.id:
                user_payments[transaction_id] = payment_data
        
        # Update session with cleaned data
        session['pending_premium_payments'] = user_payments
        session.modified = True
        
        return jsonify({'pending_premium_payments': user_payments}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

