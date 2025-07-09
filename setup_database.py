#!/usr/bin/env python3
"""
Database Setup Script for Cattle Farm Storage
Run this script to initialize the database and create default admin user.
"""

import os
import hashlib
import base64
from dotenv import load_dotenv
import psycopg2

# Load environment variables
load_dotenv()

def create_scrypt_hash(password, salt=None):
    """Create a scrypt hash for password storage"""
    if salt is None:
        salt = b'temporary-salt'  # In production, use a random salt
    
    # Scrypt parameters
    n = 16384  # CPU cost
    r = 8      # Memory cost
    p = 1      # Parallelization
    
    # Generate hash
    hash_bytes = hashlib.scrypt(
        password.encode('utf-8'),
        salt=salt,
        n=n,
        r=r,
        p=p,
        dklen=64
    )
    
    # Format: scrypt:n:r:p$base64_salt$hex_hash
    salt_b64 = base64.b64encode(salt).decode('utf-8')
    hash_hex = hash_bytes.hex()
    
    return f"scrypt:{n}:{r}:{p}${salt_b64}${hash_hex}"

def get_db_connection():
    """Get database connection"""
    try:
        if os.environ.get('DATABASE_URL'):
            # Render deployment
            conn = psycopg2.connect(os.environ['DATABASE_URL'])
        else:
            # Local development with Supabase
            conn = psycopg2.connect(
                host=os.environ.get('SUPABASE_HOST', 'db.sklrifdmdyzofielkvsj.supabase.co'),
                database=os.environ.get('SUPABASE_DB', 'postgres'),
                user=os.environ.get('SUPABASE_USER', 'postgres'),
                password=os.environ.get('SUPABASE_PASSWORD', ''),
                port=os.environ.get('SUPABASE_PORT', '5432')
            )
        return conn
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return None

def setup_database():
    """Setup database tables and default admin user"""
    conn = get_db_connection()
    if not conn:
        print("❌ Cannot connect to database. Please check your environment variables.")
        return False
    
    try:
        cur = conn.cursor()
        
        # Create tables
        print("📋 Creating tables...")
        
        # Create cattle_info table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS cattle_info (
                id SERIAL PRIMARY KEY,
                breed VARCHAR(100),
                color VARCHAR(50),
                age INTEGER,
                shed_no VARCHAR(20),
                notes TEXT,
                photo1 VARCHAR(255),
                photo2 VARCHAR(255),
                photo3 VARCHAR(255),
                photo4 VARCHAR(255),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create doctors table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS doctors (
                id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                password VARCHAR(255) NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create health_log table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS health_log (
                id SERIAL PRIMARY KEY,
                cattle_id INTEGER REFERENCES cattle_info(id) ON DELETE CASCADE,
                checkup_date DATE,
                diagnosis TEXT,
                medicines TEXT,
                remarks TEXT,
                photo VARCHAR(255),
                doctor_username VARCHAR(100),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin user
        print("👤 Creating default admin user...")
        admin_password = "admin123"
        admin_hash = create_scrypt_hash(admin_password)
        
        cur.execute("""
            INSERT INTO doctors (username, password) 
            VALUES (%s, %s)
            ON CONFLICT (username) DO NOTHING
        """, ('admin', admin_hash))
        
        conn.commit()
        cur.close()
        conn.close()
        
        print("✅ Database setup completed successfully!")
        print(f"📝 Default admin credentials:")
        print(f"   Username: admin")
        print(f"   Password: {admin_password}")
        print("⚠️  Please change the default password after first login!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error setting up database: {e}")
        conn.rollback()
        conn.close()
        return False

if __name__ == "__main__":
    print("🚀 Cattle Farm Storage - Database Setup")
    print("=" * 50)
    
    success = setup_database()
    
    if success:
        print("\n🎉 Setup completed! You can now run the application.")
        print("Run: python app.py")
    else:
        print("\n❌ Setup failed. Please check your configuration.") 