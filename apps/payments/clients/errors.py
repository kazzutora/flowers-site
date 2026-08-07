class PaymentProviderError(Exception):
    """Raised when a payment provider call fails (network, rejected, timeout)."""
