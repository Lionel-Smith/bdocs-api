import asyncio
from concurrent.futures import ThreadPoolExecutor
from functools import wraps
from typing import Callable, Any
from src.database.oracle_db_service import OracleDBService

# Thread pool for Oracle sync operations
oracle_thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="oracle_")


def run_in_thread(func: Callable) -> Callable:
    """Decorator to run synchronous Oracle operations in thread pool"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            oracle_thread_pool,
            lambda: func(*args, **kwargs)
        )
    return wrapper


class AsyncOracleDBService:
    """Async wrapper for synchronous Oracle operations"""

    def __init__(self):
        self._service = None

    def _get_service(self) -> OracleDBService:
        """Get or create thread-local Oracle service instance"""
        if self._service is None:
            self._service = OracleDBService()
        return self._service

    @run_in_thread
    def execute_query(self, sql_file_path: str, params=None):
        """Execute query asynchronously via thread pool"""
        service = self._get_service()
        service.executeQuery(sql_file_path, params)
        return service.resultSet

    @run_in_thread
    def insert_one(self, sql_file_path: str, params):
        """Insert single record asynchronously"""
        service = self._get_service()
        service.insertOneRecord(sql_file_path, params)

    @run_in_thread
    def insert_many(self, sql_file_path: str, params):
        """Insert multiple records asynchronously"""
        service = self._get_service()
        service.insertMultipleRecords(sql_file_path, params)

    @run_in_thread
    def update(self, sql_file_path: str, params):
        """Update record asynchronously"""
        service = self._get_service()
        service.updateRecord(sql_file_path, params)

    async def close(self):
        """Close Oracle connections"""
        if self._service:
            await asyncio.get_event_loop().run_in_executor(
                oracle_thread_pool,
                self._service.disposeDBConnections
            )


# Global instance
async_oracle_service = AsyncOracleDBService()
