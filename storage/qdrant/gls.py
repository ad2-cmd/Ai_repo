from qdrant.util import upsert_to_qdrant
import httpx
import os

glsParcelMachinesUrl = "https://map.gls-hungary.com/data/deliveryPoints/hu.json"


def gls_parcel_machine_to_text(gls_parcel_machine: dict) -> str:
    """
    Generates a comprehensive text representation of a gls_parcel_machine from a gls_parcel_machine dictionary.

    This function extracts various attributes of a gls_parcel_machine, such as name, zip code, city,
    and street, and concatenates them into a single string.
    The resulting string provides a detailed overview of the gls_parcel_machine, suitable for generating
    embeddings for semantic search.

    Args:
        gls_parcel_machine (dict): A dictionary containing gls_parcel_machine information.

    Returns:
        str: A string containing a detailed text representation of the gls_parcel_machine.
    """

    # Extract data from the gls_parcel_machine
    name = gls_parcel_machine.get("name")

    contact = gls_parcel_machine.get("contact")
    zip = contact.get("postalCode")
    city = contact.get("city")
    street = contact.get("address")

    # Construct the final text representation of the gls_parcel_machine
    return (
        f"Az automata neve: {name}. "
        f"Irányítószám: {zip}, "
        f"Város: {city}, "
        f"Utca: {street}."
    )


async def update_gls_parcel_machines():
    """
    Updates the Qdrant collection with the latest Gls parcel machines from URL.

    This function retrieves the latest Gls parcel machines, then calls `upsert_shipping_methods_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Get the list of Gls parcel machines from URL.
        response = httpx.get(glsParcelMachinesUrl)
        gls_parcel_machines = response.json()
        gls_parcel_machines = gls_parcel_machines.get("items")

        # Get the Qdrant collection name from the environment variables, default to 'gls-parcel-machines' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_GLS", 'gls-parcel-machines')

        # Upsert the retrieved gls-parcel-machines into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name, items=gls_parcel_machines,
                               search_text_transformator=gls_parcel_machine_to_text)
    except Exception as e:
        print('Failed to update qdrant gls parcel machines')
        print(e)
