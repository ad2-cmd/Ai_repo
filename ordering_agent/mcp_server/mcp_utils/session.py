from enum import Enum
from typing import Any, Dict, List, Literal

from mcp_utils.payment_methods import PaymentMethod
from mcp_utils.shipping_method import ShippingMethod


class Singleton(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super(
                Singleton, cls).__call__(*args, **kwargs)
        return cls._instances[cls]


class OrderState(Enum):
    CUSTOMER_IDENTIFICATION = "customer_identification"
    PRODUCT_SELECTION = "product_selection"
    SHIPPING_METHOD = "shipping_method_selection"
    SHIPPING_ADDRESS = "shipping_address_selection"
    PAYMENT_ADDRESS = "payment_address_selection"
    PAYMENT_METHOD = "payment_method_selection"
    ORDER_CONFIRMATION = "order_confirmation"
    ORDER_FINALIZATION = "order_finalization"


OrderStateLiteral = Literal[
    "customer_identification",
    "product_selection",
    "shipping_method_selection",
    "shipping_address_selection",
    "payment_address_selection",
    "payment_method_selection",
    "order_confirmation",
    "order_finalization"
]


class Session:
    # --- Mandatory attributes ---
    session_id: str
    customer: Dict[str, Any]
    products: List[Dict[str, Any]]
    shipping_method: Dict[str, Any]
    shipping_address: Dict[str, str]
    payment_address: Dict[str, str]
    payment_method: Dict[str, Any]
    order_state: str

    # --- Utility attributes ---
    found_customer: Dict[str, Any]
    found_products: List[Dict[str, Any]]
    found_shipping_methods: List[ShippingMethod]
    found_payment_methods: List[PaymentMethod]
    found_addresses: List[Dict[str, Any]]

    def __init__(self, session_id):
        self.session_id = session_id
        self.customer = {}
        self.products = []
        self.shipping_method = {}
        self.shipping_address = {}
        self.payment_address = {}
        self.payment_method = {}
        self.order_state = OrderState.CUSTOMER_IDENTIFICATION.value

        self.found_customer = {}
        self.found_products = []
        self.found_shipping_methods = []
        self.found_payment_methods = []
        self.found_addresses = []

    def dump_session(self):
        return {
            "session_id": self.session_id,
            "customer": self.customer,
            "products": self.products,
            "shipping_method": self.shipping_method,
            "shipping_address": self.shipping_address,
            "payment_address": self.payment_address,
            "payment_method": self.payment_method,
            "order_state": self.order_state
        }

    def get_missing_data_types(self):
        missing_data_types = []
        if not self.customer:
            missing_data_types.append('customer')
        if len(self.products) == 0:
            missing_data_types.append('products')
        if not self.shipping_method:
            missing_data_types.append('shipping_method')
        if not self.shipping_address:
            missing_data_types.append('shipping_address')
        if not self.payment_address:
            missing_data_types.append('payment_address')
        if not self.payment_method:
            missing_data_types.append('payment_method')

        return missing_data_types


class SessionManager(object, metaclass=Singleton):
    sessions: Dict[str, Session]

    def __init__(self):
        self.sessions: Dict[str, Session] = {}

    def get_session(self, session_id):
        return self.sessions.setdefault(session_id, Session(session_id))
