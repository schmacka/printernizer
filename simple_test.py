"""
Simple debug test without Unicode characters
"""
import requests
import json
import time

def test_simple():
    print("Testing API import...")
    time.sleep(3)  # Wait for server
    
    url = "http://localhost:8000/api/v1/ideas/import"
    data = {
        "url": "https://makerworld.com/en/models/1812269-3d-hexa-tray#profileId-1933568",
        "category": "test",
        "priority": 3
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_simple()