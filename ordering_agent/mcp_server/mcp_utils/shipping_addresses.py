
from qdrant_client.models import ScoredPoint
from qdrant.gls import search_qdrant_gls_parcel_machines


async def search_gls_parcel_machine(query: str):
    gls_parcel_machines_raw = search_qdrant_gls_parcel_machines(query)
    return get_gls_parcel_machine_details(gls_parcel_machines_raw[0])


async def search_gls_parcel_machines(query: str):
    gls_parcel_machines_raw = search_qdrant_gls_parcel_machines(query)
    gls_parcel_machines = []

    for gls_parcel_machine_raw in gls_parcel_machines_raw:
        gls_parcel_machines.append(
            get_gls_parcel_machine_details(gls_parcel_machine_raw))

    return gls_parcel_machines


def get_gls_parcel_machine_details(gls_parcel_machine_raw: ScoredPoint):

    gls_parcel_machine = gls_parcel_machine_raw.payload

    if not gls_parcel_machine:
        return {
            'id': None,
            'name': None,
            'postcode': None,
            'city': None,
            'address': None,
            # 'google_maps_url': None
        }

    gls_parcel_machine_id = gls_parcel_machine['id']
    gls_parcel_machine_name = gls_parcel_machine['name']
    gls_parcel_machine_postal_contact_raw = gls_parcel_machine.get(
        'contact') or None
    gls_parcel_machine_location_raw = gls_parcel_machine.get(
        'location') or None

    gls_parcel_machine_postal_code = None
    gls_parcel_machine_city = None
    gls_parcel_machine_address = None
    if gls_parcel_machine_postal_contact_raw:
        gls_parcel_machine_postal_code = gls_parcel_machine_postal_contact_raw['postalCode']
        gls_parcel_machine_city = gls_parcel_machine_postal_contact_raw['city']
        gls_parcel_machine_address = gls_parcel_machine_postal_contact_raw['address']

    gls_parcel_machine_latitude = None
    gls_parcel_machine_longitude = None
    if gls_parcel_machine_location_raw:
        gls_parcel_machine_latitude = gls_parcel_machine_location_raw[0]
        gls_parcel_machine_longitude = gls_parcel_machine_location_raw[1]

    gls_parcel_machine_google_maps_url = None
    if gls_parcel_machine_latitude and gls_parcel_machine_longitude:
        gls_parcel_machine_google_maps_url = f"https://www.google.com/maps/@{gls_parcel_machine_latitude},{gls_parcel_machine_longitude},15z"

    return {
        'id': gls_parcel_machine_id,
        'name': gls_parcel_machine_name,
        'postcode': gls_parcel_machine_postal_code,
        'city': gls_parcel_machine_city,
        'address': gls_parcel_machine_address,
        # 'google_maps_url': gls_parcel_machine_google_maps_url
    }
