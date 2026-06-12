from sqlalchemy import Column, String
from sqlalchemy.orm import relationship
from app.database import Base


class Category(Base):
    __tablename__ = "categories"

    id = Column(String, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    sub_categories = relationship("SubCategory", primaryjoin="foreign(SubCategory.category_name) == Category.name", lazy="selectin")


class SubCategory(Base):
    __tablename__ = "sub_categories"

    id = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    category_name = Column(String, nullable=False)

    category = relationship("Category", primaryjoin="foreign(SubCategory.category_name) == Category.name", lazy="selectin")
