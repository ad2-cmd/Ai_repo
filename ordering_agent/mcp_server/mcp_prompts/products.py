import json
from fastmcp import Context
from fastmcp.prompts.prompt import Message
from mcp_tools.products import ProductTools


class ProductPrompts:
    @classmethod
    async def search_for_products(cls, ctx: Context, query: str):
        """
        List all the relevant products that were found.

        This prompt is used to display all the relevant products that were found based on user input.
        It asks the user which products does he/she want to order.
        """

        products = await ProductTools.search_for_products(ctx, query)

        if not products:
            return Message("Sajnos nem találtam terméket a keresésedre. Próbálj meg más kulcsszavakat használni.", role="user")

        prompt = f"""
            <instructions>
              <role>You are a product extraction assistant focused on relevance to the user’s search.</role>

              <task>
                Given the input JSON list of products and the search term <query>, extract **only** the products that are relevant to <query>.
                For each relevant product, include **only**:
                  - id (must remain exactly as is)
                  - name
                  - brand
                  - price
                  - short_description
              </task>

              <relevance>
                - A product is *relevant* if its name or short_description mentions or closely matches <query>.
                - Do not list any non‑relevant products.
              </relevance>

              <formatting>
                Output the relevant products as a numbered list:
                  1.
                    ID: id
                    Név: name
                    Márka: brand
                    Ár: price
                    Leírás: short_description
                  2.
                    ...
                After listing, ask:
                  “Which product matching '<query>' would you like to choose? Please reply with the serial number or the product name.”
              </formatting>
            </instructions>

            <examples>
              <example>
                <query>Ultra</query>
                <input>
                  [
                    {{
                      "id": "123",
                      "name": "UltraWidget",
                      "brand": "WidgetCo",
                      "price": "$19.99",
                      "short_description": "A versatile ultra-fast widget."
                    }},
                    {{
                      "id": "456",
                      "name": "MegaWidget",
                      "brand": "WidgetCorp",
                      "price": "$29.99",
                      "short_description": "An even more versatile widget."
                    }}
                  ]
                </input>
                <output>
                  1.
                    ID: 123
                    Név: UltraWidget
                    Márka: WidgetCo
                    Ár: $19.99
                    Leírás: A versatile ultra-fast widget.

                  Which product matching ‘Ultra’ would you like to choose? Please reply with the serial number or the product name.
                </output>
              </example>
            </examples>

            <thinking>
            1. Look at each product’s name and short_description to check if they mention or closely match <query>.
            2. Only keep products that satisfy this relevance test.
            3. For each kept product, extract id, name, brand, price, short_description exactly.
            4. Format them as a numbered list with Hungarian labels.
            5. Prompt the user to choose by number or name, referencing the term <query>.
            </thinking>

            <user_input>
            {{
              "query": "{query}",
              "products": {json.dumps(products, indent=4)}
            }}
            </user_input>

            <assistant_response>
        """

        return Message(prompt, role="user")

    @classmethod
    async def get_information_about_product(cls, ctx: Context, product_info: str):
        """
        Get information about a specific product.

        This prompt is used to display all the information about a specific product based on the provided information from the customer.
        """

        product = await ProductTools.search_for_product(ctx, product_info)

        if not product:
            return Message("Sajnos nem találtam terméket a keresésedre. Próbálj meg más kulcsszavakat használni.", role="user")

        prompt = f"""
            <system>
              <role>You are a product information extraction assistant and shopping assistant.</role>
            </system>

            <instructions>
              <task>
                Given the input JSON representing a single product, extract and return **only** the following fields:
                - id (do **not** modify)
                - name
                - brand
                - price
                - short_description
                - description
                - stock1
              </task>
              <constraints>
                ALWAYS include the id exactly as provided.
                Do **NOT** include any additional fields.
              </constraints>
              <formatting>
                Output in this exact format (Hungarian field names):
                  ID: id  
                  Név: name  
                  Márka: brand  
                  Ár: price  
                  Rövid leírás: short_description  
                  Leírás: description  
                  Készleten: stock1  
              </formatting>
              <followup>
                After presenting the product details, ask:
                  “Would you like to add this product to your cart? (yes/no)”
              </followup>
            </instructions>

            <examples>
              <example>
                <input>
                  {{
                    "id": "A001",
                    "name": "SuperGadget",
                    "brand": "GadgetCo",
                    "price": "€49.99",
                    "short_description": "A powerful gadget.",
                    "description": "This SuperGadget is designed...",
                    "stock1": 25,
                    "internal_note": "do not expose"
                  }}
                </input>
                <output>
                  ID: A001  
                  Név: SuperGadget  
                  Márka: GadgetCo  
                  Ár: €49.99  
                  Rövid leírás: A powerful gadget.  
                  Leírás: This SuperGadget is designed...  
                  Készleten: 25  

                  Would you like to add this product to your cart? (yes/no)
                </output>
              </example>
            </examples>

            <thinking>
            1. Parse the JSON input.  
            2. Confirm all required fields (id, name, brand, price, short_description, description, stock1) are present.  
            3. Extract each one verbatim.  
            4. Ignore any extra fields such as internal notes.  
            5. Format using Hungarian labels exactly.  
            6. Finally, prompt the user: “Would you like to add this product to your cart? (yes/no)”
            </thinking>

            <prefill_assistant_response>
            ID:  
            Név:  
            Márka:  
            Ár:  
            Rövid leírás:  
            Leírás:  
            Készleten:  

            Would you like to add this product to your cart? (yes/no)
            </prefill_assistant_response>

            <user_input>
            {json.dumps(product, indent=4)}
            </user_input>

            <assistant_response>
        """

        return Message(prompt, role="user")

    @classmethod
    async def confirm_product_selection(cls, ctx: Context, product_id: str):
        """
        Confirm the user's product selection.

        This prompt is used to confirm the user's choice of product and to ask for the quantity.
        """

        product = await ProductTools.get_product_by_id(ctx, product_id)

        if not product:
            return Message("Sajnos nem találtam a kiválasztott terméket. Kérlek, próbáld meg újra.", role="user")

        prompt = f"""
            <system>
              <role>You are a shopping assistant confirming product selection and inquiring about quantity.</role>
            </system>

            <instructions>
              <task>
                Given the input JSON representing a single product, confirm the selection and ask for the desired quantity.
              </task>
              <constraints>
                - Always confirm the product name and brand.
                - Ask for the quantity in a clear and concise manner.
              </constraints>
              <formatting>
                Output in this exact format (Hungarian field names):
                  Termék: name (brand)
                  Ár: price
                  Rövid leírás: short_description

                After presenting the product details, ask:
                  “How many of this product would you like to order?”
              </formatting>
            </instructions>

            <examples>
              <example>
                <input>
                  {{
                    "id": "A001",
                    "name": "SuperGadget",
                    "brand": "GadgetCo",
                    "price": "€49.99",
                    "short_description": "A powerful gadget.",
                    "description": "This SuperGadget is designed...",
                    "stock1": 25
                  }}
                </input>
                <output>
                  Termék: SuperGadget (GadgetCo)
                  Ár: €49.99
                  Rövid leírás: A powerful gadget.

                  How many of this product would you like to order?
                </output>
              </example>
            </examples>

            <thinking>
            1. Parse the JSON input for the selected product.
            2. Extract the name, brand, price, and short_description.
            3. Format the output using the specified Hungarian labels and structure.
            4. Ask the user for the quantity they wish to order.
            </thinking>

            <user_input>
            {json.dumps(product, indent=4)}
            </user_input>

            <assistant_response>
        """

        return Message(prompt, role="user")

    @classmethod
    async def product_added_successfully(cls):
        """
        Inform the user that the product has been successfully added to the cart.

        This prompt is used to confirm that the selected product has been added to the user's shopping cart.
        """

        prompt = f"""
            ...
            A termék(ek) sikeresn hozzá lett(ek) adva a kosárhoz.
            Szeretnél még más terméket is rendelni?
        """

        return Message(prompt, role="user")
