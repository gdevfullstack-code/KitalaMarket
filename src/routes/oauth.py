from flask import Blueprint, request, jsonify, session, redirect, url_for
from authlib.integrations.flask_client import OAuth
from src.models.user import db, User
import requests
import secrets
import hashlib
from datetime import datetime

oauth_bp = Blueprint('oauth', __name__)

# Configuration OAuth (à remplacer par vos vraies clés)
GOOGLE_CLIENT_ID = "your_google_client_id.apps.googleusercontent.com"
GOOGLE_CLIENT_SECRET = "your_google_client_secret"
FACEBOOK_CLIENT_ID = "your_facebook_app_id"
FACEBOOK_CLIENT_SECRET = "your_facebook_app_secret"

# Initialize OAuth
oauth = OAuth()

def init_oauth(app):
    """Initialize OAuth with Flask app"""
    oauth.init_app(app)
    
    # Google OAuth
    oauth.register(
        name='google',
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={
            'scope': 'openid email profile'
        }
    )
    
    # Facebook OAuth
    oauth.register(
        name='facebook',
        client_id=FACEBOOK_CLIENT_ID,
        client_secret=FACEBOOK_CLIENT_SECRET,
        access_token_url='https://graph.facebook.com/oauth/access_token',
        authorize_url='https://www.facebook.com/dialog/oauth',
        api_base_url='https://graph.facebook.com/',
        client_kwargs={'scope': 'email public_profile'},
    )

def create_or_get_oauth_user(provider, user_info):
    """Create or get user from OAuth provider info"""
    try:
        email = user_info.get('email')
        if not email:
            return None, "Email non fourni par le fournisseur"
        
        # Check if user already exists
        user = User.query.filter_by(email=email).first()
        
        if user:
            # Update OAuth info if user exists
            if provider == 'google':
                user.google_id = user_info.get('sub') or user_info.get('id')
            elif provider == 'facebook':
                user.facebook_id = user_info.get('id')
            
            user.last_login = datetime.utcnow()
            db.session.commit()
            return user, None
        
        # Create new user
        first_name = user_info.get('given_name') or user_info.get('first_name', '')
        last_name = user_info.get('family_name') or user_info.get('last_name', '')
        name = user_info.get('name', f"{first_name} {last_name}").strip()
        
        # Generate username from email
        username = email.split('@')[0]
        counter = 1
        original_username = username
        while User.query.filter_by(username=username).first():
            username = f"{original_username}{counter}"
            counter += 1
        
        # Create user
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            password_hash=hashlib.sha256(secrets.token_hex(16).encode()).hexdigest(),  # Random password
            is_verified=True,  # OAuth users are pre-verified
            profile_image=user_info.get('picture'),
            user_type='buyer'  # Default type
        )
        
        # Set OAuth IDs
        if provider == 'google':
            user.google_id = user_info.get('sub') or user_info.get('id')
        elif provider == 'facebook':
            user.facebook_id = user_info.get('id')
        
        db.session.add(user)
        db.session.commit()
        
        return user, None
        
    except Exception as e:
        db.session.rollback()
        return None, str(e)

@oauth_bp.route('/google/login', methods=['GET'])
def google_login():
    """Initiate Google OAuth login"""
    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # For development/testing, simulate OAuth flow
        # In production, this would redirect to Google
        return jsonify({
            'auth_url': f'https://accounts.google.com/oauth/authorize?client_id={GOOGLE_CLIENT_ID}&redirect_uri=http://localhost:5000/api/oauth/google/callback&scope=openid+email+profile&response_type=code&state={state}',
            'state': state,
            'message': 'Redirection vers Google OAuth (simulé en développement)'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/google/callback', methods=['GET', 'POST'])
def google_callback():
    """Handle Google OAuth callback"""
    try:
        # In development, simulate successful Google OAuth response
        # In production, this would handle the actual OAuth callback
        
        # Simulate Google user info
        google_user_info = {
            'sub': '1234567890',
            'email': 'user.google@gmail.com',
            'given_name': 'John',
            'family_name': 'Doe',
            'name': 'John Doe',
            'picture': 'https://lh3.googleusercontent.com/a/default-user=s96-c'
        }
        
        user, error = create_or_get_oauth_user('google', google_user_info)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Connexion Google réussie',
            'user': user.to_dict(),
            'redirect_url': '/dashboard.html'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/facebook/login', methods=['GET'])
def facebook_login():
    """Initiate Facebook OAuth login"""
    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(32)
        session['oauth_state'] = state
        
        # For development/testing, simulate OAuth flow
        return jsonify({
            'auth_url': f'https://www.facebook.com/dialog/oauth?client_id={FACEBOOK_CLIENT_ID}&redirect_uri=http://localhost:5000/api/oauth/facebook/callback&scope=email,public_profile&response_type=code&state={state}',
            'state': state,
            'message': 'Redirection vers Facebook OAuth (simulé en développement)'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/facebook/callback', methods=['GET', 'POST'])
def facebook_callback():
    """Handle Facebook OAuth callback"""
    try:
        # In development, simulate successful Facebook OAuth response
        # In production, this would handle the actual OAuth callback
        
        # Simulate Facebook user info
        facebook_user_info = {
            'id': '9876543210',
            'email': 'user.facebook@gmail.com',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'name': 'Jane Smith',
            'picture': {
                'data': {
                    'url': 'https://graph.facebook.com/9876543210/picture?type=large'
                }
            }
        }
        
        # Extract picture URL
        if 'picture' in facebook_user_info and 'data' in facebook_user_info['picture']:
            facebook_user_info['picture'] = facebook_user_info['picture']['data']['url']
        
        user, error = create_or_get_oauth_user('facebook', facebook_user_info)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Connexion Facebook réussie',
            'user': user.to_dict(),
            'redirect_url': '/dashboard.html'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/google/simulate', methods=['POST'])
def simulate_google_login():
    """Simulate Google login for testing"""
    try:
        data = request.get_json()
        email = data.get('email', 'test.google@gmail.com')
        
        # Simulate Google user info
        google_user_info = {
            'sub': f'google_{hash(email) % 1000000}',
            'email': email,
            'given_name': email.split('@')[0].split('.')[0].title(),
            'family_name': email.split('@')[0].split('.')[-1].title() if '.' in email.split('@')[0] else 'User',
            'name': email.split('@')[0].replace('.', ' ').title(),
            'picture': 'https://lh3.googleusercontent.com/a/default-user=s96-c'
        }
        
        user, error = create_or_get_oauth_user('google', google_user_info)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Connexion Google simulée réussie',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/facebook/simulate', methods=['POST'])
def simulate_facebook_login():
    """Simulate Facebook login for testing"""
    try:
        data = request.get_json()
        email = data.get('email', 'test.facebook@gmail.com')
        
        # Simulate Facebook user info
        facebook_user_info = {
            'id': f'fb_{hash(email) % 1000000}',
            'email': email,
            'first_name': email.split('@')[0].split('.')[0].title(),
            'last_name': email.split('@')[0].split('.')[-1].title() if '.' in email.split('@')[0] else 'User',
            'name': email.split('@')[0].replace('.', ' ').title(),
            'picture': f'https://graph.facebook.com/fb_{hash(email) % 1000000}/picture?type=large'
        }
        
        user, error = create_or_get_oauth_user('facebook', facebook_user_info)
        
        if error:
            return jsonify({'error': error}), 400
        
        # Set session
        session['user_id'] = user.id
        session['username'] = user.username
        
        return jsonify({
            'message': 'Connexion Facebook simulée réussie',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/link-account', methods=['POST'])
def link_oauth_account():
    """Link OAuth account to existing user"""
    try:
        # Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        provider = data.get('provider')
        provider_id = data.get('provider_id')
        
        if not provider or not provider_id:
            return jsonify({'error': 'Fournisseur et ID requis'}), 400
        
        # Link account
        if provider == 'google':
            user.google_id = provider_id
        elif provider == 'facebook':
            user.facebook_id = provider_id
        else:
            return jsonify({'error': 'Fournisseur non supporté'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'Compte {provider} lié avec succès',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/unlink-account', methods=['POST'])
def unlink_oauth_account():
    """Unlink OAuth account from user"""
    try:
        # Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        data = request.get_json()
        provider = data.get('provider')
        
        if not provider:
            return jsonify({'error': 'Fournisseur requis'}), 400
        
        # Unlink account
        if provider == 'google':
            user.google_id = None
        elif provider == 'facebook':
            user.facebook_id = None
        else:
            return jsonify({'error': 'Fournisseur non supporté'}), 400
        
        db.session.commit()
        
        return jsonify({
            'message': f'Compte {provider} délié avec succès',
            'user': user.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@oauth_bp.route('/linked-accounts', methods=['GET'])
def get_linked_accounts():
    """Get user's linked OAuth accounts"""
    try:
        # Check if user is logged in
        user_id = session.get('user_id')
        if not user_id:
            return jsonify({'error': 'Non authentifié'}), 401
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        linked_accounts = {
            'google': {
                'linked': user.google_id is not None,
                'id': user.google_id
            },
            'facebook': {
                'linked': user.facebook_id is not None,
                'id': user.facebook_id
            }
        }
        
        return jsonify({'linked_accounts': linked_accounts}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

