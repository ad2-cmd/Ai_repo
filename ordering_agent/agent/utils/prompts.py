import os
import gspread
import json

SERVICE_ACCOUNT_FILE = "premium-horse-feeds-service-account.json"

# Output files
CORRECTIONS_FILE = "corrections.txt"
SYSTEM_PROMPTS_FILE = "system_prompts.json"

# Spreadsheet keys + worksheet ids
CORRECTIONS_SHEET_KEY = "10ca2TFmW35toHGo8JihldccJx4KTzLoYuaj06zWG0cA"
CORRECTIONS_WORKSHEET_ID = 0

SYSTEM_PROMPTS_SHEET_KEY = "1fmlh5uUB16D9-PrNrRjxnO7Fn_36uHwTrP96wp4irHA"
SYSTEM_PROMPTS_WORKSHEET_ID = 697265460


def get_google_worksheet(service_account_file, spreadsheet_key, worksheet_id):
    """Connect to Google Sheets and return a worksheet object."""
    gc = gspread.service_account(service_account_file)
    return gc.open_by_key(spreadsheet_key).get_worksheet_by_id(worksheet_id)


def read_cached_file(filename):
    """Return cached content if file exists, else empty string."""
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def write_if_changed(filename, new_content, is_json=False):
    """Write content to file only if it differs from current content."""
    current = read_cached_file(filename)
    if is_json:
        new_content_str = json.dumps(new_content, ensure_ascii=False, indent=2)
    else:
        new_content_str = new_content

    if new_content_str != current:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(new_content_str)


def get_corrections_from_spreadsheet():
    """Fetch corrections from spreadsheet (Hiba + Korrekció)."""
    try:
        wks = get_google_worksheet(
            SERVICE_ACCOUNT_FILE, CORRECTIONS_SHEET_KEY, CORRECTIONS_WORKSHEET_ID
        )
        records = wks.get_all_records()

        result = "\n\n".join(
            [
                f"- Hiba: {c['Hiba']}\n  **Korrekció**: {c['Korrekció']}"
                for c in records if c.get("Hiba") and c.get("Korrekció")
            ]
        )

        write_if_changed(CORRECTIONS_FILE, result)
        return result

    except Exception as e:
        print(f"Spreadsheet error: {e}")
        return read_cached_file(CORRECTIONS_FILE)


def get_system_prompts_from_spreadsheet():
    """Fetch system prompts from spreadsheet (Prompt Name + Prompt Text), grouped as JSON."""
    try:
        wks = get_google_worksheet(
            SERVICE_ACCOUNT_FILE, SYSTEM_PROMPTS_SHEET_KEY, SYSTEM_PROMPTS_WORKSHEET_ID
        )
        records = wks.get_all_records()

        grouped = {}
        for c in records:
            if c.get("Prompt Name") and c.get("Prompt Text"):
                name = c["Prompt Name"]
                text = c["Prompt Text"]
                grouped.setdefault(name, []).append(text)

        write_if_changed(SYSTEM_PROMPTS_FILE, grouped, is_json=True)
        return grouped

    except Exception as e:
        print(f"Spreadsheet error: {e}")
        try:
            return json.loads(read_cached_file(SYSTEM_PROMPTS_FILE))
        except Exception:
            return {}


def get_system_prompts():
    return get_system_prompts_from_spreadsheet()


def get_base_system_prompt(system_prompts={}):
    corrections_text = get_corrections_from_spreadsheet()

    prompts_text = system_prompts.get('base_system_prompt', '')

    additional_corrections = f"""
    ADDITIONAL CORRECTIONS (Hungarian Instructions):
    Below are real-world corrections gathered from domain experts.
    They are written in Hungarian and must be **strictly followed** when handling similar situations.

    Use them as hard rules to adjust your reasoning and recommendations.
    **Do NOT translate or alter them.** They are directly actionable business rules.

    {corrections_text}
    """

    return f"""
    {prompts_text}

    {additional_corrections}
    """


def get_customer_identification_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('customer_identification', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_product_selection_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('product_selection', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_shipping_method_selection_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('shipping_method_selection', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_shipping_address_selection_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('shipping_address_selection', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_payment_address_selection_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('payment_address_selection', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_payment_method_selection_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('payment_method_selection', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_order_confirmation_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('order_confirmation', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_order_finalization_system_prompt(system_prompts={}, base_system_prompt=''):
    prompts_text = system_prompts.get('order_finalization', '')

    return f"""
    {base_system_prompt}

    {prompts_text}
    """


def get_router_system_prompt(system_prompts={}):
    return system_prompts.get('router', '')


# def get_cart_system_prompt(system_prompts={}, base_system_prompt=''):
#     prompts_text = f"{system_prompts.get('customer_identification', '')}\n{system_prompts.get('product_selection', '')}"
#
#     return f"""
#     {base_system_prompt}
#
#     {prompts_text}
#     """
#
#
# def get_payment_shipping_system_prompt(system_prompts={}, base_system_prompt=''):
#     prompts_text = f"{system_prompts.get('shipping_method_selection', '')}\n{system_prompts.get('shipping_address_selection', '')}\n{system_prompts.get('payment_address_selection', '')}\n{system_prompts.get('payment_method_selection', '')}"
#
#     return f"""
#     {base_system_prompt}
#
#     {prompts_text}
#     """
#
#
# def get_order_system_prompt(system_prompts={}, base_system_prompt=''):
#     prompts_text = f"{system_prompts.get('order_confirmation', '')}\n{system_prompts.get('order_finalization', '')}"
#
#     return f"""
#     {base_system_prompt}
#
#     {prompts_text}
#     """
