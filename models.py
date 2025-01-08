from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship


# Base class for all SQLAlchemy models
Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    
    id = Column(Integer, primary_key=True)
    category = Column(String(100), nullable=False)
    product_name = Column(String(100), nullable=False)
    description = Column(String, nullable=True)
    price = Column(Float, nullable=False)
    stock = Column(Integer, nullable=False)
    image_url = Column(String(255), nullable=True)
    
    # Relationship with Review class
    reviews = relationship('Review', back_populates='product')

    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.product_name}', price={self.price})>"

class Review(Base):
    __tablename__ = 'reviews'
    
    id = Column(Integer, primary_key=True)
    product_id = Column(Integer, ForeignKey('products.id'))
    rating = Column(Integer, nullable=False)
    comment = Column(String, nullable=True)
    
    # Relationship with Product class
    product = relationship('Product', back_populates='reviews')

    def __repr__(self):
        return f"<Review(id={self.id}, product_id={self.product_id}, rating={self.rating})>"
