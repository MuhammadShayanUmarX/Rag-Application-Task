#!/usr/bin/env python3
"""
Test script for HR Copilot API
"""

import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("Testing health endpoint...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Health check: {response.status_code} - {response.json()}")

def test_query():
    """Test query endpoint"""
    print("\nTesting query endpoint...")
    
    test_questions = [
        "How do I request PTO?",
        "What's the reimbursement policy for travel?",
        "Can I work remotely?",
        "How many sick days do I get?"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        response = requests.post(f"{BASE_URL}/api/query/", json={
            "question": question,
            "user_id": "test_user"
        })
        
        if response.status_code == 200:
            data = response.json()
            print(f"Answer: {data['answer'][:100]}...")
            print(f"Confidence: {data['confidence_score']:.2f}")
            print(f"Forms: {len(data['suggested_forms'])}")
        else:
            print(f"Error: {response.status_code} - {response.text}")

def test_policies():
    """Test policies endpoint"""
    print("\nTesting policies endpoint...")
    response = requests.get(f"{BASE_URL}/api/policies/")
    
    if response.status_code == 200:
        policies = response.json()
        print(f"Found {len(policies)} policies:")
        for policy in policies:
            print(f"  - {policy['title']} ({policy['category']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_forms():
    """Test forms endpoint"""
    print("\nTesting forms endpoint...")
    response = requests.get(f"{BASE_URL}/api/forms/")
    
    if response.status_code == 200:
        forms = response.json()
        print(f"Found {len(forms)} forms:")
        for form in forms:
            print(f"  - {form['name']} ({form['category']})")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def test_analytics():
    """Test analytics endpoint"""
    print("\nTesting analytics endpoint...")
    response = requests.get(f"{BASE_URL}/api/analytics/")
    
    if response.status_code == 200:
        analytics = response.json()
        print(f"Analytics:")
        print(f"  - Total queries: {analytics['total_queries']}")
        print(f"  - Avg response time: {analytics['avg_response_time_ms']:.0f}ms")
        print(f"  - Avg confidence: {analytics['avg_confidence_score']:.2f}")
    else:
        print(f"Error: {response.status_code} - {response.text}")

def main():
    """Run all tests"""
    print("HR Copilot API Test Suite")
    print("=" * 40)
    
    try:
        test_health()
        test_policies()
        test_forms()
        test_query()
        test_analytics()
        
        print("\n" + "=" * 40)
        print("All tests completed!")
        
    except requests.exceptions.ConnectionError:
        print("Error: Could not connect to the API server.")
        print("Make sure the server is running with: uvicorn app.main:app --reload")
    except Exception as e:
        print(f"Error running tests: {e}")

if __name__ == "__main__":
    main()

