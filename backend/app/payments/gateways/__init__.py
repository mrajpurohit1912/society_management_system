from app.payments.models import PaymentMethod
from app.payments.gateways.base import BasePaymentGateway
from app.payments.gateways.mock import MockPaymentGateway
from app.payments.gateways.manual import ManualOfflineGateway
from app.payments.gateways.razorpay import RazorpayGateway

__all__ = [
    "BasePaymentGateway",
    "MockPaymentGateway",
    "ManualOfflineGateway",
    "RazorpayGateway",
    "get_payment_gateway",
]


def get_payment_gateway(method: str) -> BasePaymentGateway:
    """
    Factory method to instantiate the requested payment gateway adapter.
    """
    if method == PaymentMethod.ONLINE_RAZORPAY.value:
        return RazorpayGateway()
    elif method in (
        PaymentMethod.OFFLINE_UPI_NEFT.value,
        PaymentMethod.OFFLINE_CHEQUE.value,
        PaymentMethod.OFFLINE_CASH.value,
    ):
        return ManualOfflineGateway()
    else:
        # Default to MockPaymentGateway for ONLINE_MOCK or test runs
        return MockPaymentGateway()
