from typing import Annotated, Dict, List, Optional
from pydantic import BaseModel, Field
from qdrant_client.models import ScoredPoint
from qdrant.customers import search_qdrant_customers


class Address(BaseModel):
    innerId: Annotated[str, Field(
        description="The inner id of the customer's address")]
    lastname: Annotated[str, Field(
        description="The lastname of the customer's address")]
    firstname: Annotated[str, Field(
        description="The firstname of the customer's address")]
    postcode: Annotated[str, Field(
        description="The postcode of the customer's address")]
    city: Annotated[str, Field(
        description="The city of the customer's address")]
    address: Annotated[str, Field(
        description="The address of the customer's address")]
    telephone: Annotated[str, Field(
        description="The telephone of the customer's address")]
    country: Annotated[str, Field(
        description="The country of the customer's address")]
    message: Annotated[Optional[str], Field(
        description="Optional field for error messages")]


class Customer(BaseModel):
    id: Annotated[str, Field(description="The id of the customer")]
    email: Annotated[str, Field(description="The email of the customer")]
    name: Annotated[str, Field(description="The name of the customer")]
    telephone: Annotated[str, Field(
        description="The telephone of the customer")]
    addresses: Annotated[List[Address], Field(
        description="The addresses of the customer")]


async def search_customer(query: str) -> Dict:
    customers = search_qdrant_customers(query)
    return get_customer_details(customers[0])


async def search_customers(query: str) -> List[Dict]:
    customers_raw = search_qdrant_customers(query)
    customers = []

    for customer_raw in customers_raw:
        customers.append(get_customer_details(customer_raw))

    return customers


def get_customer_details(customer_raw: ScoredPoint) -> Dict:

    customer = customer_raw.payload

    if not customer:
        return {
            "id": None,
            "email": None,
            "firstname": None,
            "lastname": None,
            "name": None,
            "telephone": None,
            "addresses": []
        }
        return Customer(id='', email='', name='', telephone='', addresses=[])

    customer_id = customer.get('id') or ''
    customer_lastname = customer.get('lastname') or ''
    customer_firstname = customer.get('firstname') or ''
    customer_email = customer.get('email') or ''
    customer_phone = customer.get('telephone') or ''

    customer_addresses_raw = customer.get('addresses') or []
    customer_addresses = []

    for address_raw in customer_addresses_raw:
        customer_address_id = address_raw.get('id') or ''
        customer_address_inner_id = address_raw.get('innerId') or ''
        customer_address_lastname = address_raw.get('lastname') or ''
        customer_address_firstname = address_raw.get('firstname') or ''
        customer_address_postcode = address_raw.get('postcode') or ''
        customer_address_city = address_raw.get('city') or ''
        customer_address_address = address_raw.get('address1') or ''
        customer_address_telephone = address_raw.get('telephone') or ''
        customer_address_country_raw = address_raw.get('country') or {}

        customer_address_country = {
            "id": customer_address_country_raw.get('id') or '',
            "name": customer_address_country_raw.get('name') or ''
        }

        # customer_address = Address(
        #     innerId=customer_address_inner_id,
        #     lastname=customer_address_lastname,
        #     firstname=customer_address_firstname,
        #     postcode=customer_address_postcode,
        #     city=customer_address_city,
        #     address=customer_address_address,
        #     telephone=customer_address_telephone,
        #     country=customer_address_country,
        #     message=None
        # )

        customer_address = {
            "id": customer_address_id,
            "innerId": customer_address_inner_id,
            "lastname": customer_address_lastname,
            "firstname": customer_address_firstname,
            "postcode": customer_address_postcode,
            "city": customer_address_city,
            "address": customer_address_address,
            "telephone": customer_address_telephone,
            "country": customer_address_country,
            "message": None
        }

        customer_addresses.append(customer_address)

    return {
        "id": customer_id,
        "email": customer_email,
        "firstname": customer_firstname,
        "lastname": customer_lastname,
        "name": f"{customer_lastname} {customer_firstname}",
        "telephone": customer_phone,
        "addresses": customer_addresses
    }
    # return Customer(id=customer_id, email=customer_email, name=f"{customer_lastname} {customer_firstname}", telephone=customer_phone, addresses=customer_addresses)
