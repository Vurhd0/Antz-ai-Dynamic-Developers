import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, List, Dict
from config import Config
import json

# Singleton instance
_firebase_service_instance = None

def get_firebase_service() -> 'FirebaseService':
    """Get or create the singleton FirebaseService instance"""
    global _firebase_service_instance
    if _firebase_service_instance is None:
        _firebase_service_instance = FirebaseService()
    return _firebase_service_instance

class FirebaseService:
    """Service class for Firebase Firestore operations"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        import os
        self.db = None
        self._initialized = False
        self._error_message = None
        
        # Resolve absolute path for credentials
        creds_path = Config.FIREBASE_CREDENTIALS_PATH
        if not os.path.isabs(creds_path):
            # If relative path, resolve from current working directory
            creds_path = os.path.join(os.getcwd(), creds_path)
        
        if not firebase_admin._apps:
            try:
                if os.path.exists(creds_path):
                    print(f"✓ Found Firebase credentials at: {creds_path}")
                    try:
                        cred = credentials.Certificate(creds_path)
                        print("✓ Credentials loaded successfully")
                    except Exception as cred_error:
                        self._error_message = f"Failed to load credentials: {str(cred_error)}"
                        print(f"❌ {self._error_message}")
                        print("⚠️  Running in MOCK MODE - No data will be persisted!")
                        return
                    
                    try:
                        firebase_admin.initialize_app(cred)
                        print("✓ Firebase app initialized")
                    except ValueError as ve:
                        # App might already be initialized
                        if "already exists" in str(ve):
                            print("⚠️  Firebase app already initialized (this is OK)")
                        else:
                            raise
                    except Exception as init_error:
                        self._error_message = f"Failed to initialize Firebase app: {str(init_error)}"
                        print(f"❌ {self._error_message}")
                        print("⚠️  Running in MOCK MODE - No data will be persisted!")
                        return
                    
                    try:
                        self.db = firestore.client()
                        self._initialized = True
                        print("✓ Firestore client created")
                        print("✓ Firestore Initialized: True")
                        print("✓ Firebase connection successful!")
                        
                        # Test the connection by trying to access a collection
                        test_collection = self.db.collection("_test")
                        print("✓ Firebase connection test passed")
                    except Exception as db_error:
                        self._error_message = f"Failed to create Firestore client: {str(db_error)}"
                        print(f"❌ {self._error_message}")
                        print("⚠️  Running in MOCK MODE - No data will be persisted!")
                        return
                else:
                    self._error_message = f"Firebase credentials file not found at: {creds_path}"
                    print(f"❌ {self._error_message}")
                    print("⚠️  Running in MOCK MODE - No data will be persisted!")
                    print(f"   Expected path: {creds_path}")
                    print(f"   Current working directory: {os.getcwd()}")
                    print(f"   Config.FIREBASE_CREDENTIALS_PATH: {Config.FIREBASE_CREDENTIALS_PATH}")
            except Exception as e:
                import traceback
                self._error_message = f"Failed to initialize Firebase: {str(e)}"
                print(f"❌ {self._error_message}")
                print(f"❌ Full error: {traceback.format_exc()}")
                print("⚠️  Running in MOCK MODE - No data will be persisted!")
        else:
            try:
                self.db = firestore.client()
                self._initialized = True
                print("✓ Firestore Initialized: True (using existing app)")
            except Exception as e:
                self._error_message = f"Failed to get Firestore client: {str(e)}"
                print(f"❌ {self._error_message}")
                print("⚠️  Running in MOCK MODE - No data will be persisted!")
        
        # Final status print
        if not self._initialized:
            print("\n" + "="*60)
            print("⚠️  FIREBASE NOT INITIALIZED - MOCK MODE ACTIVE")
            print("="*60)
            print("To fix:")
            print("1. Download Firebase service account key JSON file")
            print("2. Place it in your project root")
            print("3. Update Config.FIREBASE_CREDENTIALS_PATH to match the filename")
            print("="*60 + "\n")
    
    def create_document(self, collection: str, document_id: str, data: dict) -> bool:
        """Create a document in Firestore"""
        if not self._initialized or not self.db:
            print(f"⚠️  MOCK MODE: Would create document {document_id} in {collection}")
            print(f"   (No data actually saved - Firebase not initialized)")
            print(f"   _initialized: {self._initialized}, db: {self.db is not None}")
            return True
        try:
            self.db.collection(collection).document(document_id).set(data)
            print(f"✓ Created document {document_id} in {collection}")
            print(f"   Collection: {collection}, Document ID: {document_id}")
            return True
        except Exception as e:
            import traceback
            print(f"❌ Error creating document: {str(e)}")
            print(f"❌ Full traceback: {traceback.format_exc()}")
            return False
    
    def get_document(self, collection: str, document_id: str) -> Optional[dict]:
        """Get a document from Firestore"""
        if not self._initialized or not self.db:
            print(f"⚠️  MOCK MODE: Would get document {document_id} from {collection}")
            print(f"   (Returns None - Firebase not initialized)")
            return None
        try:
            doc = self.db.collection(collection).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"❌ Error getting document: {str(e)}")
            return None
    
    def update_document(self, collection: str, document_id: str, data: dict) -> bool:
        """Update a document in Firestore"""
        if not self._initialized or not self.db:
            print(f"⚠️  MOCK MODE: Would update document {document_id} in {collection}")
            print(f"   (No data actually updated - Firebase not initialized)")
            return True
        try:
            self.db.collection(collection).document(document_id).update(data)
            print(f"✓ Updated document {document_id} in {collection}")
            return True
        except Exception as e:
            print(f"❌ Error updating document: {str(e)}")
            return False
    
    def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from Firestore"""
        if not self._initialized or not self.db:
            print(f"⚠️  MOCK MODE: Would delete document {document_id} from {collection}")
            return True
        try:
            self.db.collection(collection).document(document_id).delete()
            return True
        except Exception as e:
            print(f"❌ Error deleting document: {str(e)}")
            return False
    
    def get_all_documents(self, collection: str, filters: Optional[List[tuple]] = None) -> List[dict]:
        """Get all documents from a collection with optional filters"""
        if not self._initialized or not self.db:
            print(f"⚠️  MOCK MODE: Would get all documents from {collection}")
            return []
        try:
            query = self.db.collection(collection)
            
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"❌ Error getting documents: {str(e)}")
            return []
    
    def get_passenger(self, user_id: str) -> Optional[dict]:
        """Get passenger by user_id"""
        return self.get_document(Config.COLLECTION_PASSENGERS, user_id)
    
    def create_passenger(self, user_id: str, data: dict) -> bool:
        """Create passenger document"""
        return self.create_document(Config.COLLECTION_PASSENGERS, user_id, data)
    
    def update_passenger(self, user_id: str, data: dict) -> bool:
        """Update passenger document"""
        return self.update_document(Config.COLLECTION_PASSENGERS, user_id, data)
    
    def get_driver(self, driver_id: str) -> Optional[dict]:
        """Get driver by driver_id"""
        return self.get_document(Config.COLLECTION_DRIVERS, driver_id)
    
    def create_driver(self, driver_id: str, data: dict) -> bool:
        """Create driver document"""
        return self.create_document(Config.COLLECTION_DRIVERS, driver_id, data)
    
    def update_driver(self, driver_id: str, data: dict) -> bool:
        """Update driver document"""
        return self.update_document(Config.COLLECTION_DRIVERS, driver_id, data)
    
    def get_available_drivers(self) -> List[dict]:
        """Get all available drivers"""
        return self.get_all_documents(
            Config.COLLECTION_DRIVERS,
            filters=[("is_available", "==", True), ("is_online", "==", True)]
        )
    
    def create_booking(self, booking_id: str, data: dict) -> bool:
        """Create booking document"""
        return self.create_document(Config.COLLECTION_BOOKINGS, booking_id, data)
    
    def get_booking(self, booking_id: str) -> Optional[dict]:
        """Get booking by booking_id"""
        return self.get_document(Config.COLLECTION_BOOKINGS, booking_id)
    
    def update_booking(self, booking_id: str, data: dict) -> bool:
        """Update booking document"""
        return self.update_document(Config.COLLECTION_BOOKINGS, booking_id, data)
    
    def update_driver_location(self, driver_id: str, location_data: dict) -> bool:
        """Update driver location in locations collection"""
        location_data["driver_id"] = driver_id
        return self.create_document(Config.COLLECTION_LOCATIONS, driver_id, location_data)
    
    def get_driver_location(self, driver_id: str) -> Optional[dict]:
        """Get driver location from locations collection"""
        return self.get_document(Config.COLLECTION_LOCATIONS, driver_id)
    
    def get_passenger_location(self, user_id: str) -> Optional[dict]:
        """Get passenger location from locations collection"""
        return self.get_document(Config.COLLECTION_LOCATIONS, user_id)
    
    def test_connection(self) -> dict:
        """
        Test Firebase connection by attempting a simple operation
        Returns status information
        """
        status = {
            "initialized": self._initialized,
            "connected": False,
            "error": self._error_message,
            "credentials_path": Config.FIREBASE_CREDENTIALS_PATH
        }
        
        if self._initialized and self.db:
            try:
                # Try to access a collection (this will fail if not connected)
                test_collection = self.db.collection("_health_check")
                # Just check if we can access it, don't actually query
                status["connected"] = True
                status["message"] = "Firebase connection is active"
            except Exception as e:
                status["connected"] = False
                status["error"] = str(e)
                status["message"] = "Firebase initialized but connection test failed"
        else:
            status["message"] = "Firebase not initialized - running in mock mode"
        
        return status
