"""
cosmos_client.py — Shared Cosmos DB helper
==========================================
All Azure Functions import from here.
One CosmosClient instance is reused across warm invocations.

Containers created automatically:
  portfolio  (db)
  ├── contacts         — contact form messages    (pk: /email)
  ├── finance_tx       — finance tracker records  (pk: /userId)
  ├── sql_queries      — saved SQL queries         (pk: /userId)
  ├── csv_uploads      — CSV analysis metadata     (pk: /userId)
  └── chat_history     — AI assistant sessions     (pk: /sessionId)
"""

import os
import logging
from azure.cosmos import CosmosClient, PartitionKey, exceptions

_client: CosmosClient | None = None
_db = None

DB_NAME = os.environ.get("COSMOS_DB_NAME", "portfolio")

CONTAINERS = {
    "contacts":      PartitionKey(path="/email"),
    "finance_tx":    PartitionKey(path="/userId"),
    "sql_queries":   PartitionKey(path="/userId"),
    "csv_uploads":   PartitionKey(path="/userId"),
    "chat_history":  PartitionKey(path="/sessionId"),
}


def get_client() -> CosmosClient:
    global _client
    if _client is None:
        conn = os.environ["COSMOS_CONNECTION_STRING"]
        _client = CosmosClient.from_connection_string(conn)
        logging.info("CosmosClient initialized")
    return _client


def get_database():
    global _db
    if _db is None:
        _db = get_client().create_database_if_not_exists(DB_NAME)
    return _db


def get_container(name: str):
    """Return (and auto-create) a container by name."""
    db = get_database()
    pk = CONTAINERS.get(name, PartitionKey(path="/id"))
    return db.create_container_if_not_exists(
        id=name,
        partition_key=pk,
        offer_throughput=400,  # shared across all containers in free tier
    )


def upsert(container_name: str, doc: dict) -> dict:
    c = get_container(container_name)
    return c.upsert_item(doc)


def query_items(container_name: str, query: str, params: list | None = None, pk: str | None = None) -> list:
    c = get_container(container_name)
    kwargs = {"query": query, "enable_cross_partition_query": pk is None}
    if params:
        kwargs["parameters"] = params
    if pk:
        kwargs["partition_key"] = pk
    return list(c.query_items(**kwargs))


def delete_item(container_name: str, item_id: str, pk: str) -> None:
    c = get_container(container_name)
    c.delete_item(item=item_id, partition_key=pk)
