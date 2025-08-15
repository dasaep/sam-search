"""
Test DNS resolution for MongoDB Atlas
"""

import socket
import dns.resolver

def test_dns():
    print("Testing DNS resolution for MongoDB Atlas...")
    
    try:
        # Test basic DNS
        host = "cluster08122.jkmqf6j.mongodb.net"
        print(f"Resolving {host}...")
        
        # Try socket resolution
        ip = socket.gethostbyname(host)
        print(f"✓ Basic DNS works: {host} -> {ip}")
        
    except socket.gaierror as e:
        print(f"✗ DNS resolution failed: {e}")
        print("\nTry using a direct connection string instead")
        return False
    
    try:
        # Try SRV record resolution
        print("\nChecking MongoDB SRV records...")
        resolver = dns.resolver.Resolver()
        srv_records = resolver.resolve('_mongodb._tcp.cluster08122.jkmqf6j.mongodb.net', 'SRV')
        
        for srv in srv_records:
            print(f"✓ SRV Record: {srv.target}:{srv.port}")
        
        return True
        
    except Exception as e:
        print(f"✗ SRV resolution failed: {e}")
        print("\nThis might be a DNS issue. Try:")
        print("1. Check your internet connection")
        print("2. Try using Google's DNS (8.8.8.8)")
        print("3. Use the standard connection string format instead of SRV")
        return False

if __name__ == "__main__":
    test_dns()