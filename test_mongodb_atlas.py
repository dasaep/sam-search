"""
Test script to verify MongoDB Atlas connection
"""

import sys
from pymongo import MongoClient
from config_db import MONGODB_CONFIG

def test_connection():
    """Test MongoDB Atlas connection"""
    
    print("Testing MongoDB Atlas connection...")
    print(f"Connection string: mongodb+srv://Cluster08122:****@cluster08122.jkmqf6j.mongodb.net")
    print(f"Database name: {MONGODB_CONFIG['database_name']}")
    
    try:
        # Connect to MongoDB Atlas
        client = MongoClient(MONGODB_CONFIG["connection_string"])
        
        # Ping the database to verify connection
        client.admin.command('ping')
        print("✓ Successfully connected to MongoDB Atlas!")
        
        # Access the database
        db = client[MONGODB_CONFIG["database_name"]]
        print(f"✓ Database '{MONGODB_CONFIG['database_name']}' accessed")
        
        # List collections
        collections = db.list_collection_names()
        if collections:
            print(f"✓ Existing collections: {', '.join(collections)}")
        else:
            print("✓ Database is ready (no collections yet)")
        
        # Test creating a collection
        test_collection = db.test_connection
        test_doc = {"test": "connection", "status": "successful"}
        result = test_collection.insert_one(test_doc)
        print(f"✓ Test document inserted with ID: {result.inserted_id}")
        
        # Clean up test document
        test_collection.delete_one({"_id": result.inserted_id})
        print("✓ Test document cleaned up")
        
        # Close connection
        client.close()
        print("\n✅ All tests passed! MongoDB Atlas is ready to use.")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Connection failed: {str(e)}")
        print("\nTroubleshooting tips:")
        print("1. Verify your MongoDB Atlas credentials are correct")
        print("2. Ensure your IP address is whitelisted in MongoDB Atlas")
        print("3. Check that the cluster is active and running")
        print("4. Verify network connectivity to MongoDB Atlas")
        
        return False

if __name__ == "__main__":
    success = test_connection()
    sys.exit(0 if success else 1)