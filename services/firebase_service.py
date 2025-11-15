import firebase_admin
from firebase_admin import credentials, firestore
from typing import Optional, List, Dict
from config import Config
import json

class FirebaseService:
    """Service class for Firebase Firestore operations"""
    
    def __init__(self):
        """Initialize Firebase Admin SDK"""
        self.db = None
        self._initialized = False
        
        if not firebase_admin._apps:
            try:
                import os
                if os.path.exists(Config.FIREBASE_CREDENTIALS_PATH):
                    cred = credentials.Certificate(Config.FIREBASE_CREDENTIALS_PATH)
                    firebase_admin.initialize_app(cred)
                    self.db = firestore.client()
                    self._initialized = True
                else:
                    print(f"Warning: Firebase credentials file not found at {Config.FIREBASE_CREDENTIALS_PATH}")
                    print("Running in mock mode. Please configure Firebase credentials for full functionality.")
            except Exception as e:
                print(f"Warning: Failed to initialize Firebase: {str(e)}")
                print("Running in mock mode. Please configure Firebase credentials for full functionality.")
        else:
            try:
                self.db = firestore.client()
                self._initialized = True
            except Exception as e:
                print(f"Warning: Failed to get Firestore client: {str(e)}")
                print("Running in mock mode. Please configure Firebase credentials for full functionality.")
    
    def create_document(self, collection: str, document_id: str, data: dict) -> bool:
        """Create a document in Firestore"""
        if not self._initialized or not self.db:
            print(f"Mock: Would create document {document_id} in {collection}")
            return True
        try:
            self.db.collection(collection).document(document_id).set(data)
            return True
        except Exception as e:
            print(f"Error creating document: {str(e)}")
            return False
    
    def get_document(self, collection: str, document_id: str) -> Optional[dict]:
        """Get a document from Firestore"""
        if not self._initialized or not self.db:
            print(f"Mock: Would get document {document_id} from {collection}")
            return None
        try:
            doc = self.db.collection(collection).document(document_id).get()
            if doc.exists:
                return doc.to_dict()
            return None
        except Exception as e:
            print(f"Error getting document: {str(e)}")
            return None
    
    def update_document(self, collection: str, document_id: str, data: dict) -> bool:
        """Update a document in Firestore"""
        if not self._initialized or not self.db:
            print(f"Mock: Would update document {document_id} in {collection}")
            return True
        try:
            self.db.collection(collection).document(document_id).update(data)
            return True
        except Exception as e:
            print(f"Error updating document: {str(e)}")
            return False
    
    def delete_document(self, collection: str, document_id: str) -> bool:
        """Delete a document from Firestore"""
        if not self._initialized or not self.db:
            print(f"Mock: Would delete document {document_id} from {collection}")
            return True
        try:
            self.db.collection(collection).document(document_id).delete()
            return True
        except Exception as e:
            print(f"Error deleting document: {str(e)}")
            return False
    
    def get_all_documents(self, collection: str, filters: Optional[List[tuple]] = None) -> List[dict]:
        """Get all documents from a collection with optional filters"""
        if not self._initialized or not self.db:
            print(f"Mock: Would get all documents from {collection}")
            return []
        try:
            query = self.db.collection(collection)
            
            if filters:
                for field, operator, value in filters:
                    query = query.where(field, operator, value)
            
            docs = query.stream()
            return [doc.to_dict() for doc in docs]
        except Exception as e:
            print(f"Error getting documents: {str(e)}")
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

