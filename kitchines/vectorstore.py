from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import threading
from pathlib import Path
from typing import Any

import numpy as np
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

EMBEDDING_DIM = 256

_connection: sqlite3.Connection | None = None
_lock = threading.Lock()


def is_enabled() -> bool:
    return getattr(settings, 'VECTOR_STORE_ENABLED', True)


def reset_vector_store() -> None:
    global _connection
    with _lock:
        if _connection is not None:
            _connection.close()
        _connection = None


def _store_path() -> Path:
    directory = Path(getattr(settings, 'VECTOR_STORE_DIR'))
    directory.mkdir(parents=True, exist_ok=True)
    return directory / 'kitchen_orders.sqlite3'


def get_connection() -> sqlite3.Connection:
    global _connection
    with _lock:
        if _connection is None:
            _connection = sqlite3.connect(_store_path(), check_same_thread=False)
            _connection.row_factory = sqlite3.Row
            _connection.execute(
                '''
                CREATE TABLE IF NOT EXISTS documents (
                    id TEXT PRIMARY KEY,
                    document TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    embedding BLOB NOT NULL
                )
                '''
            )
            _connection.commit()
        return _connection


def embed_text(text: str) -> np.ndarray:
    """Turn order text into a dense vector for later RAG retrieval."""
    vector = np.zeros(EMBEDDING_DIM, dtype=np.float32)
    normalized = ''.join(char.lower() if char.isalnum() else ' ' for char in text)
    tokens = [token for token in normalized.split() if token]
    grams = list(tokens)
    compact = ''.join(tokens)
    for index in range(max(len(compact) - 2, 0)):
        grams.append(compact[index : index + 3])

    for gram in grams:
        digest = hashlib.md5(gram.encode('utf-8')).digest()
        bucket = int.from_bytes(digest[:2], 'little') % EMBEDDING_DIM
        sign = 1.0 if digest[2] % 2 == 0 else -1.0
        vector[bucket] += sign

    norm = np.linalg.norm(vector)
    if norm:
        vector /= norm
    return vector


def _embedding_to_blob(vector: np.ndarray) -> bytes:
    return np.asarray(vector, dtype=np.float32).tobytes()


def _blob_to_embedding(blob: bytes) -> np.ndarray:
    return np.frombuffer(blob, dtype=np.float32).copy()


def order_document(order) -> str:
    kitchen_name = getattr(order.kitchen, 'name', 'Unknown kitchen')
    notes = (order.notes or '').strip() or 'None'
    created = ''
    if order.created_at:
        created = timezone.localtime(order.created_at).isoformat()
    return (
        f'Kitchen order {order.pk}. '
        f'Customer {order.customer_name} ordered {order.quantity} {order.item_name} '
        f'from {kitchen_name}. Status is {order.get_status_display()}. '
        f'Notes: {notes}. Created at {created}.'
    )


def order_metadata(order) -> dict[str, Any]:
    kitchen_name = getattr(order.kitchen, 'name', '')
    return {
        'order_id': int(order.pk),
        'kitchen_id': int(order.kitchen_id or 0),
        'kitchen_name': kitchen_name,
        'customer_name': order.customer_name,
        'item_name': order.item_name,
        'quantity': int(order.quantity),
        'status': order.status,
        'notes': order.notes or '',
        'source': 'kitchen_order',
    }


def upsert_order(order) -> None:
    if not is_enabled() or order.pk is None:
        return

    try:
        if not getattr(order, 'kitchen', None):
            order = type(order).objects.select_related('kitchen').get(pk=order.pk)
        document = order_document(order)
        embedding = embed_text(document)
        connection = get_connection()
        with _lock:
            connection.execute(
                '''
                INSERT INTO documents (id, document, metadata, embedding)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    document = excluded.document,
                    metadata = excluded.metadata,
                    embedding = excluded.embedding
                ''',
                (
                    f'order-{order.pk}',
                    document,
                    json.dumps(order_metadata(order)),
                    _embedding_to_blob(embedding),
                ),
            )
            connection.commit()
    except Exception:
        logger.exception('Failed to upsert order %s into the vector store', order.pk)


def delete_order(order_id: int) -> None:
    if not is_enabled():
        return

    try:
        connection = get_connection()
        with _lock:
            connection.execute('DELETE FROM documents WHERE id = ?', (f'order-{order_id}',))
            connection.commit()
    except Exception:
        logger.exception('Failed to delete order %s from the vector store', order_id)


def query_orders(query: str, n_results: int = 5) -> list[dict[str, Any]]:
    """Semantic search over stored orders. Use this as the retrieval step for RAG."""
    if not is_enabled() or not query.strip():
        return []

    connection = get_connection()
    with _lock:
        rows = connection.execute(
            'SELECT id, document, metadata, embedding FROM documents'
        ).fetchall()

    if not rows:
        return []

    query_vector = embed_text(query)
    scored = []
    for row in rows:
        stored = _blob_to_embedding(row['embedding'])
        if stored.size != query_vector.size:
            continue
        score = float(np.dot(query_vector, stored))
        scored.append(
            {
                'id': row['id'],
                'document': row['document'],
                'metadata': json.loads(row['metadata']),
                'distance': 1.0 - score,
                'score': score,
            }
        )

    scored.sort(key=lambda item: item['score'], reverse=True)
    return scored[:n_results]


def sync_all_orders() -> int:
    from .models import KitchenOrder

    if not is_enabled():
        return 0

    synced = 0
    for order in KitchenOrder.objects.select_related('kitchen').iterator():
        upsert_order(order)
        synced += 1
    return synced
