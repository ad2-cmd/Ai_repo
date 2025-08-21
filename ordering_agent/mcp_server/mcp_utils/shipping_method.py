from typing import Annotated, Any
from pydantic import BaseModel, Field
from qdrant_client.models import ScoredPoint

from qdrant.shipping_methods import search_qdrant_shipping_methods


class ShippingMethod(BaseModel):
    id: Annotated[str, Field(description="The id of the shipping method")]
    shipping_type: Annotated[str, Field(
        description="The shipping_type of the shipping method")]
    extension: Annotated[str, Field(
        description="The extension of the shipping method")]
    name: Annotated[str, Field(description="The name of the shipping method")]
    description: Annotated[str, Field(
        description="The description of the shipping method")]
    # shipping_lanes: Annotated[str, Field(
    #     description="The shipping_lanes of the shipping method")]
    shipping_lanes: Annotated[list[dict[str, Any]], Field(
        description="The shipping_lanes of the shipping method")]
    tax_class: Annotated[dict, Field(
        description="The tax class of the shipping method")]

    def to_json(self):
        return {
            "id": self.id,
            "shipping_type": self.shipping_type,
            "extension": self.extension,
            "name": self.name,
            "description": self.description,
            "shipping_lanes": self.shipping_lanes,
            "tax_class": self.tax_class
        }


async def search_shipping_method(query: str):
    shipping_methods_raw = search_qdrant_shipping_methods(query)
    return get_shipping_method_details(shipping_methods_raw[0])


async def search_shipping_methods(query: str):
    shipping_methods_raw = search_qdrant_shipping_methods(query)
    shipping_methods = []

    for shipping_method_raw in shipping_methods_raw:
        shipping_methods.append(
            get_shipping_method_details(shipping_method_raw))

    return shipping_methods


def get_shipping_method_details(shipping_method_raw: ScoredPoint):

    shipping_method = shipping_method_raw.payload

    if not shipping_method:
        return ShippingMethod(
            id='',
            shipping_type='',
            extension='',
            name='',
            description='',
            shipping_lanes=[],
            tax_class={}
        )

    shipping_method_descriptions = {}
    for description in (shipping_method.get('shippingModeDescriptions') or []):
        if description.get('language', {}).get('code', '').lower() == 'hu':
            shipping_method_descriptions = description
            break

    shipping_lanes = ""
    # for i, shipping_lane in enumerate((shipping_method.get('shippingLanes') or [])):
    #     shipping_lanes += f"{i + 1}. Szállítási tartomány:\n"
    #     shipping_lanes += f"    Kosár összeg minimumtól: {shipping_lane.get('cartMinimumGross') or 'N/A'}\n"
    #     shipping_lanes += f"    Kosár összeg maximumig: {shipping_lane.get('cartMaximumGross') or 'N/A'}\n"
    #     shipping_lanes += f"    Nettó szállítási költség: {shipping_lane.get('costNet') or 'N/A'}\n"
    #     shipping_lanes += f"    Minimum csomag súlytól: {shipping_lane.get('weightMinimum') or 'N/A'}\n"
    #     shipping_lanes += f"    Maximum csomag súlyig: {shipping_lane.get('weightMaximum') or 'N/A'}\n"
    shipping_lanes = shipping_method.get('shippingLanes', [])

    shipping_method_id = shipping_method.get('id') or ''
    shipping_method_shipping_type = shipping_method.get(
        'shippingType') or ''
    shipping_method_extension = shipping_method.get(
        'extension') or ''
    shipping_method_name = shipping_method_descriptions.get(
        'name') or ''
    shipping_method_description = shipping_method_descriptions.get(
        'description') or ''
    shipping_method_tax_class = shipping_method_descriptions.get(
        'taxClass') or {}

    return ShippingMethod(
        id=shipping_method_id,
        shipping_type=shipping_method_shipping_type,
        extension=shipping_method_extension,
        name=shipping_method_name,
        description=shipping_method_description,
        shipping_lanes=shipping_lanes,
        tax_class=shipping_method_tax_class,
    )
