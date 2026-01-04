from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey, func
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    name = Column(String, nullable=False)
    phone = Column(String)
    delivery_method = Column(String)  # СДЭК, Почта РФ, Ozon и т.д.
    pickup_address = Column(String)  # Полный адрес: город, улица, дом
    ref_source = Column(String, default="direct")  # Откуда пришёл: insta, tg_ad, friend
    registered_at = Column(DateTime, default=func.now())
    is_active = Column(Boolean, default=True)

    orders = relationship("Order", back_populates="user")


class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    article = Column(String, unique=True, nullable=False)
    name_kr = Column(String)
    name_en = Column(String, nullable=False)
    name = Column(String)
    brand = Column(String, default="Amore Pacific")  # ✅ Добавьте это
    price = Column(Integer, nullable=False)
    description = Column(String)
    image_url = Column(String)
    category = Column(String, default="Разное")
    volume = Column(String)
    country = Column(String, default="Корея")
    in_stock = Column(Integer, default=10)

    orders = relationship("Order", back_populates="product")


class Order(Base):
    __tablename__ = 'orders'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    total_price = Column(Integer)  # quantity * price
    status = Column(String, default="ожидает оплаты")  # ожидает, оплачен, отменён
    payment_proof = Column(String)  # путь к файлу чека
    created_at = Column(DateTime, default=func.now())

    user = relationship("User", back_populates="orders")
    product = relationship("Product", back_populates="orders")