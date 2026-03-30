import os

import requests
from dotenv import load_dotenv
from sqlalchemy.orm import Session

from . import crud, integrations

load_dotenv()

VALID_CATEGORIES = {"billing", "account", "technical", "feature_request", "general"}
VALID_PRIORITIES = {"low", "medium", "high"}


def empty_ai_result() -> dict:
    return {"summary": None, "category": None, "priority": None}


def fallback_classify_activity(title: str, content: str) -> dict:
    """Use simple rules when Gemini key is missing."""
    text = f"{title} {content}".lower()

    category = "general"
    priority = "low"

    if any(word in text for word in ["payment", "invoice", "billing", "refund"]):
        category = "billing"
        priority = "high"
    elif any(word in text for word in ["login", "password", "account", "access"]):
        category = "account"
        priority = "high"
    elif any(word in text for word in ["error", "bug", "failed", "crash", "issue"]):
        category = "technical"
        priority = "medium"
    elif any(word in text for word in ["feature", "request", "improve", "enhance"]):
        category = "feature_request"
        priority = "low"

    summary = title.strip()
    if len(summary) > 120:
        summary = summary[:117] + "..."

    return {"summary": summary, "category": category, "priority": priority}


def read_ai_text(ai_text: str) -> dict:
    """Read lines in format: summary/category/priority."""
    ai_result = empty_ai_result()

    for line in ai_text.splitlines():
        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip().lower()
        value = value.strip()

        if not value:
            continue

        if key == "summary":
            ai_result["summary"] = value
        elif key == "category":
            ai_result["category"] = value.lower()
        elif key == "priority":
            ai_result["priority"] = value.lower()

    if ai_result["category"] not in VALID_CATEGORIES:
        ai_result["category"] = None
    if ai_result["priority"] not in VALID_PRIORITIES:
        ai_result["priority"] = None

    return ai_result


def classify_activity(title: str, content: str) -> dict:
    """Try Gemini. If it fails, return empty AI fields."""
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return fallback_classify_activity(title, content)

    model = os.getenv("GEMINI_MODEL", "gemini-1.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    prompt = f"""
Classify this support ticket.
Return only 3 lines:
summary: <one short sentence>
category: <billing|account|technical|feature_request|general>
priority: <low|medium|high>

Title: {title}
Content: {content}
""".strip()

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.2},
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        response.raise_for_status()

        data = response.json()
        ai_text = (
            data.get("candidates", [{}])[0]
            .get("content", {})
            .get("parts", [{}])[0]
            .get("text", "")
        )

        if not isinstance(ai_text, str) or not ai_text.strip():
            return empty_ai_result()

        return read_ai_text(ai_text)
    except (requests.RequestException, ValueError, KeyError, IndexError, TypeError):
        return empty_ai_result()


def sync_customers(db: Session, summary: dict) -> None:
    raw_customers, error = integrations.fetch_crm_customers()
    if error:
        summary["errors"].append(error)

    summary["customers_fetched"] = len(raw_customers)

    for raw_customer in raw_customers:
        customer = integrations.normalize_customer(raw_customer)
        if not customer:
            summary["customers_skipped"] += 1
            continue

        existing = crud.get_customer_by_external_id(
            db,
            external_id=customer["external_id"],
            source=customer["source"],
        )
        if existing:
            summary["customers_skipped"] += 1
            continue

        _, inserted = crud.create_customer(db, customer)
        if inserted:
            summary["customers_inserted"] += 1
        else:
            summary["customers_skipped"] += 1


def sync_activities(db: Session, summary: dict) -> None:
    raw_tickets, error = integrations.fetch_support_tickets()
    if error:
        summary["errors"].append(error)

    summary["activities_fetched"] = len(raw_tickets)

    for raw_ticket in raw_tickets:
        activity = integrations.normalize_activity(raw_ticket)
        if not activity:
            summary["activities_skipped"] += 1
            continue

        customer = crud.get_customer_by_external_id(
            db,
            external_id=activity["customer_external_id"],
            source="crm",
        )
        if not customer:
            summary["activities_missing_customer"] += 1
            continue

        existing = crud.get_activity_by_external_id(
            db,
            external_id=activity["external_id"],
            source=activity["source"],
        )
        if existing:
            summary["activities_skipped"] += 1
            continue

        ai_data = classify_activity(activity["title"], activity["content"])

        activity_data = {
            "external_id": activity["external_id"],
            "customer_id": customer.id,
            "type": activity["type"],
            "title": activity["title"],
            "content": activity["content"],
            "source": activity["source"],
            "ai_summary": ai_data.get("summary"),
            "ai_category": ai_data.get("category"),
            "ai_priority": ai_data.get("priority"),
        }

        _, inserted = crud.create_activity(db, activity_data)
        if inserted:
            summary["activities_inserted"] += 1
        else:
            summary["activities_skipped"] += 1


def sync_data(db: Session) -> dict:
    summary = {
        "customers_fetched": 0,
        "customers_inserted": 0,
        "customers_skipped": 0,
        "activities_fetched": 0,
        "activities_inserted": 0,
        "activities_skipped": 0,
        "activities_missing_customer": 0,
        "errors": [],
    }

    sync_customers(db, summary)
    sync_activities(db, summary)

    return summary