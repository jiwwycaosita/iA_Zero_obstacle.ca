"""Connector for persisting alerts to Supabase."""

from __future__ import annotations

from typing import Any, Dict

from supabase import Client, create_client


class SupabaseConnector:
    """Wrap a Supabase client for storing monitoring alerts."""

    def __init__(self, url: str, key: str, table: str = "alerts") -> None:
        self.url = url
        self.key = key
        self.table = table
        self.client = self._init_client()

    def _init_client(self) -> Client:
        return create_client(self.url, self.key)

    def send_alert(self, payload: Dict[str, Any]) -> None:
        """Insert an alert payload into the configured Supabase table."""
        self.client.table(self.table).insert(payload).execute()
