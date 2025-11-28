"""Supabase connector for logging application events."""

import os
from typing import Any, Dict, Optional

from supabase import Client, create_client


class SupabaseClient:
    """Wrapper around Supabase Python client for inserting logs."""

    def __init__(
        self, url: Optional[str] = None, key: Optional[str] = None, table: Optional[str] = None
    ) -> None:
        self.url = url or os.getenv("SUPABASE_URL")
        self.key = key or os.getenv("SUPABASE_KEY")
        self.table = table or os.getenv("SUPABASE_TABLE", "ai_logs")

        if not self.url or not self.key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY are required for the Supabase connector.")

        self.client: Client = create_client(self.url, self.key)

    def log_message(self, payload: Dict[str, Any]) -> None:
        """Insert a payload into the configured table."""
        self.client.table(self.table).insert(payload).execute()
