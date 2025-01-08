from flask import Flask, render_template, request, redirect, url_for, send_from_directory, jsonify
from werkzeug.utils import secure_filename
import os
from flask_sqlalchemy import SQLAlchemy
import re
from flask_migrate import Migrate

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads/'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///yourdatabase.db'  # Replace with your actual database URI
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# SQLAlchemy models
class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(100), nullable=False)
    product_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String, nullable=True)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image_url = db.Column(db.String(255), nullable=True)
    reviews = db.relationship('Review', back_populates='product')

class Review(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.String, nullable=True)
    product = db.relationship('Product', back_populates='reviews')

# Ensure all tables are created
with app.app_context():
    db.create_all()

@app.route('/')
def home():
    try:
        products = Product.query.all()
        from collections import defaultdict
        products_by_category = defaultdict(list)
        for product in products:
            products_by_category[product.category].append(product)
        return render_template('index.html', products_by_category=products_by_category)
    except Exception as e:
        app.logger.error(f"Error retrieving products: {e}")
        return "An error occurred while retrieving products."

@app.route('/product_form')
def product_form():
    return render_template('product_form.html')

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/chat', methods=['POST'])
def chat():
    try:
        message = request.json.get('message')
        if not message:
            app.logger.error('No message received in the chat request.')
            return jsonify({'response': 'No message received.'}), 400
        
        # Log incoming message
        app.logger.info(f'Received message: {message}')
        
        # Process the message to determine intent
        response = process_chat_message(message)
        
        # Log response
        app.logger.info(f'Response generated: {response}')
        
        # Ensure response is a dictionary
        if isinstance(response, dict):
            return jsonify({'response': response['response'], 'options': response.get('options', [])})
        else:
            return jsonify({'response': 'Sorry, something went wrong.'}), 500
    
    except Exception as e:
        app.logger.error(f"Error processing chat message: {e}", exc_info=True)
        return jsonify({'response': 'Sorry, there was an error processing your request.'}), 500

@app.route('/product/new', methods=['GET', 'POST'])
def new_product():
    if request.method == 'POST':
        try:
            category = request.form['category']
            product_name = request.form['product_name']
            price = float(request.form['price'])
            description = request.form['description']
            stock = int(request.form['stock'])
            
            # Validate inputs
            if not category or not product_name or price <= 0 or stock < 0:
                return "Invalid product data. Please check your input."

            image_url = ''
            if 'image' in request.files:
                image = request.files['image']
                if image.filename != '':
                    # Ensure upload folder exists
                    if not os.path.exists(app.config['UPLOAD_FOLDER']):
                        os.makedirs(app.config['UPLOAD_FOLDER'])
                    
                    filename = secure_filename(image.filename)
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                    image.save(file_path)
                    image_url = url_for('uploaded_file', filename=filename)

            new_product = Product(
                category=category,
                product_name=product_name,
                price=price,
                description=description,
                stock=stock,
                image_url=image_url
            )
            db.session.add(new_product)
            db.session.commit()

            return redirect(url_for('home'))
        except Exception as e:
            app.logger.error(f"Error adding new product: {e}", exc_info=True)
            return "An error occurred while adding the new product."

    return render_template('product_form.html')

def process_chat_message(message):
    # Convert message to lowercase for easier matching
    message = message.lower()
    
    # Define rule-based patterns
    patterns = [
        # Pattern to get categories
        (r'categories|category|list of categories', lambda _: get_categories()),  # Fixed this line
        
        # Pattern to get products in a specific category
        (r'products in (\w+)', lambda match: get_products_in_category(match.group(1))),
        
        # Pattern to get reviews of a specific product
        (r'review of (\w+)', lambda match: get_product_reviews(match.group(1))),
        
        # Additional patterns for specific product details
        (r'product details of (\w+)', lambda match: get_product_details(match.group(1))),
    ]
    
    # Loop through patterns to find a match
    for pattern, func in patterns:
        match = re.search(pattern, message)
        if match:
            return func(match)
    
    # Default response with options
    options = ["Show categories", "View products in a category", "Check product reviews"]
    return {
        'response': "What would you like to do next? Choose an option below:",
        'options': options
    }

def get_categories():
    try:
        categories = db.session.query(Product.category.distinct()).all()
        category_list = [category[0] for category in categories]
        return {
            'response': f"Available categories are: {', '.join(category_list)}",
            'options': [f"Products in {category}" for category in category_list]
        }
    except Exception as e:
        app.logger.error(f"Error retrieving categories: {e}")
        return {'response': "An error occurred while retrieving categories."}

def get_products_in_category(category):
    try:
        # Use ilike for case-insensitive matching
        products = Product.query.filter(Product.category.ilike(f"%{category}%")).all()
        if products:
            product_list = [product.product_name for product in products]
            return {
                'response': f"Products available in {category} are: {', '.join(product_list)}",
                'options': [f"Product details of {product_name}" for product_name in product_list]
            }
        return {'response': f"No products found in the category '{category}'."}
    except Exception as e:
        app.logger.error(f"Error retrieving products: {e}")
        return {'response': "An error occurred while retrieving products."}


def get_product_reviews(product_name):
    try:
        product = Product.query.filter(Product.product_name.ilike(f"%{product_name}%")).first()
        if product:
            reviews = Review.query.filter_by(product_id=product.id).all()
            review_text = "\n".join([f"Rating: {r.rating}, Comment: {r.comment}" for r in reviews])
            return {'response': f"Reviews for {product.product_name}:\n{review_text}"}
        return {'response': f"No reviews found for the product '{product_name}'."}
    except Exception as e:
        app.logger.error(f"Error retrieving reviews: {e}")
        return {'response': "An error occurred while retrieving reviews."}

def get_product_details(product_name):
    try:
        product = Product.query.filter(Product.product_name.ilike(f"%{product_name}%")).first()
        if product:
            return {'response': f"Details for {product.product_name}: Price: {product.price}, Stock: {product.stock}, Description: {product.description}"}
        return {'response': f"No details found for the product '{product_name}'."}
    except Exception as e:
        app.logger.error(f"Error retrieving product details: {e}")
        return {'response': "An error occurred while retrieving product details."}

if __name__ == '__main__':
    app.run(debug=True)
