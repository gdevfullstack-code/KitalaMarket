import os
import sys
# DON'T CHANGE THIS !!!
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from flask import Flask, send_from_directory
from flask_cors import CORS
from src.models.user import db
from src.routes.user import user_bp
from src.routes.auth import auth_bp
from src.routes.oauth import oauth_bp
from src.routes.products import products_bp
from src.routes.messages import messages_bp
from src.routes.orders import orders_bp
from src.routes.location import location_bp
from src.routes.payment import payment_bp
from src.routes.premium import premium_bp

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(__file__), 'static'))
app.config['SECRET_KEY'] = 'asdf#FGSgvasgf$5$WGT'

# Enable CORS for all routes
CORS(app, origins="*")

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(oauth_bp, url_prefix='/api/oauth')
app.register_blueprint(user_bp, url_prefix='/api/users')
app.register_blueprint(products_bp, url_prefix='/api/products')
app.register_blueprint(messages_bp, url_prefix='/api/messages')
app.register_blueprint(orders_bp, url_prefix='/api/orders')
app.register_blueprint(location_bp, url_prefix='/api/location')
app.register_blueprint(payment_bp, url_prefix='/api/payment')
app.register_blueprint(premium_bp, url_prefix='/api/premium')

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"sqlite:///{os.path.join(os.path.dirname(__file__), 'database', 'app.db')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

with app.app_context():
    db.create_all()
    
    # Create sample data if database is empty
    from src.models.user import User, Product, Message
    if User.query.count() == 0:
        # Create sample users
        user1 = User(
            username='jeandupont',
            email='jean.dupont@email.com',
            first_name='Jean',
            last_name='Dupont',
            user_type='both',
            phone='+33 6 12 34 56 78',
            address='123 Rue de la Paix, 75001 Paris',
            rating=4.8,
            total_reviews=127,
            is_verified=True
        )
        user1.set_password('password123')
        
        user2 = User(
            username='marieleblanc',
            email='marie.leblanc@email.com',
            first_name='Marie',
            last_name='Leblanc',
            user_type='buyer',
            phone='+33 6 98 76 54 32',
            address='456 Avenue des Champs, 69000 Lyon',
            rating=4.9,
            total_reviews=89,
            is_verified=True
        )
        user2.set_password('password123')
        
        user3 = User(
            username='pierremartin',
            email='pierre.martin@email.com',
            first_name='Pierre',
            last_name='Martin',
            user_type='seller',
            phone='+33 6 11 22 33 44',
            address='789 Boulevard Saint-Michel, 13000 Marseille',
            rating=4.7,
            total_reviews=156,
            is_verified=True
        )
        user3.set_password('password123')
        
        db.session.add_all([user1, user2, user3])
        db.session.commit()
        
        # Create sample products
        product1 = Product(
            title='iPhone 13 Pro Max 256GB Bleu',
            description='iPhone 13 Pro Max en excellent état, utilisé avec précaution. Livré avec boîte et accessoires d\'origine.',
            price=1099.0,
            category='electronique',
            brand='Apple',
            condition='excellent',
            color='Bleu',
            location='Paris 15e',
            latitude=48.8566,
            longitude=2.3522,
            images='["iphone1.jpg", "iphone2.jpg", "iphone3.jpg"]',
            status='active',
            views=234,
            favorites_count=12,
            seller_id=user1.id
        )
        
        product2 = Product(
            title='Nike Air Max 270 Blanc',
            description='Baskets Nike Air Max 270 en très bon état, portées quelques fois seulement. Taille 42.',
            price=89.0,
            category='mode',
            brand='Nike',
            condition='good',
            size='42',
            color='Blanc',
            location='Lyon 3e',
            latitude=45.7640,
            longitude=4.8357,
            images='["nike1.jpg", "nike2.jpg"]',
            status='sold',
            views=156,
            favorites_count=8,
            seller_id=user1.id
        )
        
        product3 = Product(
            title='MacBook Air M2 13" 256GB',
            description='MacBook Air M2 neuf, encore sous garantie. Parfait pour le travail et les études.',
            price=999.0,
            category='electronique',
            brand='Apple',
            condition='new',
            color='Gris sidéral',
            location='Marseille 1er',
            latitude=43.2965,
            longitude=5.3698,
            images='["macbook1.jpg", "macbook2.jpg", "macbook3.jpg"]',
            status='active',
            views=89,
            favorites_count=15,
            seller_id=user3.id
        )
        
        db.session.add_all([product1, product2, product3])
        db.session.commit()
        
        # Create sample messages
        message1 = Message(
            content='Bonjour ! Je suis intéressée par votre iPhone 13 Pro Max. Est-il toujours disponible ?',
            sender_id=user2.id,
            receiver_id=user1.id,
            product_id=product1.id
        )
        
        message2 = Message(
            content='Bonjour Marie ! Oui, il est toujours disponible 😊',
            sender_id=user1.id,
            receiver_id=user2.id,
            product_id=product1.id
        )
        
        message3 = Message(
            content='Parfait ! Pouvez-vous me dire dans quel état il est exactement ?',
            sender_id=user2.id,
            receiver_id=user1.id,
            product_id=product1.id
        )
        
        db.session.add_all([message1, message2, message3])
        db.session.commit()

@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def serve(path):
    static_folder_path = app.static_folder
    if static_folder_path is None:
        return "Static folder not configured", 404

    if path != "" and os.path.exists(os.path.join(static_folder_path, path)):
        return send_from_directory(static_folder_path, path)
    else:
        index_path = os.path.join(static_folder_path, 'index.html')
        if os.path.exists(index_path):
            return send_from_directory(static_folder_path, 'index.html')
        else:
            return "index.html not found", 404

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

