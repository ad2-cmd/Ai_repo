import os
from qdrant.util import get_qdrant_client


def get_all_payment_methods():
    payment_methods_raw = get_qdrant_client().scroll(
        collection_name=os.getenv(
            'QDRANT_COLLECTION_PAYMENT_METHODS', 'payment-methods-test'),
        limit=20,
        with_payload=True,
        with_vectors=False,
    )

    return [method.payload for method in payment_methods_raw[0]]
