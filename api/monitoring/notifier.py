"""Send alerts to downstream systems such as Supabase or WordPress."""

from __future__ import annotations

from typing import Any, Dict, Optional

from api.connectors.supabase_connector import SupabaseConnector


class Notifier:
    """Dispatch alert payloads to configured destinations."""

    def __init__(self, supabase_connector: SupabaseConnector, wordpress_webhook_url: Optional[str] = None) -> None:
        self.supabase_connector = supabase_connector
        self.wordpress_webhook_url = wordpress_webhook_url

    def notify(self, alert_content: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Send the alert content to Supabase and optionally to WordPress."""
        payload = {"content": alert_content, "metadata": metadata or {}}
        self.supabase_connector.send_alert(payload)
        if self.wordpress_webhook_url:
            self._notify_wordpress(payload)

    def _notify_wordpress(self, payload: Dict[str, Any]) -> None:
        """Placeholder for a WordPress webhook call."""
        # Implementation would POST to the configured WordPress webhook.
        # Left as a stub to avoid introducing network side effects in the template.
        return None
