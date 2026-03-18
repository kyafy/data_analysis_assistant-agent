import os
import json
from sqlalchemy import create_engine, text
from langchain_community.utilities import SQLDatabase
from app.core.config import settings

DB_CONFIG_PATH = "db_config.json"

def get_db_url_from_config():
    """Try to read DB config from file, return None if invalid."""
    if not os.path.exists(DB_CONFIG_PATH):
        return None
    try:
        with open(DB_CONFIG_PATH, "r") as f:
            config = json.load(f)
            # Basic validation
            required_keys = ["host", "port", "user", "password", "db"]
            if not all(k in config and config[k] for k in required_keys):
                return None
            
            return f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
    except Exception as e:
        print(f"Error reading db_config.json: {e}")
        return None

def test_connection(config: dict) -> bool:
    """Test connection with provided config dict."""
    try:
        url = f"mysql+pymysql://{config['user']}:{config['password']}@{config['host']}:{config['port']}/{config['db']}"
        engine = create_engine(url)
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"Connection test failed: {e}")
        return False

def get_db_engine():
    # Try dynamic config first
    db_url = get_db_url_from_config()
    
    if not db_url:
        # Fallback for dev if not set in config file
        db_url = getattr(settings, "DATABASE_URL", None)
        if not db_url:
            # Construct from components if available
            user = getattr(settings, "MYSQL_USER", "root")
            password = getattr(settings, "MYSQL_PASSWORD", "root")
            host = getattr(settings, "MYSQL_HOST", "127.0.0.1")
            port = getattr(settings, "MYSQL_PORT", "3307")
            db_name = getattr(settings, "MYSQL_DB", "data_analysis")
            db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{db_name}"
            
            # Using SQLite for now to ensure server starts without MySQL credentials
            # import os
            # db_path = "dev_data.db"
            # db_url = f"sqlite:///{db_path}"
    
    engine = create_engine(db_url)
    return engine

def get_sql_database() -> SQLDatabase:
    """
    Get LangChain SQLDatabase instance.
    This is used by the Toolkit.
    """
    engine = get_db_engine()
    # include_tables or sample_rows_in_table_info can be configured here
    return SQLDatabase(engine)
