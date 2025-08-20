

from typing import List
from fastmcp import Context
from mcp_utils.session import SessionManager
from mcp_utils.shipping_method import ShippingMethod
from qdrant.shipping_methods import get_all_shipping_methods


class ShippingMethodTools:
    @classmethod
    async def get_shipping_methods(cls) -> List[ShippingMethod]:
        """
        Get all shipping methods.

        This tool returns all available shipping methods.
        It is intended to provide information about available shipping methods for the user.
        """
        shipping_methods_raw = get_all_shipping_methods()
        shipping_methods = []

        for shipping_method in shipping_methods_raw:

            if not shipping_method:
                continue

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

            shipping_method_id = shipping_method.get('id') or ''
            shipping_method_shipping_type = shipping_method.get(
                'shippingType') or ''
            shipping_method_extension = shipping_method.get(
                'extension') or ''
            shipping_method_name = shipping_method_descriptions.get(
                'name') or ''
            shipping_method_description = shipping_method_descriptions.get(
                'description') or ''
            shipping_lanes = shipping_method.get('shippingLanes') or []
            shipping_tax_class = shipping_method.get(
                'taxClass') or {}

            shipping_methods.append(ShippingMethod(
                id=shipping_method_id,
                shipping_type=shipping_method_shipping_type,
                extension=shipping_method_extension,
                name=shipping_method_name,
                description=shipping_method_description,
                shipping_lanes=shipping_lanes,
                tax_class=shipping_tax_class
            ))
            # shipping_methods.append({
            #     "id": shipping_method_id,
            #     "shipping_type": shipping_method_shipping_type,
            #     "extension": shipping_method_extension,
            #     "name": shipping_method_name,
            #     "description": shipping_method_description,
            #     "shipping_lanes": shipping_lanes,
            # })

        return shipping_methods

    @classmethod
    async def store_selected_shipping_method(cls, ctx: Context, shipping_method_id: str):
        """
        Store the selected shipping method in the session.
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        shipping_methods = session_manager.found_shipping_methods

        selected_shipping_method = [
            shipping_method for shipping_method in shipping_methods if shipping_method.id == shipping_method_id
        ]

        if not selected_shipping_method:
            return {
                "status": "unsuccessfull",
                "shipping_method_id": shipping_method_id
            }

        session_manager.shipping_method = selected_shipping_method[0].to_json()

        return {
            "status": "successfull",
            "shipping_method_name": session_manager.shipping_method.get('name', '')
        }
