#!/bin/bash

echo "Fixing Frontend Setup"
echo "===================="

cd frontend

# Clean up existing node_modules and lock file
echo "Cleaning up old installations..."
sudo rm -rf node_modules package-lock.json

# Install dependencies without sudo
echo "Installing dependencies..."
npm install

echo ""
echo "Starting the frontend..."
npm start