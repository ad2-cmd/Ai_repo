import os
import httpx
from pathlib import Path

# Configuration
qdrant_base_url = os.getenv('QDRANT_URL', 'http://localhost:6333')
snapshots_path = Path('database_migrations/qdrant_snapshots')

# Collection mapping
collection_map = {
    'products.snapshot': os.getenv('QDRANT_COLLECTION_PRODUCTS', 'products-test'),
    'customers.snapshot': os.getenv('QDRANT_COLLECTION_CUSTOMERS', 'customers-test'),
    'shipping-methods.snapshot': os.getenv('QDRANT_COLLECTION_SHIPPING_METHODS', 'shipping-methods-test'),
    'payment-methods.snapshot': os.getenv('QDRANT_COLLECTION_PAYMENT_METHODS', 'payment-methods-test'),
}


def get_collection_name(filename):
    """Determine collection name from filename."""
    for key, collection in collection_map.items():
        if key in filename or key.split('.')[0] in filename.lower():
            return collection
    return None


def upload_snapshot(snapshot_filename, collection_name=None):
    """Upload snapshot to Qdrant collection."""
    snapshot_file = snapshots_path / snapshot_filename
    if not snapshot_file.exists():
        raise FileNotFoundError(f"Snapshot file not found: {snapshot_file}")

    # Determine collection if not provided
    if not collection_name:
        collection_name = get_collection_name(snapshot_filename)
        if not collection_name:
            raise ValueError(
                f"Cannot determine collection from: {snapshot_filename}")

    url = f"{qdrant_base_url}/collections/{collection_name}/snapshots/upload"

    with open(snapshot_file, 'rb') as f:
        files = {"snapshot": (snapshot_file.name, f,
                              "application/octet-stream")}
        with httpx.Client(timeout=300.0) as client:
            response = client.post(
                url, params={"priority": "snapshot"}, files=files)
            response.raise_for_status()
            return response.json()


def upload_multiple_snapshots(pattern="*.snapshot"):
    """Upload multiple snapshots from directory."""
    results = {}
    for snapshot_file in snapshots_path.glob(pattern):
        try:
            result = upload_snapshot(snapshot_file.name)
            results[snapshot_file.name] = {"success": True, "result": result}
            print(f"✅ {snapshot_file.name}")
        except Exception as e:
            results[snapshot_file.name] = {"success": False, "error": str(e)}
            print(f"❌ {snapshot_file.name}: {e}")
    return results


# Usage examples
if __name__ == "__main__":
    # Bulk upload
    results = upload_multiple_snapshots()
