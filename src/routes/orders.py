from flask import Blueprint, request, jsonify, session
from src.models.user import db, Order, Product, User, Cart
from datetime import datetime
import uuid

orders_bp = Blueprint('orders', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def get_cart_session_key():
    """Get or create cart session key"""
    if 'cart_session_id' not in session:
        session['cart_session_id'] = str(uuid.uuid4())
    return session['cart_session_id']

@orders_bp.route('/cart', methods=['GET'])
def get_cart():
    """Get current user's cart items"""
    current_user = require_auth()
    
    try:
        if current_user:
            # Authenticated user - get cart from database
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            cart_data = []
            total_price = 0
            
            for item in cart_items:
                if item.product and item.product.status == 'active':
                    item_data = {
                        'id': item.id,
                        'product': item.product.to_dict(),
                        'quantity': item.quantity,
                        'subtotal': item.product.price * item.quantity,
                        'added_at': item.created_at.isoformat()
                    }
                    cart_data.append(item_data)
                    total_price += item_data['subtotal']
        else:
            # Anonymous user - get cart from session
            cart_session = session.get('cart', {})
            cart_data = []
            total_price = 0
            
            for product_id, quantity in cart_session.items():
                product = Product.query.get(int(product_id))
                if product and product.status == 'active':
                    item_data = {
                        'product': product.to_dict(),
                        'quantity': quantity,
                        'subtotal': product.price * quantity
                    }
                    cart_data.append(item_data)
                    total_price += item_data['subtotal']
        
        return jsonify({
            'cart_items': cart_data,
            'total_items': len(cart_data),
            'total_price': round(total_price, 2),
            'is_authenticated': current_user is not None
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    """Add product to cart"""
    current_user = require_auth()
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity', 1)
        
        if not product_id:
            return jsonify({'error': 'ID du produit requis'}), 400
        
        if quantity < 1:
            return jsonify({'error': 'Quantité invalide'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        if product.status != 'active':
            return jsonify({'error': 'Produit non disponible'}), 400
        
        if current_user:
            # Authenticated user - save to database
            existing_item = Cart.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()
            
            if existing_item:
                existing_item.quantity += quantity
            else:
                cart_item = Cart(
                    user_id=current_user.id,
                    product_id=product_id,
                    quantity=quantity
                )
                db.session.add(cart_item)
            
            db.session.commit()
        else:
            # Anonymous user - save to session
            if 'cart' not in session:
                session['cart'] = {}
            
            cart = session['cart']
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                cart[product_id_str] += quantity
            else:
                cart[product_id_str] = quantity
            
            session['cart'] = cart
            session.modified = True
        
        return jsonify({
            'message': 'Produit ajouté au panier',
            'product_id': product_id,
            'quantity': quantity
        }), 200
        
    except Exception as e:
        if current_user:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart/update', methods=['PUT'])
def update_cart_item():
    """Update quantity of item in cart"""
    current_user = require_auth()
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        quantity = data.get('quantity')
        
        if not product_id or quantity is None:
            return jsonify({'error': 'ID du produit et quantité requis'}), 400
        
        if quantity < 0:
            return jsonify({'error': 'Quantité invalide'}), 400
        
        if current_user:
            # Authenticated user - update database
            cart_item = Cart.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()
            
            if not cart_item:
                return jsonify({'error': 'Article non trouvé dans le panier'}), 404
            
            if quantity == 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = quantity
            
            db.session.commit()
        else:
            # Anonymous user - update session
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            
            if product_id_str not in cart:
                return jsonify({'error': 'Article non trouvé dans le panier'}), 404
            
            if quantity == 0:
                del cart[product_id_str]
            else:
                cart[product_id_str] = quantity
            
            session['cart'] = cart
            session.modified = True
        
        return jsonify({
            'message': 'Panier mis à jour',
            'product_id': product_id,
            'quantity': quantity
        }), 200
        
    except Exception as e:
        if current_user:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart/remove', methods=['DELETE'])
def remove_from_cart():
    """Remove product from cart"""
    current_user = require_auth()
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'ID du produit requis'}), 400
        
        if current_user:
            # Authenticated user - remove from database
            cart_item = Cart.query.filter_by(
                user_id=current_user.id,
                product_id=product_id
            ).first()
            
            if cart_item:
                db.session.delete(cart_item)
                db.session.commit()
        else:
            # Anonymous user - remove from session
            cart = session.get('cart', {})
            product_id_str = str(product_id)
            
            if product_id_str in cart:
                del cart[product_id_str]
                session['cart'] = cart
                session.modified = True
        
        return jsonify({
            'message': 'Produit retiré du panier',
            'product_id': product_id
        }), 200
        
    except Exception as e:
        if current_user:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart/clear', methods=['DELETE'])
def clear_cart():
    """Clear all items from cart"""
    current_user = require_auth()
    
    try:
        if current_user:
            # Authenticated user - clear database cart
            Cart.query.filter_by(user_id=current_user.id).delete()
            db.session.commit()
        else:
            # Anonymous user - clear session cart
            session.pop('cart', None)
            session.modified = True
        
        return jsonify({'message': 'Panier vidé'}), 200
        
    except Exception as e:
        if current_user:
            db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/create', methods=['POST'])
def create_order():
    """Create a new order from cart or single product"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Authentification requise pour passer commande'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')  # For single product order
        shipping_address = data.get('shipping_address')
        payment_method = data.get('payment_method', 'mtn_mobile_money')
        
        if not shipping_address:
            return jsonify({'error': 'Adresse de livraison requise'}), 400
        
        orders_created = []
        
        if product_id:
            # Single product order
            product = Product.query.get(product_id)
            if not product or product.status != 'active':
                return jsonify({'error': 'Produit non disponible'}), 400
            
            if product.seller_id == current_user.id:
                return jsonify({'error': 'Vous ne pouvez pas acheter votre propre produit'}), 400
            
            order = Order(
                buyer_id=current_user.id,
                seller_id=product.seller_id,
                product_id=product_id,
                quantity=1,
                total_price=product.price,
                shipping_address=shipping_address,
                payment_method=payment_method
            )
            
            db.session.add(order)
            orders_created.append(order)
        else:
            # Cart order
            cart_items = Cart.query.filter_by(user_id=current_user.id).all()
            
            if not cart_items:
                return jsonify({'error': 'Panier vide'}), 400
            
            # Group cart items by seller
            seller_groups = {}
            for item in cart_items:
                if item.product.status != 'active':
                    continue
                
                if item.product.seller_id == current_user.id:
                    continue  # Skip own products
                
                seller_id = item.product.seller_id
                if seller_id not in seller_groups:
                    seller_groups[seller_id] = []
                seller_groups[seller_id].append(item)
            
            # Create separate orders for each seller
            for seller_id, items in seller_groups.items():
                for item in items:
                    order = Order(
                        buyer_id=current_user.id,
                        seller_id=seller_id,
                        product_id=item.product_id,
                        quantity=item.quantity,
                        total_price=item.product.price * item.quantity,
                        shipping_address=shipping_address,
                        payment_method=payment_method
                    )
                    
                    db.session.add(order)
                    orders_created.append(order)
            
            # Clear cart after order creation
            Cart.query.filter_by(user_id=current_user.id).delete()
        
        db.session.commit()
        
        # Generate tracking numbers
        for order in orders_created:
            order.tracking_number = f"KM{order.id:08d}"
        
        db.session.commit()
        
        return jsonify({
            'message': 'Commande créée avec succès',
            'orders': [order.to_dict() for order in orders_created],
            'total_orders': len(orders_created)
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/my-orders', methods=['GET'])
def get_my_orders():
    """Get current user's orders (as buyer)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Order.query.filter_by(buyer_id=current_user.id)
        
        if status_filter:
            query = query.filter_by(order_status=status_filter)
        
        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders = [order.to_dict() for order in pagination.items]
        
        return jsonify({
            'orders': orders,
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

@orders_bp.route('/my-sales', methods=['GET'])
def get_my_sales():
    """Get current user's sales (as seller)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        status_filter = request.args.get('status')
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        
        query = Order.query.filter_by(seller_id=current_user.id)
        
        if status_filter:
            query = query.filter_by(order_status=status_filter)
        
        pagination = query.order_by(Order.created_at.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        orders = [order.to_dict() for order in pagination.items]
        
        return jsonify({
            'sales': orders,
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

@orders_bp.route('/<int:order_id>', methods=['GET'])
def get_order(order_id):
    """Get specific order details"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        # Check if user is buyer or seller
        if order.buyer_id != current_user.id and order.seller_id != current_user.id:
            return jsonify({'error': 'Non autorisé'}), 403
        
        return jsonify({'order': order.to_dict()}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/<int:order_id>/status', methods=['PUT'])
def update_order_status():
    """Update order status (seller only)"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        order_id = data.get('order_id')
        new_status = data.get('status')
        
        if not order_id or not new_status:
            return jsonify({'error': 'ID de commande et statut requis'}), 400
        
        valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'cancelled']
        if new_status not in valid_statuses:
            return jsonify({'error': 'Statut invalide'}), 400
        
        order = Order.query.get(order_id)
        if not order:
            return jsonify({'error': 'Commande non trouvée'}), 404
        
        if order.seller_id != current_user.id:
            return jsonify({'error': 'Seul le vendeur peut modifier le statut'}), 403
        
        order.order_status = new_status
        order.updated_at = datetime.utcnow()
        
        # If order is confirmed and product is still active, mark as sold
        if new_status == 'confirmed' and order.product.status == 'active':
            order.product.status = 'sold'
        
        db.session.commit()
        
        return jsonify({
            'message': 'Statut de commande mis à jour',
            'order': order.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@orders_bp.route('/cart/migrate', methods=['POST'])
def migrate_cart():
    """Migrate anonymous cart to authenticated user"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        # Get session cart
        session_cart = session.get('cart', {})
        
        if not session_cart:
            return jsonify({'message': 'Aucun article à migrer'}), 200
        
        migrated_count = 0
        
        for product_id_str, quantity in session_cart.items():
            product_id = int(product_id_str)
            product = Product.query.get(product_id)
            
            if product and product.status == 'active':
                # Check if item already exists in user's cart
                existing_item = Cart.query.filter_by(
                    user_id=current_user.id,
                    product_id=product_id
                ).first()
                
                if existing_item:
                    existing_item.quantity += quantity
                else:
                    cart_item = Cart(
                        user_id=current_user.id,
                        product_id=product_id,
                        quantity=quantity
                    )
                    db.session.add(cart_item)
                
                migrated_count += 1
        
        # Clear session cart
        session.pop('cart', None)
        session.modified = True
        
        db.session.commit()
        
        return jsonify({
            'message': f'{migrated_count} articles migrés vers votre compte',
            'migrated_count': migrated_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

