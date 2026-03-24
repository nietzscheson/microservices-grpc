from sqlalchemy import Column, Integer, String

from src.database import Base


class Product(Base):
    __tablename__ = "product"
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    created_by = Column(Integer)
