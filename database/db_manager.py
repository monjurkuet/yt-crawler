"""
Database module for YouTube Crawler
Handles MySQL connections via SSH tunnel with connection pooling and best practices
"""

import mysql.connector
from mysql.connector import pooling, Error
from sshtunnel import SSHTunnelForwarder
import os
from dotenv import load_dotenv
import logging
from contextlib import contextmanager
from typing import Optional, Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class DatabaseManager:
    """
    Manages database connections with SSH tunnel support and connection pooling.
    Implements singleton pattern to ensure single tunnel and connection pool.
    """
    
    _instance = None
    _tunnel = None
    _connection_pool = None
    
    def __new__(cls):
        """Singleton pattern implementation"""
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        """Initialize database manager with SSH tunnel and connection pool"""
        if self._initialized:
            return
            
        self._initialized = True
        self.use_ssh = os.getenv('USE_SSH_TUNNEL', 'false').lower() == 'true'
        
        # SSH Configuration
        self.ssh_host = os.getenv('SSH_HOST')
        self.ssh_port = int(os.getenv('SSH_PORT', 22))
        self.ssh_user = os.getenv('SSH_USER')
        self.ssh_password = os.getenv('SSH_PASSWORD')
        self.ssh_key_path = os.getenv('SSH_KEY_PATH')
        
        # Database Configuration
        self.remote_db_host = os.getenv('REMOTE_DB_HOST', '127.0.0.1')
        self.remote_db_port = int(os.getenv('REMOTE_DB_PORT', 3306))
        self.local_bind_port = int(os.getenv('LOCAL_BIND_PORT', 3307))
        
        self.db_user = os.getenv('DB_USER')
        self.db_password = os.getenv('DB_PASSWORD')
        self.db_name = os.getenv('DB_NAME')
        
        # Connection pool configuration
        self.pool_name = "youtube_crawler_pool"
        self.pool_size = int(os.getenv('DB_POOL_SIZE', 5))
        
    def start_ssh_tunnel(self):
        """Start SSH tunnel if not already running"""
        if not self.use_ssh:
            logger.info("SSH tunnel disabled, connecting directly to database")
            return
            
        if self._tunnel is not None and self._tunnel.is_active:
            logger.info("SSH tunnel already active")
            return
        
        try:
            logger.info(f"Starting SSH tunnel to {self.ssh_host}:{self.ssh_port}")
            
            # Use SSH key if provided, otherwise use password
            ssh_auth = {}
            if self.ssh_key_path and os.path.exists(self.ssh_key_path):
                ssh_auth['ssh_pkey'] = self.ssh_key_path
                logger.info(f"Using SSH key authentication: {self.ssh_key_path}")
            elif self.ssh_password:
                ssh_auth['ssh_password'] = self.ssh_password
                logger.info("Using SSH password authentication")
            else:
                raise ValueError("No SSH authentication method provided")
            
            self._tunnel = SSHTunnelForwarder(
                (self.ssh_host, self.ssh_port),
                ssh_username=self.ssh_user,
                **ssh_auth,
                remote_bind_address=(self.remote_db_host, self.remote_db_port),
                local_bind_address=('127.0.0.1', self.local_bind_port)
            )
            
            self._tunnel.start()
            logger.info(f"SSH tunnel established on local port {self._tunnel.local_bind_port}")
            
        except Exception as e:
            logger.error(f"Failed to start SSH tunnel: {e}")
            raise
    
    def stop_ssh_tunnel(self):
        """Stop SSH tunnel if running"""
        if self._tunnel is not None and self._tunnel.is_active:
            self._tunnel.stop()
            logger.info("SSH tunnel stopped")
    
    def create_connection_pool(self):
        """Create MySQL connection pool"""
        if self._connection_pool is not None:
            logger.info("Connection pool already exists")
            return
        
        try:
            # Determine host and port based on SSH tunnel usage
            if self.use_ssh:
                db_host = '127.0.0.1'
                db_port = self.local_bind_port
            else:
                db_host = os.getenv('DB_HOST', 'localhost')
                db_port = int(os.getenv('DB_PORT', 3306))
            
            logger.info(f"Creating connection pool to {db_host}:{db_port}")
            
            self._connection_pool = pooling.MySQLConnectionPool(
                pool_name=self.pool_name,
                pool_size=self.pool_size,
                pool_reset_session=True,
                host=db_host,
                port=db_port,
                user=self.db_user,
                password=self.db_password,
                database=self.db_name,
                autocommit=False,
                charset='utf8mb4',
                collation='utf8mb4_unicode_ci',
                use_pure=True,
                ssl_disabled=True
            )
            
            logger.info(f"Connection pool created with {self.pool_size} connections")
            
        except Error as e:
            logger.error(f"Failed to create connection pool: {e}")
            raise
    
    def initialize(self):
        """Initialize SSH tunnel and connection pool"""
        try:
            if self.use_ssh:
                self.start_ssh_tunnel()
            self.create_connection_pool()
            logger.info("Database manager initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            self.cleanup()
            raise
    
    @contextmanager
    def get_connection(self):
        """
        Context manager for database connections.
        Automatically handles connection acquisition and release.
        
        Usage:
            with db_manager.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM videos")
        """
        connection = None
        try:
            connection = self._connection_pool.get_connection()
            yield connection
        except Error as e:
            logger.error(f"Database connection error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """
        Context manager for database cursor.
        Automatically handles connection, cursor, commit, and cleanup.
        
        Usage:
            with db_manager.get_cursor() as cursor:
                cursor.execute("SELECT * FROM videos")
                results = cursor.fetchall()
        """
        connection = None
        cursor = None
        try:
            connection = self._connection_pool.get_connection()
            cursor = connection.cursor(dictionary=dictionary)
            yield cursor
            connection.commit()
        except Error as e:
            logger.error(f"Database cursor error: {e}")
            if connection:
                connection.rollback()
            raise
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
    
    def cleanup(self):
        """Cleanup resources (connection pool and SSH tunnel)"""
        try:
            if self._connection_pool:
                # Close all connections in the pool
                logger.info("Closing connection pool")
                self._connection_pool = None
            
            if self.use_ssh:
                self.stop_ssh_tunnel()
                
            logger.info("Database manager cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
    
    def __del__(self):
        """Destructor to ensure cleanup"""
        self.cleanup()


# Global database manager instance
db_manager = DatabaseManager()


def init_database():
    """Initialize database connection"""
    db_manager.initialize()


def close_database():
    """Close database connection"""
    db_manager.cleanup()


# Convenience functions
@contextmanager
def get_db_connection():
    """Get database connection (convenience wrapper)"""
    with db_manager.get_connection() as conn:
        yield conn


@contextmanager
def get_db_cursor(dictionary=True):
    """Get database cursor (convenience wrapper)"""
    with db_manager.get_cursor(dictionary=dictionary) as cursor:
        yield cursor
