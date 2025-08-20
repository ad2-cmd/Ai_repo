from qdrant.util import upsert_to_qdrant
import httpx
import os

foxpostParcelMachinesUrl = "https://cdn.foxpost.hu/foxplus.json"


def foxpost_parcel_machine_to_text(foxpost_parcel_machine: dict) -> str:
    """
    Generates a comprehensive text representation of a foxpost_parcel_machine from a foxpost_parcel_machine dictionary.

    This function extracts various attributes of a foxpost_parcel_machine, such as name, zip code, city,
    and street, and concatenates them into a single string.
    The resulting string provides a detailed overview of the foxpost_parcel_machine, suitable for generating
    embeddings for semantic search.

    Args:
        foxpost_parcel_machine (dict): A dictionary containing foxpost_parcel_machine information.

    Returns:
        str: A string containing a detailed text representation of the foxpost_parcel_machine.
    """

    # Extract data from the foxpost_parcel_machine
    name = foxpost_parcel_machine.get("name")
    address = foxpost_parcel_machine.get("address")
    zip = foxpost_parcel_machine.get("zip")
    city = foxpost_parcel_machine.get("city")
    street = foxpost_parcel_machine.get("street")

    # Construct the final text representation of the foxpost_parcel_machine
    return (
        f"Az automata neve: {name}. "
        f"Teljes cím: {address}. "
        f"Irányítószám: {zip}, "
        f"Város: {city}, "
        f"Utca: {street}."
    )


async def update_foxpost_parcel_machines():
    """
    Updates the Qdrant collection with the latest Foxpost parcel machines from URL.

    This function retrieves the latest Foxpost parcel machines, then calls `upsert_shipping_methods_to_qdrant`
    to update the Qdrant collection with this data.
    """
    try:
        # Get the list of Foxpost parcel machines from URL.
        response = httpx.get(foxpostParcelMachinesUrl)
        foxpost_parcel_machines = response.json()

        # Get the Qdrant collection name from the environment variables, default to 'foxpost-parcel-machines' if not set.
        collection_name = os.getenv(
            "QDRANT_COLLECTION_FOXPOST", 'foxpost-parcel-machines')

        # Upsert the retrieved foxpost-parcel-machines into the Qdrant collection.
        await upsert_to_qdrant(collection_name=collection_name, items=foxpost_parcel_machines,
                               search_text_transformator=foxpost_parcel_machine_to_text)
    except Exception as e:
        print('Failed to update qdrant foxpost parcel machines')
        print(e)
