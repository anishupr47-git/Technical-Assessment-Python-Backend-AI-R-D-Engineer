import requests

CRM_CUSTOMERS_URL = "https://jsonplaceholder.typicode.com/users"
SUPPORT_TICKETS_URL = "https://jsonplaceholder.typicode.com/posts"


def fetch_list(url: str, system_name: str):
    """Fetch a list payload from an external API."""
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        data = response.json()

        if not isinstance(data, list):
            return [], f"{system_name} API returned invalid data format"

        return data, None
    except requests.RequestException as exc:
        return [], f"{system_name} API request failed: {exc}"


def fetch_crm_customers():
    return fetch_list(CRM_CUSTOMERS_URL, "CRM")


def fetch_support_tickets():
    return fetch_list(SUPPORT_TICKETS_URL, "Support")


def normalize_customer(raw_customer: dict):
    """Map CRM customer fields into internal customer format."""
    try:
        customer_id = int(raw_customer.get("id"))
        name = str(raw_customer.get("name", "")).strip()
        email = str(raw_customer.get("email", "")).strip()

        if not name or not email:
            return None

        return {
            "external_id": customer_id,
            "name": name,
            "email": email,
            "source": "crm",
        }
    except (TypeError, ValueError):
        return None


def normalize_activity(raw_ticket: dict):
    """Map Support ticket fields into internal activity format."""
    try:
        ticket_id = int(raw_ticket.get("id"))
        customer_external_id = int(raw_ticket.get("userId"))
        title = str(raw_ticket.get("title", "")).strip()
        content = str(raw_ticket.get("body", "")).strip()

        if not title or not content:
            return None

        return {
            "external_id": ticket_id,
            "customer_external_id": customer_external_id,
            "type": "ticket",
            "title": title,
            "content": content,
            "source": "support",
        }
    except (TypeError, ValueError):
        return None