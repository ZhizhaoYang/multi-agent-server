"""
Checkpointer Manager - Simple utility to create the best available checkpointer
"""

from typing import Optional
from langgraph.checkpoint.base import BaseCheckpointSaver
import os

# Optional PostgreSQL imports
try:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    HAS_POSTGRES = True
except ImportError:
    AsyncPostgresSaver = None
    HAS_POSTGRES = False

# SQLite imports
try:
    from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
    HAS_SQLITE = True
except ImportError:
    AsyncSqliteSaver = None
    HAS_SQLITE = False

ENV = os.environ.get("ENV", "dev")
DATABASE_URL = os.environ.get("SUPABASE_DB_URL")
SQLITE_DB_PATH = os.environ.get("SQLITE_DB_PATH", "./db/checkpoints/checkpoints.sqlite")

class CheckpointerManager:
    """Manages long-lived checkpointer connections"""

    def __init__(self):
        self._postgres_checkpointer = None
        self._sqlite_checkpointer = None
        self._postgres_cm = None
        self._sqlite_cm = None

    async def get_postgres_checkpointer(self) -> Optional[BaseCheckpointSaver]:
        """Get or create PostgreSQL checkpointer"""
        if self._postgres_checkpointer is not None:
            return self._postgres_checkpointer

        if not HAS_POSTGRES or not AsyncPostgresSaver or not DATABASE_URL:
            return None

        try:
            print("🔄 Attempting PostgreSQL checkpointer...")
            self._postgres_cm = AsyncPostgresSaver.from_conn_string(DATABASE_URL)
            self._postgres_checkpointer = await self._postgres_cm.__aenter__()
            await self._postgres_checkpointer.setup()
            print(f"✅ PostgreSQL checkpointer initialized successfully")
            return self._postgres_checkpointer
        except Exception:
            self._postgres_checkpointer = None
            self._postgres_cm = None
            raise

    async def get_sqlite_checkpointer(self) -> Optional[BaseCheckpointSaver]:
        """Get or create SQLite checkpointer"""
        if self._sqlite_checkpointer is not None:
            return self._sqlite_checkpointer

        if not HAS_SQLITE or not AsyncSqliteSaver:
            return None

        try:
            print("🔄 Attempting SQLite checkpointer...")
            os.makedirs(os.path.dirname(SQLITE_DB_PATH), exist_ok=True)
            self._sqlite_cm = AsyncSqliteSaver.from_conn_string(SQLITE_DB_PATH)
            self._sqlite_checkpointer = await self._sqlite_cm.__aenter__()
            await self._sqlite_checkpointer.setup()
            print(f"✅ SQLite checkpointer initialized at {SQLITE_DB_PATH}")
            return self._sqlite_checkpointer
        except Exception:
            self._sqlite_checkpointer = None
            self._sqlite_cm = None
            raise

    async def cleanup(self):
        """Clean up checkpointer connections"""
        if self._postgres_cm and self._postgres_checkpointer:
            try:
                await self._postgres_cm.__aexit__(None, None, None)
            except:
                pass
        if self._sqlite_cm and self._sqlite_checkpointer:
            try:
                await self._sqlite_cm.__aexit__(None, None, None)
            except:
                pass

        self._postgres_checkpointer = None
        self._sqlite_checkpointer = None
        self._postgres_cm = None
        self._sqlite_cm = None

# Global manager instance
_checkpointer_manager = CheckpointerManager()

async def get_best_checkpointer() -> Optional[BaseCheckpointSaver]:
    """
    Try to create the best available checkpointer.
    Returns None if no persistent checkpointer can be created.
    """
    # Try PostgreSQL first for production
    if ENV == "production" and DATABASE_URL and HAS_POSTGRES:
        try:
            checkpointer = await _checkpointer_manager.get_postgres_checkpointer()
            if checkpointer:
                return checkpointer
        except Exception as e:
            print(f"⚠️ Failed to initialize PostgreSQL checkpointer: {e}")

    # Try SQLite fallback
    if ENV == "dev" or HAS_SQLITE:
        try:
            checkpointer = await _checkpointer_manager.get_sqlite_checkpointer()
            if checkpointer:
                return checkpointer
        except Exception as e:
            print(f"⚠️ Failed to initialize SQLite checkpointer: {e}")

    return None

# Cleanup function for graceful shutdown
async def cleanup_checkpointers():
    """Clean up all checkpointer connections"""
    await _checkpointer_manager.cleanup()

async def clear_sqlite_history() -> dict:
    """
    Clear all conversation history from SQLite database.
    Returns statistics about the cleanup operation.
    """
    if not HAS_SQLITE or not AsyncSqliteSaver:
        return {"error": "SQLite not available"}

    try:
        import aiosqlite

        # Get count before cleanup
        async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
            cursor = await conn.execute("SELECT COUNT(*) FROM checkpoints")
            result = await cursor.fetchone()
            checkpoints_before = result[0] if result else 0

            cursor = await conn.execute("SELECT COUNT(*) FROM writes")
            result = await cursor.fetchone()
            writes_before = result[0] if result else 0

        # Clear the tables
        async with aiosqlite.connect(SQLITE_DB_PATH) as conn:
            await conn.execute("DELETE FROM checkpoints")
            await conn.execute("DELETE FROM writes")
            await conn.commit()

            # Reset auto-increment counters (only if sqlite_sequence table exists)
            try:
                await conn.execute("DELETE FROM sqlite_sequence WHERE name IN ('checkpoints', 'writes')")
                await conn.commit()
            except aiosqlite.OperationalError:
                # sqlite_sequence table doesn't exist, which is fine
                pass

        # Reset the checkpointer connection to pick up the cleared database
        if _checkpointer_manager._sqlite_checkpointer:
            await _checkpointer_manager.cleanup()

        return {
            "success": True,
            "checkpoints_cleared": checkpoints_before,
            "writes_cleared": writes_before,
            "message": f"Successfully cleared {checkpoints_before} checkpoints and {writes_before} writes"
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to clear SQLite history"
        }