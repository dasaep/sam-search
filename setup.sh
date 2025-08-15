#!/bin/bash

echo "SAM.gov Opportunity Analysis System - Setup Script"
echo "=================================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip install -r requirements.txt

# Test MongoDB Atlas connection
echo ""
echo "Testing MongoDB Atlas connection..."
python test_mongodb_atlas.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MongoDB Atlas connection successful!"
else
    echo ""
    echo "❌ MongoDB Atlas connection failed. Please check:"
    echo "   1. Your IP is whitelisted in MongoDB Atlas"
    echo "   2. Credentials in config_db.py are correct"
    echo "   3. Your cluster is running"
    exit 1
fi

# Install frontend dependencies
echo ""
echo "Installing frontend dependencies..."
cd frontend
npm install
cd ..

echo ""
echo "=================================================="
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Set your SAM.gov API key: export SAM_API_KEY='your-key-here'"
echo "2. Fetch opportunities: python search_db.py \$SAM_API_KEY"
echo "3. Start backend: python app.py"
echo "4. Start frontend: cd frontend && npm start"
echo ""
echo "Access the application at http://localhost:3000"