from urllib.parse import urlencode
from dotenv import load_dotenv
from base64 import b64encode
import httpx
import os

load_dotenv()

# Get the environment variables first
api_user = os.getenv('SHOPRENTER_API_USER', '')
api_pass = os.getenv('SHOPRENTER_API_PASS', '')

# Create the auth string and encode it to bytes, then to base64
auth_string = f"{api_user}:{api_pass}"

B64_API_AUTH = b64encode(auth_string.encode('utf-8')).decode('utf-8')
SHOPRENTER_BASE = os.getenv(
    'SHOPRENTER_API_BASE_URL') or 'http://testmcp2.api.myshoprenter.hu'
SHOPRENTER_HEADERS = {
    "Authorization": f"Basic {B64_API_AUTH}", "Content-Type": "application/json", "Accept": "application/json"}


async def call_shoprenter_api(method='GET', endpoint='', params=None, data=None):
    """
    Simple API caller that accepts dicts for structured data

    Args:
        method: HTTP method (GET, POST, PUT, PATCH, DELETE)
        endpoint: API endpoint (e.g., 'products', 'products/123')
        params: Dict of query parameters
        data: Dict of request body data
    """
    params = params or {}
    data = data or {}

    async with httpx.AsyncClient() as client:
        try:
            # Build URL
            url = f"{SHOPRENTER_BASE}/{endpoint.lstrip('/')}"

            # Add query parameters if provided
            if params:
                url += f"?{urlencode(params)}"

            # Get the HTTP method dynamically
            method_func = getattr(client, method.lower())

            # Make the request
            if method.upper() in ['POST', 'PUT', 'PATCH']:
                response = await method_func(url, headers=SHOPRENTER_HEADERS, json=data)
            else:
                response = await method_func(url, headers=SHOPRENTER_HEADERS)

            # Handle response
            if response.status_code in [200, 201, 204]:
                return response.json()
            else:
                return {
                    'error': True,
                    'status_code': response.status_code,
                    'message': response.text
                }

        except Exception as e:
            return {'error': True, 'message': str(e)}


async def get_all_shoprenter_items(endpoint, filters=None):
    """Get all shoprenter items wrapper"""
    params = {'page': 0, 'full': 1, 'limit': 200}
    if filters:
        params.update(filters)

    items = []

    print("Making request with params", params, "for endpoint", endpoint)
    items_response_data = await call_shoprenter_api('GET', endpoint, params=params)
    items = items_response_data['items']

    while (items_response_data['next']):
        params['page'] += 1
        print("Making request with params", params, "for endpoint", endpoint)
        items_response_data = await call_shoprenter_api('GET', endpoint, params=params)
        items += items_response_data['items']

    print(f"{len(items)} of items found for endpoint:", endpoint)
    print()

    return items


async def resolve_linked_resource(resource: dict, key: str, all_resources: list, id_key: str = 'href'):
    """
    Resolves a linked resource within a dictionary by fetching its details from the API.

    Args:
        resource (dict): The dictionary containing the linked resource.
        key (str): The key in the dictionary where the linked resource's reference is stored.
        endpoint_prefix (str): The base endpoint for fetching the linked resource.
        id_key (str, optional): The key containing the ID or URL to extract the ID from. Defaults to 'href'.

    Returns:
        dict: The original resource dictionary with the linked resource details added, or the original resource if an error occurred.
    """
    try:
        if resource.get(key):
            resource_href = resource[key].get(id_key)
            resource_id = resource_href.split('/')[-1]
            resource_response = await find_resource_by_id(
                resource_id=resource_id, resources=all_resources)
            resource[key] = resource_response
        return resource
    except Exception as e:
        print(f"Error resolving linked resource for key '{key}': {e}")
        return resource


async def find_resource_by_id(resources: list, resource_id: str, id_key: str = 'id'):
    """
    Finds a resource within a list of resources by its ID.

    Args:
        resources (list): A list of resource dictionaries to search within.
        resource_id (str): The ID of the resource to find.
        id_key (str, optional): The key containing the ID in the resource dictionary. Defaults to 'id'.

    Returns:
        dict or None: The matching resource dictionary if found, otherwise None.
    """
    try:
        matching_resource = next(
            (r for r in resources if str(r.get(id_key)) == resource_id), None)
        return matching_resource
    except Exception as e:
        print(f"Error finding resource by ID '{resource_id}': {e}")
        return None
