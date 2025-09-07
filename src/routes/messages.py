from flask import Blueprint, request, jsonify, session
from src.models.user import db, Message, User, Product
from datetime import datetime
from sqlalchemy import or_, and_

messages_bp = Blueprint('messages', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@messages_bp.route('/conversations', methods=['GET'])
def get_conversations():
    """Get all conversations for the current user"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Get all conversations (unique pairs of users)
        conversations = db.session.query(Message).filter(
            or_(Message.sender_id == current_user.id, Message.receiver_id == current_user.id)
        ).order_by(Message.created_at.desc()).all()
        
        # Group by conversation partner
        conversation_dict = {}
        for message in conversations:
            partner_id = message.sender_id if message.receiver_id == current_user.id else message.receiver_id
            
            if partner_id not in conversation_dict:
                partner = User.query.get(partner_id)
                conversation_dict[partner_id] = {
                    'partner': partner.to_dict(),
                    'last_message': message.to_dict(),
                    'unread_count': 0,
                    'product': message.product.to_dict() if message.product else None
                }
            
            # Count unread messages
            if message.receiver_id == current_user.id and not message.is_read:
                conversation_dict[partner_id]['unread_count'] += 1
        
        conversations_list = list(conversation_dict.values())
        return jsonify({'conversations': conversations_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversation/<int:partner_id>', methods=['GET'])
def get_conversation_messages(partner_id):
    """Get all messages in a conversation with a specific user"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Get messages between current user and partner
        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == current_user.id)
            )
        ).order_by(Message.created_at.asc()).all()
        
        # Mark messages as read
        unread_messages = Message.query.filter(
            Message.sender_id == partner_id,
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).all()
        
        for message in unread_messages:
            message.is_read = True
        
        db.session.commit()
        
        # Get partner info
        partner = User.query.get(partner_id)
        if not partner:
            return jsonify({'error': 'Utilisateur non trouvé'}), 404
        
        messages_data = [message.to_dict() for message in messages]
        
        return jsonify({
            'messages': messages_data,
            'partner': partner.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/send', methods=['POST'])
def send_message():
    """Send a new message"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        content = data.get('content')
        receiver_id = data.get('receiver_id')
        product_id = data.get('product_id')
        
        if not content or not receiver_id:
            return jsonify({'error': 'Contenu et destinataire requis'}), 400
        
        # Check if receiver exists
        receiver = User.query.get(receiver_id)
        if not receiver:
            return jsonify({'error': 'Destinataire non trouvé'}), 404
        
        # Check if product exists (optional)
        product = None
        if product_id:
            product = Product.query.get(product_id)
            if not product:
                return jsonify({'error': 'Produit non trouvé'}), 404
        
        # Create new message
        message = Message(
            content=content,
            sender_id=current_user.id,
            receiver_id=receiver_id,
            product_id=product_id
        )
        
        db.session.add(message)
        db.session.commit()
        
        return jsonify({
            'message': 'Message envoyé avec succès',
            'data': message.to_dict()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/unread-count', methods=['GET'])
def get_unread_count():
    """Get total unread messages count for current user"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        unread_count = Message.query.filter(
            Message.receiver_id == current_user.id,
            Message.is_read == False
        ).count()
        
        return jsonify({'unread_count': unread_count}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/mark-read/<int:message_id>', methods=['POST'])
def mark_message_read(message_id):
    """Mark a specific message as read"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        message = Message.query.get(message_id)
        if not message:
            return jsonify({'error': 'Message non trouvé'}), 404
        
        if message.receiver_id != current_user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        message.is_read = True
        db.session.commit()
        
        return jsonify({'message': 'Message marqué comme lu'}), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/conversation/<int:partner_id>/product/<int:product_id>', methods=['GET'])
def get_product_conversation(partner_id, product_id):
    """Get messages for a specific product conversation"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Get messages between current user and partner for specific product
        messages = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.receiver_id == partner_id),
                and_(Message.sender_id == partner_id, Message.receiver_id == current_user.id)
            ),
            Message.product_id == product_id
        ).order_by(Message.created_at.asc()).all()
        
        # Mark messages as read
        unread_messages = Message.query.filter(
            Message.sender_id == partner_id,
            Message.receiver_id == current_user.id,
            Message.product_id == product_id,
            Message.is_read == False
        ).all()
        
        for message in unread_messages:
            message.is_read = True
        
        db.session.commit()
        
        # Get partner and product info
        partner = User.query.get(partner_id)
        product = Product.query.get(product_id)
        
        if not partner or not product:
            return jsonify({'error': 'Utilisateur ou produit non trouvé'}), 404
        
        messages_data = [message.to_dict() for message in messages]
        
        return jsonify({
            'messages': messages_data,
            'partner': partner.to_dict(),
            'product': product.to_dict()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/new-messages', methods=['GET'])
def check_new_messages():
    """Check for new messages since last check (for auto-refresh)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        last_check = request.args.get('since')
        if last_check:
            try:
                since_datetime = datetime.fromisoformat(last_check.replace('Z', '+00:00'))
            except:
                since_datetime = datetime.utcnow()
        else:
            since_datetime = datetime.utcnow()
        
        # Get new messages since last check
        new_messages = Message.query.filter(
            Message.receiver_id == current_user.id,
            Message.created_at > since_datetime
        ).order_by(Message.created_at.desc()).all()
        
        messages_data = [message.to_dict() for message in new_messages]
        
        return jsonify({
            'new_messages': messages_data,
            'count': len(messages_data),
            'timestamp': datetime.utcnow().isoformat()
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

