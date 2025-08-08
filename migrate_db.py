#!/usr/bin/env python3
"""
Database migration script to add Stripe payment columns
"""
import sqlite3
import os

def migrate_database():
    db_path = 'instance/seo_tool.db'
    
    if not os.path.exists(db_path):
        print(f"Database {db_path} not found. Creating new database...")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Check if columns already exist
    cursor.execute("PRAGMA table_info(user)")
    columns = [column[1] for column in cursor.fetchall()]
    
    new_columns = [
        ('stripe_customer_id', 'VARCHAR(100)'),
        ('stripe_subscription_id', 'VARCHAR(100)'),
        ('subscription_status', 'VARCHAR(20) DEFAULT "trialing"'),
        ('current_period_end', 'DATETIME')
    ]
    
    for column_name, column_type in new_columns:
        if column_name not in columns:
            try:
                cursor.execute(f'ALTER TABLE user ADD COLUMN {column_name} {column_type}')
                print(f"✅ Added column: {column_name}")
            except sqlite3.Error as e:
                print(f"❌ Error adding column {column_name}: {e}")
        else:
            print(f"ℹ️  Column {column_name} already exists")
    
    conn.commit()
    conn.close()
    print("🎉 Database migration completed!")

if __name__ == '__main__':
    migrate_database()