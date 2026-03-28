import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load .env from parent directory
load_dotenv(os.path.join(os.path.dirname(__file__), '../../.env'))

def get_db_connection():
    db_url = os.environ.get("DATABASE_URL")
    if not db_url or "YOUR_SUPABASE" in db_url:
        print("[DB] Warning: Please configure a real DATABASE_URL in the root .env file.")
        return None
    
    try:
        conn = psycopg2.connect(db_url, cursor_factory=RealDictCursor)
        conn.autocommit = True
        return conn
    except Exception as e:
        print(f"[DB] Error connecting to database: {e}")
        return None

def verify_schema():
    conn = get_db_connection()
    if conn:
        try:
            with conn.cursor() as cur:
                print("[DB] Verifying and scaffolding projects table schema...")
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS projects (
                        id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                        name VARCHAR(255) NOT NULL,
                        repo_url TEXT NOT NULL,
                        sub_directory VARCHAR(255) DEFAULT '/',
                        assigned_port INTEGER,
                        status VARCHAR(50) DEFAULT 'QUEUED',
                        env_vars JSONB DEFAULT '{}',
                        framework VARCHAR(50),
                        build_duration FLOAT,
                        created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                    );
                """)
                
                # Migration: add sub_directory column to existing table
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS sub_directory VARCHAR(255) DEFAULT '/';")
                except Exception:
                    pass
                
                # Migration: add env_vars column to existing table
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS env_vars JSONB DEFAULT '{}';")
                except Exception:
                    pass

                # Migration: add framework column to existing table
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS framework VARCHAR(50);")
                except Exception:
                    pass

                # Migration: add build_duration column to existing table
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS build_duration FLOAT;")
                except Exception:
                    pass

                # Migration for Dual Deployment modes
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS deployment_type VARCHAR(50) DEFAULT 'MANAGED';")
                except Exception:
                    pass
                
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS custom_worker_url VARCHAR(255);")
                except Exception:
                    pass
                
                try:
                    cur.execute("ALTER TABLE projects ADD COLUMN IF NOT EXISTS memory_limit INTEGER;")
                except Exception:
                    pass
                
                print("[DB] Database schema is ready.")
        except Exception as e:
            print(f"[DB] Database schema verification failed: {e}")
        finally:
            conn.close()
    else:
        print("[DB] Skipping schema verification due to missing valid connection string.")
            
if __name__ == "__main__":
    verify_schema()