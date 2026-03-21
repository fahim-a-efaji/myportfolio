"""
function_app.py — Azure Functions v2 (Python)
==============================================
All 6 HTTP endpoints for the portfolio:

  POST /api/contact           → save contact message     → Cosmos: contacts
  GET  /api/finance           → list transactions        → Cosmos: finance_tx
  POST /api/finance           → add transaction          → Cosmos: finance_tx
  DELETE /api/finance/{id}    → delete transaction       → Cosmos: finance_tx
  POST /api/finance/seed      → seed sample data         → Cosmos: finance_tx
  GET  /api/sql/queries       → list saved queries       → Cosmos: sql_queries
  POST /api/sql/queries       → save a query             → Cosmos: sql_queries
  DELETE /api/sql/queries/{id}→ delete saved query       → Cosmos: sql_queries
  POST /api/csv               → save CSV analysis meta   → Cosmos: csv_uploads
  GET  /api/csv               → list past analyses       → Cosmos: csv_uploads
  GET  /api/chat              → get session history      → Cosmos: chat_history
  POST /api/chat              → append message           → Cosmos: chat_history
  DELETE /api/chat/{session}  → clear session            → Cosmos: chat_history

CORS: set ALLOWED_ORIGIN env var (e.g. https://yourusername.github.io)
"""

import azure.functions as func
import json
import logging
import os
import uuid
from datetime import datetime, timezone
from cosmos_client import upsert, query_items, delete_item

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

ALLOWED_ORIGIN = os.environ.get("ALLOWED_ORIGIN", "*")


# ─────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────

def cors(extra: dict | None = None) -> dict:
    h = {
        "Access-Control-Allow-Origin": ALLOWED_ORIGIN,
        "Access-Control-Allow-Methods": "GET, POST, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, X-User-Id",
        "Content-Type": "application/json",
    }
    if extra:
        h.update(extra)
    return h


def ok(data, status=200) -> func.HttpResponse:
    return func.HttpResponse(json.dumps(data, default=str), status_code=status, headers=cors())


def err(msg: str, status=400) -> func.HttpResponse:
    return func.HttpResponse(json.dumps({"error": msg}), status_code=status, headers=cors())


def preflight() -> func.HttpResponse:
    return func.HttpResponse(status_code=204, headers=cors())


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


def user_id(req: func.HttpRequest) -> str:
    """Get userId from header; fall back to 'anonymous'."""
    return req.headers.get("X-User-Id", "anonymous")


# ─────────────────────────────────────────────
# 1. CONTACT FORM  →  Cosmos: contacts
# ─────────────────────────────────────────────

@app.route(route="contact", methods=["POST", "OPTIONS"])
def contact(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()
    try:
        body = req.get_json()
    except ValueError:
        return err("Invalid JSON")

    name    = (body.get("name") or "").strip()
    email   = (body.get("email") or "").strip()
    subject = (body.get("subject") or "").strip()
    message = (body.get("message") or "").strip()

    if not all([name, email, message]):
        return err("name, email, and message are required")

    doc = {
        "id":        new_id(),
        "name":      name,
        "email":     email,
        "subject":   subject,
        "message":   message,
        "createdAt": now_iso(),
        "read":      False,
    }

    try:
        upsert("contacts", doc)
        logging.info("Contact saved from %s", email)
        return ok({"success": True, "message": "Your message has been received!"})
    except Exception as e:
        logging.error("Contact save error: %s", e)
        return err("Failed to save message", 500)


# ─────────────────────────────────────────────
# 2. FINANCE TRACKER  →  Cosmos: finance_tx
# ─────────────────────────────────────────────

SAMPLE_TRANSACTIONS = [
    {"desc": "Monthly Salary",    "cat": "Salary",        "date": "2024-12-01", "amount": 3500,  "type": "income"},
    {"desc": "Freelance Project", "cat": "Freelance",     "date": "2024-12-05", "amount": 800,   "type": "income"},
    {"desc": "Apartment Rent",    "cat": "Housing",       "date": "2024-12-01", "amount": 1200,  "type": "expense"},
    {"desc": "Grocery Shopping",  "cat": "Food",          "date": "2024-12-03", "amount": 180,   "type": "expense"},
    {"desc": "Metro Pass",        "cat": "Transport",     "date": "2024-12-04", "amount": 50,    "type": "expense"},
    {"desc": "Netflix",           "cat": "Entertainment", "date": "2024-12-06", "amount": 15,    "type": "expense"},
    {"desc": "Gym Membership",    "cat": "Health",        "date": "2024-12-08", "amount": 40,    "type": "expense"},
    {"desc": "Monthly Salary",    "cat": "Salary",        "date": "2024-11-01", "amount": 3500,  "type": "income"},
    {"desc": "Online Shopping",   "cat": "Shopping",      "date": "2024-11-10", "amount": 250,   "type": "expense"},
    {"desc": "Restaurant",        "cat": "Food",          "date": "2024-11-15", "amount": 90,    "type": "expense"},
    {"desc": "Stock Dividend",    "cat": "Investment",    "date": "2024-11-20", "amount": 350,   "type": "income"},
    {"desc": "Electricity Bill",  "cat": "Housing",       "date": "2024-11-25", "amount": 85,    "type": "expense"},
]


@app.route(route="finance", methods=["GET", "POST", "OPTIONS"])
def finance(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()

    uid = user_id(req)

    # GET — list all transactions for this user
    if req.method == "GET":
        try:
            rows = query_items(
                "finance_tx",
                "SELECT * FROM c WHERE c.userId = @uid ORDER BY c.date DESC",
                [{"name": "@uid", "value": uid}],
                pk=uid,
            )
            return ok(rows)
        except Exception as e:
            logging.error("Finance GET error: %s", e)
            return err("Failed to fetch transactions", 500)

    # POST — add a transaction
    try:
        body = req.get_json()
    except ValueError:
        return err("Invalid JSON")

    amount = body.get("amount")
    if not body.get("desc") or amount is None:
        return err("desc and amount are required")

    doc = {
        "id":        new_id(),
        "userId":    uid,
        "desc":      str(body.get("desc", "")).strip(),
        "cat":       str(body.get("cat", "Other")).strip(),
        "date":      str(body.get("date", now_iso()[:10])),
        "amount":    float(amount),
        "type":      body.get("type", "expense"),
        "createdAt": now_iso(),
    }

    try:
        upsert("finance_tx", doc)
        return ok(doc, 201)
    except Exception as e:
        logging.error("Finance POST error: %s", e)
        return err("Failed to save transaction", 500)


@app.route(route="finance/{tx_id}", methods=["DELETE", "OPTIONS"])
def finance_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()
    uid   = user_id(req)
    tx_id = req.route_params.get("tx_id")
    try:
        delete_item("finance_tx", tx_id, uid)
        return ok({"deleted": tx_id})
    except Exception as e:
        logging.error("Finance DELETE error: %s", e)
        return err("Failed to delete transaction", 500)


@app.route(route="finance/seed", methods=["POST", "OPTIONS"])
def finance_seed(req: func.HttpRequest) -> func.HttpResponse:
    """Re-seed the user's finance data with sample transactions."""
    if req.method == "OPTIONS":
        return preflight()
    uid = user_id(req)

    # Delete existing
    try:
        existing = query_items(
            "finance_tx",
            "SELECT c.id FROM c WHERE c.userId = @uid",
            [{"name": "@uid", "value": uid}],
            pk=uid,
        )
        for row in existing:
            delete_item("finance_tx", row["id"], uid)
    except Exception:
        pass

    # Insert sample
    inserted = []
    for s in SAMPLE_TRANSACTIONS:
        doc = {**s, "id": new_id(), "userId": uid, "createdAt": now_iso()}
        upsert("finance_tx", doc)
        inserted.append(doc)

    return ok({"seeded": len(inserted), "transactions": inserted})


# ─────────────────────────────────────────────
# 3. SQL PLAYGROUND  →  Cosmos: sql_queries
# ─────────────────────────────────────────────

@app.route(route="sql/queries", methods=["GET", "POST", "OPTIONS"])
def sql_queries(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()

    uid = user_id(req)

    if req.method == "GET":
        try:
            rows = query_items(
                "sql_queries",
                "SELECT * FROM c WHERE c.userId = @uid ORDER BY c.createdAt DESC",
                [{"name": "@uid", "value": uid}],
                pk=uid,
            )
            return ok(rows)
        except Exception as e:
            logging.error("SQL GET error: %s", e)
            return err("Failed to fetch queries", 500)

    try:
        body = req.get_json()
    except ValueError:
        return err("Invalid JSON")

    sql = (body.get("sql") or "").strip()
    name = (body.get("name") or "Untitled Query").strip()
    if not sql:
        return err("sql is required")

    doc = {
        "id":        new_id(),
        "userId":    uid,
        "name":      name,
        "sql":       sql,
        "rowCount":  body.get("rowCount", 0),
        "createdAt": now_iso(),
    }

    try:
        upsert("sql_queries", doc)
        return ok(doc, 201)
    except Exception as e:
        logging.error("SQL POST error: %s", e)
        return err("Failed to save query", 500)


@app.route(route="sql/queries/{query_id}", methods=["DELETE", "OPTIONS"])
def sql_query_delete(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()
    uid      = user_id(req)
    query_id = req.route_params.get("query_id")
    try:
        delete_item("sql_queries", query_id, uid)
        return ok({"deleted": query_id})
    except Exception as e:
        logging.error("SQL DELETE error: %s", e)
        return err("Failed to delete query", 500)


# ─────────────────────────────────────────────
# 4. CSV ANALYZER  →  Cosmos: csv_uploads
# ─────────────────────────────────────────────

@app.route(route="csv", methods=["GET", "POST", "OPTIONS"])
def csv_route(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()

    uid = user_id(req)

    if req.method == "GET":
        try:
            rows = query_items(
                "csv_uploads",
                "SELECT * FROM c WHERE c.userId = @uid ORDER BY c.analyzedAt DESC",
                [{"name": "@uid", "value": uid}],
                pk=uid,
            )
            return ok(rows)
        except Exception as e:
            logging.error("CSV GET error: %s", e)
            return err("Failed to fetch CSV history", 500)

    # POST — save analysis metadata (not the raw CSV, just stats)
    try:
        body = req.get_json()
    except ValueError:
        return err("Invalid JSON")

    filename = (body.get("filename") or "unknown.csv").strip()

    doc = {
        "id":         new_id(),
        "userId":     uid,
        "filename":   filename,
        "rows":       int(body.get("rows", 0)),
        "columns":    int(body.get("columns", 0)),
        "headers":    body.get("headers", []),
        "numericCols":body.get("numericCols", []),
        "catCols":    body.get("catCols", []),
        "stats":      body.get("stats", {}),   # per-column stats dict
        "analyzedAt": now_iso(),
    }

    try:
        upsert("csv_uploads", doc)
        return ok(doc, 201)
    except Exception as e:
        logging.error("CSV POST error: %s", e)
        return err("Failed to save CSV analysis", 500)


# ─────────────────────────────────────────────
# 5. AI CHAT HISTORY  →  Cosmos: chat_history
# ─────────────────────────────────────────────

@app.route(route="chat", methods=["GET", "POST", "OPTIONS"])
def chat(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()

    session_id = req.params.get("session") or req.headers.get("X-Session-Id", "default")

    if req.method == "GET":
        try:
            rows = query_items(
                "chat_history",
                "SELECT * FROM c WHERE c.sessionId = @sid ORDER BY c.ts",
                [{"name": "@sid", "value": session_id}],
                pk=session_id,
            )
            return ok(rows)
        except Exception as e:
            logging.error("Chat GET error: %s", e)
            return err("Failed to fetch chat history", 500)

    # POST — append a message
    try:
        body = req.get_json()
    except ValueError:
        return err("Invalid JSON")

    role    = body.get("role", "user")
    content = (body.get("content") or "").strip()
    if not content:
        return err("content is required")

    doc = {
        "id":        new_id(),
        "sessionId": session_id,
        "role":      role,
        "content":   content,
        "ts":        now_iso(),
    }

    try:
        upsert("chat_history", doc)
        return ok(doc, 201)
    except Exception as e:
        logging.error("Chat POST error: %s", e)
        return err("Failed to save message", 500)


@app.route(route="chat/{session_id}", methods=["DELETE", "OPTIONS"])
def chat_clear(req: func.HttpRequest) -> func.HttpResponse:
    if req.method == "OPTIONS":
        return preflight()

    sid = req.route_params.get("session_id")
    try:
        rows = query_items(
            "chat_history",
            "SELECT c.id FROM c WHERE c.sessionId = @sid",
            [{"name": "@sid", "value": sid}],
            pk=sid,
        )
        for r in rows:
            delete_item("chat_history", r["id"], sid)
        return ok({"cleared": len(rows), "sessionId": sid})
    except Exception as e:
        logging.error("Chat DELETE error: %s", e)
        return err("Failed to clear session", 500)
