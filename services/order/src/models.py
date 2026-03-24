from sqlalchemy import Column, Integer, String

from src.database import Base


class Order(Base):
    __tablename__ = "order"
    id = Column(Integer, primary_key=True)
    name = Column(String(128))
    created_by = Column(Integer)
    product = Column(Integer)
