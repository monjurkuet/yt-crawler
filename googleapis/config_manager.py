import os
from google.colab import userdata # Keep for direct Colab execution, but prefer os.environ

class ConfigManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._load_config()
        return cls._instance

    def _load_config(self):
        # Helper to get config, prioritizing environment variables
        def get_config_value(key):
            return os.environ.get(key) or userdata.get(key)

        # YouTube API Credentials
        self.API_KEY = get_config_value('API_KEY')

        # SSH Tunnel & MySQL Database Credentials
        self.SSH_HOST = get_config_value('SSH_HOST')
        self.SSH_USERNAME = 'administrator' # This is often a fixed username for cloud VMs
        self.SSH_PRIVATEKEY_PATH = get_config_value('SSH_PRIVATEKEY_PATH') # Path to private key on Colab
        self.LOCAL_PORT = 3307 # Local port for SSH tunnel
        self.REMOTE_MYSQL_HOST = '127.0.0.1'
        self.REMOTE_MYSQL_PORT = 3306
        self.DATABASE_NAME = get_config_value('DATABASE_NAME')
        self.DATABASE_PASSWORD = get_config_value('DATABASE_PASSWORD')

        # Google Drive Service Account Key File
        self.SERVICE_ACCOUNT_KEY_FILE_PATH = get_config_value('SERVICE_ACCOUNT_KEY_FILE')

        # File path for video IDs
        self.VIDEO_IDS_FILE_PATH = '/content/drive/MyDrive/cloudaccess/videoids.txt'

    def get_config(self):
        return {
            'API_KEY': self.API_KEY,
            'SSH_HOST': self.SSH_HOST,
            'SSH_USERNAME': self.SSH_USERNAME,
            'SSH_PRIVATEKEY_PATH': self.SSH_PRIVATEKEY_PATH,
            'LOCAL_PORT': self.LOCAL_PORT,
            'REMOTE_MYSQL_HOST': self.REMOTE_MYSQL_HOST,
            'REMOTE_MYSQL_PORT': self.REMOTE_MYSQL_PORT,
            'DATABASE_NAME': self.DATABASE_NAME,
            'DATABASE_PASSWORD': self.DATABASE_PASSWORD,
            'SERVICE_ACCOUNT_KEY_FILE_PATH': self.SERVICE_ACCOUNT_KEY_FILE_PATH,
            'VIDEO_IDS_FILE_PATH': self.VIDEO_IDS_FILE_PATH
        }

# Example usage (for testing purposes, not part of the module's core function)
if __name__ == '__main__':
    config = ConfigManager()
    print("API Key:", config.API_KEY)
    print("SSH Host:", config.SSH_HOST)
    print("Database Name:", config.DATABASE_NAME)
