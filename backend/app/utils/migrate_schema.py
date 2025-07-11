"""
Database Schema Migration Script
Adds new agent-related fields to existing tables
"""
import sqlite3
import logging
from pathlib import Path
from datetime import datetime

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = Path(__file__).parent.parent.parent / "docuforge.db"

def run_migration():
    """Run the database migration"""
    
    if not DB_PATH.exists():
        logger.error(f"Database file not found: {DB_PATH}")
        return False
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Backup current schema
        logger.info("Creating backup of current schema...")
        cursor.execute("CREATE TABLE IF NOT EXISTS migration_backup AS SELECT * FROM sqlite_master")
        
        # Add agent-related fields to documents table
        logger.info("Adding agent-related fields to documents table...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(documents)")
        existing_columns = [row[1] for row in cursor.fetchall()]
        
        new_columns = [
            ("agent_state", "TEXT DEFAULT 'idle'"),
            ("agent_config", "TEXT"),  # JSON stored as TEXT in SQLite
            ("preview_version", "INTEGER DEFAULT 1"),
            ("plan_data", "TEXT"),  # JSON stored as TEXT in SQLite
            ("last_preview_update", "DATETIME"),
            ("status", "TEXT DEFAULT 'draft'"),  # Add status column
        ]
        
        for column_name, column_def in new_columns:
            if column_name not in existing_columns:
                cursor.execute(f"ALTER TABLE documents ADD COLUMN {column_name} {column_def}")
                logger.info(f"Added column {column_name} to documents table")
        
        # Update existing records with default values
        cursor.execute("UPDATE documents SET last_preview_update = CURRENT_TIMESTAMP WHERE last_preview_update IS NULL")
        logger.info("Updated existing records with default values")
        
        # Update conversations table to enforce 1:1 relationship
        logger.info("Updating conversations table...")
        
        # Check if unique constraint exists
        cursor.execute("SELECT sql FROM sqlite_master WHERE name='conversations' AND type='table'")
        table_sql = cursor.fetchone()
        
        if table_sql and "UNIQUE" not in table_sql[0]:
            # Create new conversations table with unique constraint
            cursor.execute("""
                CREATE TABLE conversations_new (
                    id INTEGER PRIMARY KEY,
                    document_id INTEGER NOT NULL UNIQUE,
                    messages TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (document_id) REFERENCES documents (id)
                )
            """)
            
            # Copy existing data
            cursor.execute("""
                INSERT INTO conversations_new (id, document_id, messages, created_at)
                SELECT id, document_id, messages, created_at
                FROM conversations
            """)
            
            # Replace old table
            cursor.execute("DROP TABLE conversations")
            cursor.execute("ALTER TABLE conversations_new RENAME TO conversations")
            
            logger.info("Updated conversations table with unique constraint")
        
        # Create agent_messages table
        logger.info("Creating agent_messages table...")
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS agent_messages (
                id INTEGER PRIMARY KEY,
                document_id INTEGER NOT NULL,
                agent_type TEXT NOT NULL,
                message_type TEXT NOT NULL,
                content TEXT NOT NULL,
                message_metadata TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (document_id) REFERENCES documents (id)
            )
        """)
        
        # Create indexes for performance
        logger.info("Creating indexes...")
        
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_documents_agent_state ON documents(agent_state)",
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_document_id ON agent_messages(document_id)",
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_agent_type ON agent_messages(agent_type)",
            "CREATE INDEX IF NOT EXISTS idx_agent_messages_created_at ON agent_messages(created_at)",
        ]
        
        for index_sql in indexes:
            cursor.execute(index_sql)
        
        # Record migration
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS migration_history (
                id INTEGER PRIMARY KEY,
                migration_name TEXT NOT NULL,
                applied_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                description TEXT
            )
        """)
        
        cursor.execute("""
            INSERT INTO migration_history (migration_name, description)
            VALUES (?, ?)
        """, ("agent_system_migration", "Added agent orchestration system support"))
        
        conn.commit()
        conn.close()
        
        logger.info("Migration completed successfully!")
        return True
        
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

def rollback_migration():
    """Rollback the migration (if needed)"""
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        logger.info("Rolling back migration...")
        
        # Remove added columns from documents table
        # Note: SQLite doesn't support DROP COLUMN, so we'd need to recreate the table
        logger.warning("SQLite doesn't support DROP COLUMN. Manual rollback required.")
        
        # Drop new tables
        cursor.execute("DROP TABLE IF EXISTS agent_messages")
        
        # Record rollback
        cursor.execute("""
            INSERT INTO migration_history (migration_name, description)
            VALUES (?, ?)
        """, ("agent_system_rollback", "Rolled back agent orchestration system"))
        
        conn.commit()
        conn.close()
        
        logger.info("Rollback completed!")
        return True
        
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    
    logging.basicConfig(level=logging.INFO)
    
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        success = rollback_migration()
    else:
        success = run_migration()
    
    sys.exit(0 if success else 1)