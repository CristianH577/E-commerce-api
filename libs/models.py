from pydantic import BaseModel

from datetime import datetime


class Product(BaseModel):
    name_product: str
    category_product: str
    price: float = None
    stock: int = None
    description: str = None
    date: datetime = None
    id_product: int = None


class Client(BaseModel):
    name_client: str
    category_client: int
    date: datetime = None
    id_client: int = None


class Ticket(BaseModel):
    id_client: int
    date: datetime = None
    id_ticket: int = None


class Sell(BaseModel):
    id_ticket: int
    name_product: str = None
    id_product: int
    quantity: int
