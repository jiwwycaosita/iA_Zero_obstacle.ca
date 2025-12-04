from supabase import create_client, Client


class SupabaseConnector:
    def __init__(self, url: str, key: str):
        self.client: Client = create_client(url, key)

    def upsert_status(self, job: str, status: str):
        self.client.table("job_status").upsert(
            {"job": job, "status": status}
        ).execute()
