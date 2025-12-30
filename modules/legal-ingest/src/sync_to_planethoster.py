"""
Sync to PlanetHoster
Incremental synchronization of metadata from local Postgres to PlanetHoster cache
"""

import asyncio
import logging
import os
from datetime import datetime
from typing import Any, Dict, List, Optional

import asyncpg
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


class PlanetHosterSync:
    """
    Synchronizes metadata from local database to PlanetHoster cache
    Implements incremental sync with conflict resolution
    """
    
    def __init__(self):
        """Initialize sync manager"""
        # Local database connection
        self.local_host = os.getenv("POSTGRES_HOST", "localhost")
        self.local_port = int(os.getenv("POSTGRES_PORT", "5432"))
        self.local_user = os.getenv("POSTGRES_USER", "legal_ingest")
        self.local_password = os.getenv("POSTGRES_PASSWORD")
        self.local_db = os.getenv("POSTGRES_DB", "legal_data")
        
        # PlanetHoster database connection
        self.remote_host = os.getenv("PLANETHOSTER_POSTGRES_HOST")
        self.remote_port = int(os.getenv("PLANETHOSTER_POSTGRES_PORT", "5432"))
        self.remote_user = os.getenv("PLANETHOSTER_POSTGRES_USER")
        self.remote_password = os.getenv("PLANETHOSTER_POSTGRES_PASSWORD")
        self.remote_db = os.getenv("PLANETHOSTER_POSTGRES_DB")
        
        self.local_conn = None
        self.remote_conn = None
        
        logger.info("PlanetHosterSync initialized")
        
    async def connect(self):
        """Establish database connections"""
        try:
            # Connect to local database
            self.local_conn = await asyncpg.connect(
                host=self.local_host,
                port=self.local_port,
                user=self.local_user,
                password=self.local_password,
                database=self.local_db
            )
            logger.info("Connected to local database")
            
            # Connect to remote database
            if self.remote_host:
                self.remote_conn = await asyncpg.connect(
                    host=self.remote_host,
                    port=self.remote_port,
                    user=self.remote_user,
                    password=self.remote_password,
                    database=self.remote_db
                )
                logger.info("Connected to PlanetHoster database")
            else:
                logger.warning("PlanetHoster connection not configured")
                
        except Exception as e:
            logger.error(f"Failed to connect to databases: {e}")
            raise
            
    async def disconnect(self):
        """Close database connections"""
        if self.local_conn:
            await self.local_conn.close()
            logger.info("Disconnected from local database")
            
        if self.remote_conn:
            await self.remote_conn.close()
            logger.info("Disconnected from PlanetHoster database")
            
    async def sync_metadata(self, batch_size: int = 1000) -> Dict[str, int]:
        """
        Synchronize metadata incrementally
        
        Args:
            batch_size: Number of records to sync per batch
            
        Returns:
            Statistics about sync operation
        """
        if not self.remote_conn:
            logger.warning("Remote connection not available, skipping sync")
            return {"synced": 0, "skipped": 1}
            
        stats = {
            "synced": 0,
            "updated": 0,
            "errors": 0,
            "skipped": 0
        }
        
        try:
            # Get last sync timestamp from remote
            last_sync = await self._get_last_sync_timestamp()
            logger.info(f"Last sync: {last_sync}")
            
            # Get changed records from local database
            query = """
                SELECT id, title, url, category, jurisdiction, language, 
                       metadata, normalized_at, content_hash
                FROM documents
                WHERE normalized_at > $1
                ORDER BY normalized_at
                LIMIT $2
            """
            
            records = await self.local_conn.fetch(query, last_sync, batch_size)
            logger.info(f"Found {len(records)} records to sync")
            
            # Sync each record
            for record in records:
                try:
                    await self._sync_record(record)
                    stats["synced"] += 1
                    
                except Exception as e:
                    logger.error(f"Failed to sync record {record['id']}: {e}")
                    stats["errors"] += 1
                    
            # Update last sync timestamp
            await self._update_last_sync_timestamp()
            
            logger.info(f"Sync completed: {stats}")
            
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            stats["errors"] += 1
            
        return stats
        
    async def _get_last_sync_timestamp(self) -> datetime:
        """Get timestamp of last successful sync"""
        try:
            query = "SELECT last_sync FROM sync_status WHERE id = 1"
            result = await self.remote_conn.fetchval(query)
            
            if result:
                return result
            else:
                # First sync - start from beginning
                return datetime(2000, 1, 1)
                
        except Exception as e:
            logger.warning(f"Failed to get last sync timestamp: {e}")
            return datetime(2000, 1, 1)
            
    async def _update_last_sync_timestamp(self):
        """Update last sync timestamp"""
        try:
            query = """
                INSERT INTO sync_status (id, last_sync)
                VALUES (1, $1)
                ON CONFLICT (id)
                DO UPDATE SET last_sync = $1
            """
            await self.remote_conn.execute(query, datetime.utcnow())
            
        except Exception as e:
            logger.error(f"Failed to update sync timestamp: {e}")
            
    async def _sync_record(self, record: Dict[str, Any]):
        """
        Sync a single record to remote database
        
        Args:
            record: Record to sync
        """
        # Check if record exists
        existing = await self.remote_conn.fetchval(
            "SELECT id FROM documents WHERE id = $1",
            record['id']
        )
        
        if existing:
            # Update existing record
            query = """
                UPDATE documents
                SET title = $2, url = $3, category = $4, jurisdiction = $5,
                    language = $6, metadata = $7, normalized_at = $8,
                    content_hash = $9
                WHERE id = $1
            """
        else:
            # Insert new record
            query = """
                INSERT INTO documents
                (id, title, url, category, jurisdiction, language, metadata, 
                 normalized_at, content_hash)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            """
            
        await self.remote_conn.execute(
            query,
            record['id'],
            record['title'],
            record['url'],
            record['category'],
            record['jurisdiction'],
            record['language'],
            record['metadata'],
            record['normalized_at'],
            record['content_hash']
        )
        
    async def send_webhook(self, event: str, data: Dict[str, Any]):
        """
        Send webhook notification about changes
        
        Args:
            event: Event type (e.g., 'document_updated')
            data: Event data
        """
        # TODO: Implement webhook sending
        logger.info(f"Would send webhook: {event}")
        
        # In production:
        # 1. Build webhook payload
        # 2. Sign payload
        # 3. Send POST request to configured endpoint
        # 4. Handle retries
        
        pass
        
    async def run_daemon(self, interval_minutes: int = 15):
        """
        Run sync in daemon mode
        
        Args:
            interval_minutes: Minutes between sync runs
        """
        logger.info(f"Starting sync daemon (interval: {interval_minutes}m)")
        
        await self.connect()
        
        try:
            while True:
                try:
                    stats = await self.sync_metadata()
                    logger.info(f"Sync completed: {stats}")
                    
                except Exception as e:
                    logger.error(f"Sync error: {e}")
                    
                await asyncio.sleep(interval_minutes * 60)
                
        finally:
            await self.disconnect()
            

async def main():
    """Main entry point"""
    sync = PlanetHosterSync()
    await sync.run_daemon()
    

if __name__ == "__main__":
    asyncio.run(main())
