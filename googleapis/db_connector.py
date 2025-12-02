import mysql.connector
from sshtunnel import SSHTunnelForwarder, BaseSSHTunnelForwarderError
import warnings
import paramiko
from config_manager import ConfigManager # Import ConfigManager
import logging
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
    after_log
)

# Suppress Paramiko UserWarning about missing cryptography library
warnings.filterwarnings('ignore', category=UserWarning, module='paramiko')

class DBConnector:
    def __init__(self):
        self.config = ConfigManager()
        self.ssh_tunnel = None
        self.mysql_conn = None
        self.logger = self._setup_logging()

        self.create_table_sql = """
CREATE TABLE IF NOT EXISTS youtube_videos (
    video_id VARCHAR(255) PRIMARY KEY,
    channel_id VARCHAR(255),
    published_at DATETIME,
    title VARCHAR(255),
    description TEXT,
    tags TEXT, -- Storing tags as a JSON string
    category_id VARCHAR(50),
    default_language VARCHAR(10),
    duration VARCHAR(50), -- Storing YouTube's ISO 8601 duration format
    caption BOOLEAN,
    view_count BIGINT,
    like_count BIGINT,
    comment_count BIGINT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
"""

    def _setup_logging(self):
        logger = logging.getLogger('db_connector')
        if not logger.handlers: # Prevent adding multiple handlers
            handler = logging.StreamHandler() # Or a file handler
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger

    # Helper for retry condition
    def _is_connection_error(self, exception):
        return isinstance(exception, (
            mysql.connector.Error, 
            paramiko.SSHException, 
            BaseSSHTunnelForwarderError
        ))

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=10),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type((mysql.connector.Error, paramiko.SSHException, BaseSSHTunnelForwarderError)),
        after=after_log(logging.getLogger('db_connector'), logging.WARNING)
    )
    def establish_connection(self):
        self.close_connection() # Ensure previous connections are closed before retrying
        try:
            # Establish SSH tunnel
            self.logger.info("Attempting to establish SSH tunnel...")
            self.ssh_tunnel = SSHTunnelForwarder(
                (self.config.SSH_HOST, 22),
                ssh_username=self.config.SSH_USERNAME,
                ssh_pkey=self.config.SSH_PRIVATEKEY_PATH,
                remote_bind_address=(self.config.REMOTE_MYSQL_HOST, self.config.REMOTE_MYSQL_PORT),
                local_bind_address=('0.0.0.0', self.config.LOCAL_PORT)
            )
            self.ssh_tunnel.start()
            self.logger.info(f"SSH tunnel established on local port {self.ssh_tunnel.local_bind_port}")

            # Connect to MySQL
            self.logger.info("Attempting to connect to MySQL database...")
            self.mysql_conn = mysql.connector.connect(
                host='localhost',
                port=self.ssh_tunnel.local_bind_port,
                user='adminuser',
                password=self.config.DATABASE_PASSWORD,
                database=self.config.DATABASE_NAME
            )
            if self.mysql_conn.is_connected():
                self.logger.info("Successfully connected to MySQL database.")
                return True
            else:
                self.logger.error("Failed to connect to MySQL database after SSH tunnel.")
                self.close_connection() # Close partially established connections
                return False

        except (mysql.connector.Error, paramiko.SSHException, BaseSSHTunnelForwarderError) as e:
            self.logger.error(f"Connection error during establish_connection: {e}")
            self.close_connection()
            raise # Re-raise to trigger retry
        except Exception as e:
            self.logger.critical(f"An unexpected critical error occurred during connection establishment: {e}")
            self.close_connection()
            return False

    def create_table(self):
        if self.mysql_conn and self.mysql_conn.is_connected():
            try:
                cursor = self.mysql_conn.cursor()
                self.logger.info("Executing CREATE TABLE statement...")
                cursor.execute(self.create_table_sql)
                self.mysql_conn.commit()
                cursor.close()
                self.logger.info("Table 'youtube_videos' ensured.")
                return True
            except mysql.connector.Error as err:
                if err.errno == 1050: # Table already exists
                    self.logger.info("Table 'youtube_videos' already exists. Skipping creation.")
                else:
                    self.logger.error(f"Error creating table: {err}")
                return False
            except Exception as e:
                self.logger.error(f"An unexpected error occurred during table creation: {e}")
                return False
        else:
            self.logger.warning("Cannot create table: MySQL connection is not active.")
        return False

    def close_connection(self):
        if self.mysql_conn and self.mysql_conn.is_connected():
            self.mysql_conn.close()
            self.mysql_conn = None
            self.logger.info("MySQL connection closed.")
        if self.ssh_tunnel and self.ssh_tunnel.is_active:
            self.ssh_tunnel.stop()
            self.ssh_tunnel = None
            self.logger.info("SSH tunnel stopped.")

# Example usage
if __name__ == '__main__':
    db_connector = DBConnector()
    if db_connector.establish_connection():
        print("Database connection successful.")
        db_connector.create_table()
        db_connector.close_connection()
        print("Connection closed.")
    else:
        print("Failed to connect to database.")
