from fastmcp import FastMCP
from starlette.responses import JSONResponse
import uvicorn

from mcp_prompts.customers import CustomerPrompts
from mcp_prompts.orders import OrderPrompts
from mcp_prompts.payment_addresses import PaymentAddressPrompts
from mcp_prompts.payment_methods import PaymentMethodPrompts
from mcp_prompts.products import ProductPrompts
from mcp_prompts.shipping_addresses import ShippingAddressPrompts
from mcp_prompts.shipping_methods import ShippingMethodPrompts
from mcp_tools.customers import CustomerTools
from mcp_tools.payment_addresses import PaymentAddressTools
from mcp_tools.payment_methods import PaymentMethodTools
from mcp_tools.products import ProductTools
from mcp_tools.session import SessionTools
from mcp_tools.shipping_addresses import ShippingAddressTools
from mcp_tools.shipping_methods import ShippingMethodTools
from mcp_utils.session import OrderState, SessionManager

mcp = FastMCP(
    name="Premium Horse Feeds Ordering Agent",
    on_duplicate_tools="error",
    on_duplicate_prompts="error",
    on_duplicate_resources="error",
)

# NOTE: Kérdések:
# Tovább rendelési folyamat spreadsheet: https://docs.google.com/spreadsheets/d/17ZLvu4JBbIObJhOVJ1cuYxQcvzZSzxF3jRrdt8xG6M4/edit?gid=0#gid=0
# Milyen email címekre milyen mintát kell használnunk az egyes beszállítókhoz?
# Kukoricacsíra olaj XXL raktárra van beírva, de legutóbb amikor néztem nem találtam cikkszám alapján. Ilyen esetekben mi a teendő?
# Mi történik azzal a rendeléssel az XXL logistics-ban ha egyetlen termék sem elérhető és mindegyiket külön beszállítótól kell berendelni?
# Mi történik azzal a rendeléssel amihez a termékeket különböző beszállítóktól kell berendelni és csomagpontra lett kérve?
# Hogyan néz ki a különböző a GLS csomagpont és a GLS házhozszállítás címkéje? Mik a különbségek?
# Mi a folyamat ha Foxpost-os csomagpontra van kérve a rendelés?


# TODO: Visszakérdezés, hogy minden rendben van e, szeretne e még valamit hozzáadni


# NOTE: Referencia darab számra és súlyra: https://www.premiumhorsefeeds.hu/szallitasi-informaciok


# TODO: Use spreadsheet to give AI assistent with predefined data: https://docs.google.com/spreadsheets/d/10ca2TFmW35toHGo8JihldccJx4KTzLoYuaj06zWG0cA/edit?gid=0#gid=0 (DONE, TESTING NEEDED)

# TODO: Save only enabled products (DONE, TESTING NEEDED)
# TODO: Create rule to make gls print label (by weight. Max 20 kg, if more than one print label needed (set Count)) (DONE, TESTING NEEDED)

# TODO: 25kg táp (egy csomag 25 kg de 30 kg alatti, gls max 30 kg csomagautomatába) rendelés foxpost esetén gls automata választása (AI asszisztens keressen közeli automatát, sima qdrant kérés valószínűleg)


# NOTE: MCP Szerver specifikus
# TODO: Agent oldalon (agent.py) törölni a már nem használt agent-et az Agents listából. Ne foglaljon memóriát és tárhelyet
# TODO: Kilistázás helyett legyen lehetőség a termékek, szállítási és fizetési módok és minden mást is egyből lementeni. Ne legyen a felhasználó rákényszerítve a sorszámos választásra

# NOTE: Agent specifikus
# TODO: Csillagozott szövegek (pl email vagy ilyesmi) ne töröljük a csillagot vagy találjunk alternatív megjelenést (DONE)

# NOTE: Folyamat specifikus
# TODO: Tovább rendelés folyamatának kialakítása (Premium Horse Feeds | Forgalmazott márkák és beszállítók spreadsheet használata) melyik márka honnan és hogyan kell berendelni (email sablon-t és email címet kapunk). Külön Agent kell a tovább rendeléshez (beszállítóktól való termék rendelés)
# TODO: Készlet lekérdezés XXL raktárból (API, puppeteer) (DONE BY SKU)
# TODO: GLS címke gyártásának folyamatának kitalálása (API, puppeteer, vagy valami más) (DONE)
# TODO: GLS és Foxpost automaták helyeinek lementése qdrant-ba (DONE, MAYBE UPDGRADE NEEDED FOR SEARCHING)
# TODO: Premium Horse Feeds AI Okosító spreadsheet-ből behúzni a különféle hibákat, megerősítéseket és a lexikont, hogy tudjuk tovább okosítani az LLM-et (system prompt, instructions vagy esetleg valami alternatívákat keresni)
# NOTE: Ne gondolkozz lineáris folyamatokban. Bármilyen kérdés vagy válasz előfordulhat.

# --- Customers ---
mcp.tool(CustomerTools.search_customer_by_email,
         tags={OrderState.CUSTOMER_IDENTIFICATION.value},
         enabled=False
         )
mcp.tool(CustomerTools.customer_agreed_with_found_details,
         tags={OrderState.CUSTOMER_IDENTIFICATION.value}
         )
mcp.prompt(
    CustomerPrompts.search_customer_by_email_address,
    tags={OrderState.CUSTOMER_IDENTIFICATION.value}
)
mcp.prompt(
    CustomerPrompts.customer_identification,
    tags={OrderState.CUSTOMER_IDENTIFICATION.value}
)

# --- Products ---
mcp.tool(ProductTools.search_for_products,
         tags={OrderState.PRODUCT_SELECTION.value},
         enabled=False
         )
mcp.tool(ProductTools.search_for_product,
         tags={OrderState.PRODUCT_SELECTION.value},
         enabled=False
         )
mcp.tool(ProductTools.add_selected_products_to_cart,
         tags={OrderState.PRODUCT_SELECTION.value},
         )
mcp.prompt(
    ProductPrompts.search_for_products,
    tags={OrderState.PRODUCT_SELECTION.value}
)
mcp.prompt(
    ProductPrompts.get_information_about_product,
    tags={OrderState.PRODUCT_SELECTION.value},
    enabled=False
)
mcp.prompt(
    ProductPrompts.product_added_successfully,
    tags={OrderState.PRODUCT_SELECTION.value}
)

# --- Shipping Method ---
mcp.tool(ShippingMethodTools.get_shipping_methods,
         tags={OrderState.SHIPPING_METHOD.value},
         enabled=False
         )
mcp.tool(ShippingMethodTools.store_selected_shipping_method,
         tags={OrderState.SHIPPING_METHOD.value}
         )
mcp.prompt(
    ShippingMethodPrompts.select_shipping_method_by_name,
    tags={OrderState.SHIPPING_METHOD.value}
)
mcp.prompt(
    ShippingMethodPrompts.list_shipping_methods,
    tags={OrderState.SHIPPING_METHOD.value}
)

# --- Shipping Address ---
mcp.tool(ShippingAddressTools.store_selected_shipping_address,
         tags={OrderState.SHIPPING_ADDRESS.value}
         )
mcp.prompt(
    ShippingAddressPrompts.customer_address_selection,
    name="customer_shipping_address_selection",
    tags={OrderState.SHIPPING_ADDRESS.value}
)
mcp.prompt(
    ShippingAddressPrompts.request_close_location_to_gls_parcel_machine,
    tags={OrderState.SHIPPING_ADDRESS.value}
)
mcp.prompt(
    ShippingAddressPrompts.gls_parcel_machine_location_selection,
    tags={OrderState.SHIPPING_ADDRESS.value}
)

# --- Payment Address ---
mcp.prompt(
    PaymentAddressPrompts.customer_address_selection,
    name="customer_payment_address_selection",
)
mcp.prompt(PaymentAddressPrompts.ask_for_new_payment_address)
mcp.tool(PaymentAddressTools.parse_payment_address)
mcp.tool(PaymentAddressTools.store_selected_payment_address)

# --- Payment Method ---
mcp.tool(PaymentMethodTools.get_payment_methods,
         tags={OrderState.PAYMENT_METHOD.value},
         enabled=False
         )
mcp.tool(PaymentMethodTools.store_selected_payment_method,
         tags={OrderState.PAYMENT_METHOD.value},
         )
mcp.prompt(
    PaymentMethodPrompts.list_payment_methods,
    tags={OrderState.PAYMENT_METHOD.value}
)

# --- Order finalization ---
mcp.prompt(
    OrderPrompts.order_confirmation,
    tags={OrderState.ORDER_CONFIRMATION.value}
)
mcp.prompt(
    OrderPrompts.order_finalization,
    tags={OrderState.ORDER_FINALIZATION.value}
)

# --- Session ---
mcp.tool(SessionTools.set_order_state)
mcp.tool(SessionTools.get_order_state)

# --- Custom Routes ---


@mcp.custom_route("/session_manager/session/{session_id}", methods=["GET"])
async def get_session(request):
    session_id = request.path_params["session_id"]
    if not session_id:
        return JSONResponse({"error": "No session found"}, status_code=404)
    session_manager = SessionManager().get_session(session_id)
    return JSONResponse(session_manager.dump_session())


mcp_server_app = mcp.http_app(stateless_http=True)

# --- Entry point ---
if __name__ == "__main__":
    uvicorn.run(
        mcp_server_app,
        host="0.0.0.0",
        port=8000,
        timeout_keep_alive=60
    )
