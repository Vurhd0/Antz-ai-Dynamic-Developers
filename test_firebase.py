"""
Quick test script to verify Firebase connection
Run this to check if Firebase is working: python test_firebase.py
"""
from services.firebase_service import FirebaseService
from config import Config
import os

print("="*60)
print("Firebase Connection Test")
print("="*60)
print(f"Credentials path from config: {Config.FIREBASE_CREDENTIALS_PATH}")
print(f"Current working directory: {os.getcwd()}")

# Resolve absolute path
creds_path = Config.FIREBASE_CREDENTIALS_PATH
if not os.path.isabs(creds_path):
    creds_path = os.path.join(os.getcwd(), creds_path)

print(f"Resolved absolute path: {creds_path}")
print(f"File exists: {os.path.exists(creds_path)}")
print("="*60)

# Initialize service
print("\nInitializing FirebaseService...")
service = FirebaseService()

print(f"\nInitialization status: {service._initialized}")
print(f"Database client: {service.db is not None}")

if service._initialized:
    print("\n✓ Firebase is initialized!")
    
    # Test connection
    print("\nTesting connection...")
    status = service.test_connection()
    print(f"Connection test result: {status}")
    
    # Try to create a test document
    print("\nTesting document creation...")
    test_result = service.create_document(
        collection="test",
        document_id="test_doc_123",
        data={"test": True, "message": "This is a test"}
    )
    print(f"Create document result: {test_result}")
    
    # Try to read it back
    print("\nTesting document retrieval...")
    test_doc = service.get_document("test", "test_doc_123")
    print(f"Retrieved document: {test_doc}")
    
    if test_doc:
        print("\n✅ SUCCESS! Firebase is working correctly!")
    else:
        print("\n⚠️  Document creation returned True but retrieval returned None")
        print("   This might indicate a permissions issue in Firestore")
else:
    print("\n❌ Firebase is NOT initialized!")
    if service._error_message:
        print(f"Error: {service._error_message}")

print("\n" + "="*60)

