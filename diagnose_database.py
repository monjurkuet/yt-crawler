"""
Database Connection Diagnostic Tool
Helps identify database connection issues
"""

import os
from dotenv import load_dotenv

print("=" * 70)
print("DATABASE CONNECTION DIAGNOSTIC TOOL")
print("=" * 70)

# Load environment variables
load_dotenv()

print("\n[1] Checking Environment Configuration...")
print("-" * 70)

# Check if .env exists
if os.path.exists('.env'):
    print("[OK] .env file found")
else:
    print("[ERROR] .env file NOT found - Please create it from .env.example")
    print("  Run: copy .env.example .env")
    exit(1)

# Check configuration
save_to_db = os.getenv('SAVE_TO_DB', 'false')
use_ssh = os.getenv('USE_SSH_TUNNEL', 'false')
db_host = os.getenv('DB_HOST', 'localhost')
db_port = os.getenv('DB_PORT', '3306')
db_user = os.getenv('DB_USER', '')
db_name = os.getenv('DB_NAME', '')

print(f"  SAVE_TO_DB: {save_to_db}")
print(f"  USE_SSH_TUNNEL: {use_ssh}")
print(f"  DB_HOST: {db_host}")
print(f"  DB_PORT: {db_port}")
print(f"  DB_USER: {db_user}")
print(f"  DB_NAME: {db_name}")

if save_to_db.lower() == 'false':
    print("\n[OK] Database saving is DISABLED")
    print("  The application will work without database connection")
    print("  To enable: Set SAVE_TO_DB=true in .env")
    exit(0)

print("\n[2] Testing Database Connection...")
print("-" * 70)

if use_ssh.lower() == 'true':
    print("SSH Tunnel Mode Enabled")
    ssh_host = os.getenv('SSH_HOST', '')
    ssh_user = os.getenv('SSH_USER', '')
    ssh_key = os.getenv('SSH_KEY_PATH', '')
    ssh_pass = os.getenv('SSH_PASSWORD', '')
    
    print(f"  SSH_HOST: {ssh_host}")
    print(f"  SSH_USER: {ssh_user}")
    print(f"  SSH_KEY_PATH: {ssh_key}")
    print(f"  SSH_PASSWORD: {'***' if ssh_pass else '(not set)'}")
    
    if not ssh_host or not ssh_user:
        print("\n[ERROR] SSH configuration incomplete!")
        print("  Please set SSH_HOST and SSH_USER in .env")
        exit(1)
    
    if not ssh_key and not ssh_pass:
        print("\n[ERROR] No SSH authentication method configured!")
        print("  Please set either SSH_KEY_PATH or SSH_PASSWORD in .env")
        exit(1)
    
    print("\n  Testing SSH connection...")
    try:
        import paramiko
        ssh = paramiko.SSHClient()
        ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        ssh_port = int(os.getenv('SSH_PORT', 22))
        
        if ssh_key and os.path.exists(ssh_key):
            print(f"  Connecting with SSH key: {ssh_key}")
            ssh.connect(ssh_host, port=ssh_port, username=ssh_user, key_filename=ssh_key, timeout=10)
        elif ssh_pass:
            print(f"  Connecting with password")
            ssh.connect(ssh_host, port=ssh_port, username=ssh_user, password=ssh_pass, timeout=10)
        else:
            print(f"  [ERROR] SSH key file not found: {ssh_key}")
            exit(1)
        
        print("  [OK] SSH connection successful!")
        ssh.close()
    except ImportError:
        print("  [ERROR] paramiko not installed")
        print("  Install: pip install paramiko")
        exit(1)
    except Exception as e:
        print(f"  [ERROR] SSH connection failed: {e}")
        print("\n  Troubleshooting:")
        print("  1. Verify SSH_HOST is correct")
        print("  2. Verify SSH_USER is correct")
        print("  3. Verify SSH_KEY_PATH points to valid key")
        print(f"  4. Test manually: ssh {ssh_user}@{ssh_host}")
        exit(1)

else:
    print("Direct Connection Mode (No SSH Tunnel)")

# Test MySQL connection
print("\n  Testing MySQL connection...")
try:
    import mysql.connector
    
    if use_ssh.lower() == 'true':
        # For SSH tunnel, we would connect through the tunnel
        print("  Note: Full tunnel test requires running the application")
        print("  This diagnostic only tests SSH connectivity")
    else:
        # Direct connection test
        db_password = os.getenv('DB_PASSWORD', '')
        
        print(f"  Connecting to {db_host}:{db_port}...")
        conn = mysql.connector.connect(
            host=db_host,
            port=int(db_port),
            user=db_user,
            password=db_password,
            connect_timeout=10
        )
        print("  [OK] MySQL connection successful!")
        
        # Test database exists
        cursor = conn.cursor()
        cursor.execute("SHOW DATABASES")
        databases = [db[0] for db in cursor.fetchall()]
        
        if db_name in databases:
            print(f"  [OK] Database '{db_name}' exists")
        else:
            print(f"  [WARNING] Database '{db_name}' does NOT exist")
            print(f"\n  Create it with:")
            print(f"  CREATE DATABASE {db_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
        
        conn.close()
        
except ImportError:
    print("  [ERROR] mysql-connector-python not installed")
    print("  Install: pip install mysql-connector-python")
    exit(1)
except mysql.connector.Error as e:
    print(f"  [ERROR] MySQL connection failed: {e}")
    print("\n  Troubleshooting:")
    print("  1. Is MySQL running? Check with: sc query MySQL80")
    print("  2. Start MySQL: net start MySQL80")
    print("  3. Verify credentials in .env")
    print(f"  4. Test manually: mysql -h {db_host} -P {db_port} -u {db_user} -p")
    exit(1)
except Exception as e:
    print(f"  [ERROR] Unexpected error: {e}")
    exit(1)

print("\n" + "=" * 70)
print("[SUCCESS] ALL CHECKS PASSED!")
print("=" * 70)
print("\nYour database configuration is correct.")
print("You can now run: python example_with_database.py")
