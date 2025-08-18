
from typing import Annotated
from pydantic import BaseModel, Field


class PaymentMethod(BaseModel):
    id: Annotated[str, Field(description="The id of the payment method")]
    code: Annotated[str, Field(description="The code of the payment method")]
    name: Annotated[str, Field(description="The name of the payment method")]
    description: Annotated[str, Field(
        description="The description of the payment method")]
    payment_duty: Annotated[dict, Field(
        description="The payment duty of the payment method")]

    def to_json(self):
        return {
            "id": self.id,
            "code": self.code,
            "name": self.name,
            "description": self.description,
            "payment_duty": self.payment_duty
        }
