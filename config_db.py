"""
Database configuration for MongoDB Atlas
"""

import os

# MongoDB Atlas connection configuration
MONGODB_CONFIG = {
    "connection_string": os.getenv(
        "MONGODB_URI",
        "mongodb+srv://Cluster08122:dVBYQ0R4aHZx@cluster08122.jkmqf6j.mongodb.net/?retryWrites=true&w=majority"
    ),
    "database_name": os.getenv("MONGODB_DATABASE", "sam_opportunities")
}

# You can override these with environment variables
# export MONGODB_URI="your-custom-connection-string"
# export MONGODB_DATABASE="your-database-name"