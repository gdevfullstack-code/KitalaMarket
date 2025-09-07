from flask import Blueprint, request, jsonify, session
from src.models.user import db, Product, User, Favorite, Cart
from sqlalchemy import or_, and_, func, desc, asc
import json
from datetime import datetime, timedelta

products_bp = Blueprint('products', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

@products_bp.route('/', methods=['GET'])
def get_products():
    """Get products with filtering, sorting and pagination"""
    try:
        # Get query parameters
        page = int(request.args.get('page', 1))
        per_page = min(int(request.args.get('per_page', 20)), 100)
        category = request.args.get('category')
        search = request.args.get('search')
        min_price = request.args.get('min_price', type=float)
        max_price = request.args.get('max_price', type=float)
        condition = request.args.get('condition')
        brand = request.args.get('brand')
        location = request.args.get('location')
        sort_by = request.args.get('sort_by', 'created_at')
        sort_order = request.args.get('sort_order', 'desc')
        
        # Build query
        query = Product.query.filter(Product.status == 'active')
        
        # Apply filters
        if category:
            query = query.filter(Product.category == category)
        
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                or_(
                    Product.title.ilike(search_term),
                    Product.description.ilike(search_term),
                    Product.brand.ilike(search_term)
                )
            )
        
        if min_price is not None:
            query = query.filter(Product.price >= min_price)
        
        if max_price is not None:
            query = query.filter(Product.price <= max_price)
        
        if condition:
            query = query.filter(Product.condition == condition)
        
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        
        if location:
            query = query.filter(Product.location.ilike(f"%{location}%"))
        
        # Apply sorting
        if sort_by == 'price':
            if sort_order == 'asc':
                query = query.order_by(asc(Product.price))
            else:
                query = query.order_by(desc(Product.price))
        elif sort_by == 'created_at':
            if sort_order == 'asc':
                query = query.order_by(asc(Product.created_at))
            else:
                query = query.order_by(desc(Product.created_at))
        elif sort_by == 'views':
            query = query.order_by(desc(Product.views))
        elif sort_by == 'favorites':
            query = query.order_by(desc(Product.favorites_count))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        products = [product.to_dict() for product in pagination.items]
        
        return jsonify({
            'products': products,
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

@products_bp.route('/<int:product_id>', methods=['GET'])
def get_product(product_id):
    """Get a specific product by ID"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        # Increment view count
        product.views += 1
        db.session.commit()
        
        # Get similar products (same category, different seller)
        similar_products = Product.query.filter(
            Product.category == product.category,
            Product.seller_id != product.seller_id,
            Product.status == 'active',
            Product.id != product.id
        ).limit(6).all()
        
        return jsonify({
            'product': product.to_dict(),
            'similar_products': [p.to_dict() for p in similar_products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/compare', methods=['POST'])
def compare_products():
    """Compare multiple products"""
    try:
        data = request.get_json()
        product_ids = data.get('product_ids', [])
        
        if not product_ids or len(product_ids) < 2:
            return jsonify({'error': 'Au moins 2 produits requis pour la comparaison'}), 400
        
        if len(product_ids) > 5:
            return jsonify({'error': 'Maximum 5 produits pour la comparaison'}), 400
        
        products = Product.query.filter(
            Product.id.in_(product_ids),
            Product.status == 'active'
        ).all()
        
        if len(products) != len(product_ids):
            return jsonify({'error': 'Certains produits sont introuvables'}), 404
        
        # Calculate comparison metrics
        prices = [p.price for p in products]
        comparison_data = {
            'products': [p.to_dict() for p in products],
            'price_analysis': {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': sum(prices) / len(prices),
                'price_difference': max(prices) - min(prices),
                'best_value': min(products, key=lambda p: p.price).to_dict(),
                'most_expensive': max(products, key=lambda p: p.price).to_dict()
            },
            'comparison_matrix': []
        }
        
        # Create comparison matrix
        for product in products:
            comparison_row = {
                'product_id': product.id,
                'title': product.title,
                'price': product.price,
                'condition': product.condition,
                'brand': product.brand,
                'location': product.location,
                'seller_rating': product.seller.rating if product.seller else 0,
                'views': product.views,
                'favorites': product.favorites_count,
                'created_at': product.created_at.isoformat()
            }
            comparison_data['comparison_matrix'].append(comparison_row)
        
        return jsonify(comparison_data), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/price-history/<int:product_id>', methods=['GET'])
def get_price_history(product_id):
    """Get price history for a product (simulated data)"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        # Simulate price history (in real app, this would come from a price_history table)
        current_price = product.price
        history = []
        
        # Generate 30 days of simulated price history
        for i in range(30, 0, -1):
            date = datetime.utcnow() - timedelta(days=i)
            # Simulate price variations (±10% of current price)
            import random
            variation = random.uniform(-0.1, 0.1)
            historical_price = current_price * (1 + variation)
            
            history.append({
                'date': date.isoformat(),
                'price': round(historical_price, 2)
            })
        
        # Add current price
        history.append({
            'date': datetime.utcnow().isoformat(),
            'price': current_price
        })
        
        return jsonify({
            'product_id': product_id,
            'current_price': current_price,
            'price_history': history,
            'price_trend': 'stable'  # Could be 'increasing', 'decreasing', 'stable'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/market-analysis', methods=['GET'])
def get_market_analysis():
    """Get market analysis for products"""
    try:
        category = request.args.get('category')
        brand = request.args.get('brand')
        
        # Build base query
        query = Product.query.filter(Product.status == 'active')
        
        if category:
            query = query.filter(Product.category == category)
        
        if brand:
            query = query.filter(Product.brand.ilike(f"%{brand}%"))
        
        products = query.all()
        
        if not products:
            return jsonify({'error': 'Aucun produit trouvé pour l\'analyse'}), 404
        
        # Calculate market statistics
        prices = [p.price for p in products]
        prices.sort()
        
        analysis = {
            'total_products': len(products),
            'price_statistics': {
                'min_price': min(prices),
                'max_price': max(prices),
                'avg_price': round(sum(prices) / len(prices), 2),
                'median_price': prices[len(prices) // 2] if prices else 0,
                'price_range': max(prices) - min(prices)
            },
            'condition_distribution': {},
            'brand_distribution': {},
            'location_distribution': {},
            'price_ranges': {
                'under_50': len([p for p in prices if p < 50]),
                '50_to_100': len([p for p in prices if 50 <= p < 100]),
                '100_to_500': len([p for p in prices if 100 <= p < 500]),
                '500_to_1000': len([p for p in prices if 500 <= p < 1000]),
                'over_1000': len([p for p in prices if p >= 1000])
            }
        }
        
        # Calculate distributions
        for product in products:
            # Condition distribution
            condition = product.condition
            analysis['condition_distribution'][condition] = analysis['condition_distribution'].get(condition, 0) + 1
            
            # Brand distribution
            if product.brand:
                brand = product.brand
                analysis['brand_distribution'][brand] = analysis['brand_distribution'].get(brand, 0) + 1
            
            # Location distribution
            if product.location:
                location = product.location.split(',')[0].strip()  # Get city part
                analysis['location_distribution'][location] = analysis['location_distribution'].get(location, 0) + 1
        
        return jsonify(analysis), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/categories', methods=['GET'])
def get_categories():
    """Get all available categories with product counts"""
    try:
        categories = db.session.query(
            Product.category,
            func.count(Product.id).label('count')
        ).filter(Product.status == 'active').group_by(Product.category).all()
        
        category_list = [
            {'name': cat.category, 'count': cat.count}
            for cat in categories
        ]
        
        return jsonify({'categories': category_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/brands', methods=['GET'])
def get_brands():
    """Get all available brands with product counts"""
    try:
        category = request.args.get('category')
        
        query = db.session.query(
            Product.brand,
            func.count(Product.id).label('count')
        ).filter(
            Product.status == 'active',
            Product.brand.isnot(None),
            Product.brand != ''
        )
        
        if category:
            query = query.filter(Product.category == category)
        
        brands = query.group_by(Product.brand).all()
        
        brand_list = [
            {'name': brand.brand, 'count': brand.count}
            for brand in brands
        ]
        
        return jsonify({'brands': brand_list}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/trending', methods=['GET'])
def get_trending_products():
    """Get trending products based on views and favorites"""
    try:
        limit = min(int(request.args.get('limit', 10)), 50)
        
        # Get products with high views and favorites in the last 7 days
        week_ago = datetime.utcnow() - timedelta(days=7)
        
        trending_products = Product.query.filter(
            Product.status == 'active',
            Product.created_at >= week_ago
        ).order_by(
            desc(Product.views + Product.favorites_count * 2)
        ).limit(limit).all()
        
        return jsonify({
            'trending_products': [p.to_dict() for p in trending_products]
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@products_bp.route('/favorites', methods=['POST'])
def toggle_favorite():
    """Add or remove product from favorites"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        if not product_id:
            return jsonify({'error': 'ID du produit requis'}), 400
        
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        # Check if already in favorites
        existing_favorite = Favorite.query.filter_by(
            user_id=current_user.id,
            product_id=product_id
        ).first()
        
        if existing_favorite:
            # Remove from favorites
            db.session.delete(existing_favorite)
            product.favorites_count = max(0, product.favorites_count - 1)
            action = 'removed'
        else:
            # Add to favorites
            favorite = Favorite(user_id=current_user.id, product_id=product_id)
            db.session.add(favorite)
            product.favorites_count += 1
            action = 'added'
        
        db.session.commit()
        
        return jsonify({
            'message': f'Produit {action} des favoris',
            'action': action,
            'favorites_count': product.favorites_count
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@products_bp.route('/user-favorites', methods=['GET'])
def get_user_favorites():
    """Get current user's favorite products"""
    current_user = require_auth()
    if not current_user:
        return jsonify({'error': 'Non authentifié'}), 401
    
    try:
        favorites = Favorite.query.filter_by(user_id=current_user.id).all()
        favorite_products = [fav.product.to_dict() for fav in favorites if fav.product.status == 'active']
        
        return jsonify({'favorites': favorite_products}), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

