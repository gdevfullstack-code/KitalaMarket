from flask import Blueprint, request, jsonify, session, send_file
from src.models.user import db, User, Product
import requests
import os
from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont
import math

location_bp = Blueprint('location', __name__)

def require_auth():
    """Helper function to check authentication"""
    user_id = session.get('user_id')
    if not user_id:
        return None
    return User.query.get(user_id)

def generate_static_map(latitude, longitude, zoom=15, width=400, height=300, marker=True):
    """Generate a static map image using OpenStreetMap tiles"""
    try:
        # Calculate tile coordinates
        def deg2num(lat_deg, lon_deg, zoom):
            lat_rad = math.radians(lat_deg)
            n = 2.0 ** zoom
            xtile = int((lon_deg + 180.0) / 360.0 * n)
            ytile = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
            return (xtile, ytile)
        
        def num2deg(xtile, ytile, zoom):
            n = 2.0 ** zoom
            lon_deg = xtile / n * 360.0 - 180.0
            lat_rad = math.atan(math.sinh(math.pi * (1 - 2 * ytile / n)))
            lat_deg = math.degrees(lat_rad)
            return (lat_deg, lon_deg)
        
        # Get tile coordinates for the center
        center_x, center_y = deg2num(latitude, longitude, zoom)
        
        # Calculate how many tiles we need
        tiles_x = math.ceil(width / 256) + 1
        tiles_y = math.ceil(height / 256) + 1
        
        # Create a larger image to accommodate tiles
        map_image = Image.new('RGB', (tiles_x * 256, tiles_y * 256), (200, 200, 200))
        
        # Download and place tiles
        start_x = center_x - tiles_x // 2
        start_y = center_y - tiles_y // 2
        
        for i in range(tiles_x):
            for j in range(tiles_y):
                tile_x = start_x + i
                tile_y = start_y + j
                
                # Ensure tile coordinates are valid
                if tile_x < 0 or tile_y < 0 or tile_x >= 2**zoom or tile_y >= 2**zoom:
                    continue
                
                # Download tile from OpenStreetMap
                tile_url = f"https://tile.openstreetmap.org/{zoom}/{tile_x}/{tile_y}.png"
                
                try:
                    response = requests.get(tile_url, timeout=5, headers={
                        'User-Agent': 'Kitalamarket/1.0'
                    })
                    if response.status_code == 200:
                        tile_image = Image.open(BytesIO(response.content))
                        map_image.paste(tile_image, (i * 256, j * 256))
                except:
                    # If tile download fails, create a placeholder
                    placeholder = Image.new('RGB', (256, 256), (220, 220, 220))
                    draw = ImageDraw.Draw(placeholder)
                    draw.text((128, 128), "Map", fill=(100, 100, 100), anchor="mm")
                    map_image.paste(placeholder, (i * 256, j * 256))
        
        # Crop to desired size
        crop_x = (map_image.width - width) // 2
        crop_y = (map_image.height - height) // 2
        map_image = map_image.crop((crop_x, crop_y, crop_x + width, crop_y + height))
        
        # Add marker if requested
        if marker:
            draw = ImageDraw.Draw(map_image)
            marker_x = width // 2
            marker_y = height // 2
            
            # Draw marker pin
            pin_size = 20
            draw.ellipse([
                marker_x - pin_size//2, marker_y - pin_size//2,
                marker_x + pin_size//2, marker_y + pin_size//2
            ], fill='red', outline='darkred', width=2)
            
            # Draw marker point
            draw.ellipse([
                marker_x - 3, marker_y - 3,
                marker_x + 3, marker_y + 3
            ], fill='white')
        
        return map_image
        
    except Exception as e:
        # Return a simple placeholder image if map generation fails
        placeholder = Image.new('RGB', (width, height), (240, 240, 240))
        draw = ImageDraw.Draw(placeholder)
        draw.text((width//2, height//2), f"Carte\n{latitude:.4f}, {longitude:.4f}", 
                 fill=(100, 100, 100), anchor="mm")
        return placeholder

@location_bp.route('/geocode', methods=['POST'])
def geocode_address():
    """Convert address to coordinates using Nominatim API"""
    try:
        data = request.get_json()
        address = data.get('address')
        
        if not address:
            return jsonify({'error': 'Adresse requise'}), 400
        
        # Use Nominatim API for geocoding
        url = "https://nominatim.openstreetmap.org/search"
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'countrycodes': 'fr'  # Limit to France
        }
        
        headers = {
            'User-Agent': 'Kitalamarket/1.0 (contact@kitalamarket.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            results = response.json()
            if results:
                result = results[0]
                return jsonify({
                    'latitude': float(result['lat']),
                    'longitude': float(result['lon']),
                    'display_name': result['display_name'],
                    'address': address
                }), 200
            else:
                return jsonify({'error': 'Adresse non trouvée'}), 404
        else:
            return jsonify({'error': 'Erreur du service de géocodage'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/reverse-geocode', methods=['POST'])
def reverse_geocode():
    """Convert coordinates to address using Nominatim API"""
    try:
        data = request.get_json()
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if latitude is None or longitude is None:
            return jsonify({'error': 'Latitude et longitude requises'}), 400
        
        # Use Nominatim API for reverse geocoding
        url = "https://nominatim.openstreetmap.org/reverse"
        params = {
            'lat': latitude,
            'lon': longitude,
            'format': 'json',
            'zoom': 18,
            'addressdetails': 1
        }
        
        headers = {
            'User-Agent': 'Kitalamarket/1.0 (contact@kitalamarket.com)'
        }
        
        response = requests.get(url, params=params, headers=headers, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            return jsonify({
                'latitude': latitude,
                'longitude': longitude,
                'display_name': result.get('display_name', ''),
                'address': result.get('address', {})
            }), 200
        else:
            return jsonify({'error': 'Erreur du service de géocodage inverse'}), 500
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/static-map', methods=['GET'])
def get_static_map():
    """Generate and return a static map image"""
    try:
        latitude = float(request.args.get('lat', 48.8566))
        longitude = float(request.args.get('lon', 2.3522))
        zoom = int(request.args.get('zoom', 15))
        width = int(request.args.get('width', 400))
        height = int(request.args.get('height', 300))
        marker = request.args.get('marker', 'true').lower() == 'true'
        
        # Validate parameters
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({'error': 'Coordonnées invalides'}), 400
        
        if not (1 <= zoom <= 18):
            zoom = 15
        
        if not (100 <= width <= 1000) or not (100 <= height <= 1000):
            width, height = 400, 300
        
        # Generate map image
        map_image = generate_static_map(latitude, longitude, zoom, width, height, marker)
        
        # Save to BytesIO
        img_io = BytesIO()
        map_image.save(img_io, 'PNG')
        img_io.seek(0)
        
        return send_file(img_io, mimetype='image/png')
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/static-map-base64', methods=['GET'])
def get_static_map_base64():
    """Generate and return a static map image as base64"""
    try:
        latitude = float(request.args.get('lat', 48.8566))
        longitude = float(request.args.get('lon', 2.3522))
        zoom = int(request.args.get('zoom', 15))
        width = int(request.args.get('width', 400))
        height = int(request.args.get('height', 300))
        marker = request.args.get('marker', 'true').lower() == 'true'
        
        # Validate parameters
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            return jsonify({'error': 'Coordonnées invalides'}), 400
        
        if not (1 <= zoom <= 18):
            zoom = 15
        
        if not (100 <= width <= 1000) or not (100 <= height <= 1000):
            width, height = 400, 300
        
        # Generate map image
        map_image = generate_static_map(latitude, longitude, zoom, width, height, marker)
        
        # Convert to base64
        img_io = BytesIO()
        map_image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        return jsonify({
            'image': f'data:image/png;base64,{img_base64}',
            'latitude': latitude,
            'longitude': longitude,
            'zoom': zoom,
            'width': width,
            'height': height
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/product-location/<int:product_id>', methods=['GET'])
def get_product_location(product_id):
    """Get location information and map for a specific product"""
    try:
        product = Product.query.get(product_id)
        if not product:
            return jsonify({'error': 'Produit non trouvé'}), 404
        
        if not product.latitude or not product.longitude:
            return jsonify({'error': 'Localisation non disponible pour ce produit'}), 404
        
        # Generate map image
        map_image = generate_static_map(product.latitude, product.longitude, 15, 400, 300, True)
        
        # Convert to base64
        img_io = BytesIO()
        map_image.save(img_io, 'PNG')
        img_io.seek(0)
        img_base64 = base64.b64encode(img_io.getvalue()).decode()
        
        return jsonify({
            'product_id': product_id,
            'latitude': product.latitude,
            'longitude': product.longitude,
            'location': product.location,
            'map_image': f'data:image/png;base64,{img_base64}',
            'coordinates_display': f"{product.latitude:.6f}, {product.longitude:.6f}"
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@location_bp.route('/nearby-products', methods=['GET'])
def get_nearby_products():
    """Get products near a specific location"""
    try:
        latitude = float(request.args.get('lat'))
        longitude = float(request.args.get('lon'))
        radius = float(request.args.get('radius', 10))  # km
        
        # Simple distance calculation (not perfectly accurate but good enough)
        # 1 degree ≈ 111 km
        lat_range = radius / 111.0
        lon_range = radius / (111.0 * math.cos(math.radians(latitude)))
        
        products = Product.query.filter(
            Product.latitude.between(latitude - lat_range, latitude + lat_range),
            Product.longitude.between(longitude - lon_range, longitude + lon_range),
            Product.status == 'active'
        ).all()
        
        # Calculate actual distances and filter
        nearby_products = []
        for product in products:
            if product.latitude and product.longitude:
                # Haversine formula for distance calculation
                dlat = math.radians(product.latitude - latitude)
                dlon = math.radians(product.longitude - longitude)
                a = (math.sin(dlat/2)**2 + 
                     math.cos(math.radians(latitude)) * math.cos(math.radians(product.latitude)) * 
                     math.sin(dlon/2)**2)
                c = 2 * math.asin(math.sqrt(a))
                distance = 6371 * c  # Earth radius in km
                
                if distance <= radius:
                    product_data = product.to_dict()
                    product_data['distance'] = round(distance, 2)
                    nearby_products.append(product_data)
        
        # Sort by distance
        nearby_products.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'products': nearby_products,
            'count': len(nearby_products),
            'search_center': {'latitude': latitude, 'longitude': longitude},
            'radius': radius
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

