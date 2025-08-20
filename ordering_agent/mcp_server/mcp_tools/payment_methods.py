from fastmcp import Context
from mcp_utils.payment_methods import PaymentMethod
from mcp_utils.session import SessionManager
from qdrant.payment_methods import get_all_payment_methods


class PaymentMethodTools:
    @classmethod
    async def get_payment_methods(cls):
        """
        Retrieves a list of available payment methods from the backend and returns them 
        in a structured format suitable for presentation to users.
        """
        payment_methods_raw = get_all_payment_methods()
        payment_methods = []

        for payment_method in payment_methods_raw:

            if not payment_method:
                continue

            payment_method_descriptions = {}
            for description in (payment_method.get('paymentDescription') or []):
                if description.get('language', {}).get('code', '').lower() == 'hu':
                    payment_method_descriptions = description
                    break

            payment_method_id = payment_method.get('id', '')
            payment_method_code = payment_method.get('code', '')
            payment_method_name = payment_method_descriptions.get('name', '')
            payment_method_description = payment_method_descriptions.get(
                'description', '')
            payment_method_payment_duty = payment_method.get('paymentDuty', {})

            payment_methods.append(
                PaymentMethod(
                    id=payment_method_id,
                    code=payment_method_code,
                    name=payment_method_name,
                    description=payment_method_description,
                    payment_duty=payment_method_payment_duty
                )
            )

            # payment_methods.append({
            #     "id": payment_method_id,
            #     "code": payment_method_code,
            #     "name": payment_method_name,
            #     "description": payment_method_description
            # })

        return payment_methods

    @classmethod
    async def store_selected_payment_method(cls, ctx: Context, payment_method_id: str):
        """
        Store the selected payment method in the session.
        """
        session_manager = SessionManager().get_session(ctx.session_id)
        payment_methods = session_manager.found_payment_methods

        selected_payment_method = [
            payment_method for payment_method in payment_methods if payment_method.id == payment_method_id
        ]

        if not selected_payment_method:
            return {
                "status": "unsuccessfull",
                "payment_method_id": payment_method_id
            }

        session_manager.payment_method = selected_payment_method[0].to_json()

        return {
            "status": "successfull",
            "payment_method_name": session_manager.payment_method.get('name', '')
        }
