"""
Fixed Database configuration for MongoDB Atlas
Using standard connection string instead of SRV
"""

import os

# MongoDB Atlas connection configuration
# Using standard format instead of SRV which is having DNS issues
MONGODB_CONFIG = {
    "connection_string": os.getenv(
        "MONGODB_URI",
        "mongodb://Cluster08122:dVBYQ0R4aHZx@cluster08122-shard-00-00.jkmqf6j.mongodb.net:27017,cluster08122-shard-00-01.jkmqf6j.mongodb.net:27017,cluster08122-shard-00-02.jkmqf6j.mongodb.net:27017/sam_opportunities?ssl=true&replicaSet=atlas-bhbxbs-shard-0&authSource=admin&retryWrites=true&w=majority"
    ),
    "database_name": os.getenv("MONGODB_DATABASE", "sam_opportunities")
}

# Alternative: If the above doesn't work, try the local MongoDB instead
MONGODB_LOCAL = {
    "connection_string": "mongodb://localhost:27017/",
    "database_name": "sam_opportunities"
}