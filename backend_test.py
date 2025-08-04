#!/usr/bin/env python3
"""
Backend API Testing for Arabic Note-Taking App
Tests all CRUD operations, voice recording storage, statistics, and reminder system
"""

import requests
import json
import base64
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv('/app/frontend/.env')
BACKEND_URL = os.getenv('REACT_APP_BACKEND_URL', 'http://localhost:8001')
API_BASE = f"{BACKEND_URL}/api"

print(f"Testing backend at: {API_BASE}")

class BackendTester:
    def __init__(self):
        self.created_note_ids = []
        self.test_results = {
            'crud_operations': False,
            'voice_storage': False,
            'statistics': False,
            'reminders': False,
            'errors': []
        }

    def log_error(self, test_name, error):
        error_msg = f"{test_name}: {str(error)}"
        self.test_results['errors'].append(error_msg)
        print(f"❌ {error_msg}")

    def log_success(self, test_name):
        print(f"✅ {test_name}")

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        try:
            response = requests.get(f"{API_BASE}/")
            if response.status_code == 200:
                data = response.json()
                if "ذكّرني بالمهم" in data.get('message', ''):
                    self.log_success("Root endpoint - Arabic message returned")
                    return True
                else:
                    self.log_error("Root endpoint", "Arabic message not found in response")
            else:
                self.log_error("Root endpoint", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Root endpoint", e)
        return False

    def test_create_text_note(self):
        """Test creating a text note with Arabic content"""
        try:
            note_data = {
                "title": "مهمة مهمة",
                "content": "يجب أن أتذكر شراء الخضروات من السوق اليوم",
                "note_type": "text",
                "category": "shopping",
                "reminder_time": (datetime.utcnow() + timedelta(hours=2)).isoformat()
            }
            
            response = requests.post(f"{API_BASE}/notes", json=note_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('id') and data.get('title') == note_data['title']:
                    self.created_note_ids.append(data['id'])
                    self.log_success("Create Arabic text note")
                    return data
                else:
                    self.log_error("Create text note", "Invalid response structure")
            else:
                self.log_error("Create text note", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("Create text note", e)
        return None

    def test_create_audio_note(self):
        """Test creating an audio note with base64 data"""
        try:
            # Create a simple base64 encoded audio data (simulated)
            sample_audio = "data:audio/wav;base64,UklGRnoGAABXQVZFZm10IBAAAAABAAEAQB8AAEAfAAABAAgAZGF0YQoGAACBhYqFbF1fdJivrJBhNjVgodDbq2EcBj+a2/LDciUFLIHO8tiJNwgZaLvt559NEAxQp+PwtmMcBjiR1/LMeSwFJHfH8N2QQAoUXrTp66hVFApGn+DyvmwhBSuBzvLZiTYIG2m98OScTgwOUarm7blmGgU7k9n1unEiBC13yO/eizEIHWq+8+OWT"
            
            note_data = {
                "title": "Voice Reminder",
                "audio_data": sample_audio,
                "audio_duration": 15,
                "note_type": "audio",
                "category": "personal",
                "reminder_time": (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
            response = requests.post(f"{API_BASE}/notes", json=note_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('id') and data.get('audio_data') and data.get('note_type') == 'audio':
                    self.created_note_ids.append(data['id'])
                    self.log_success("Create audio note with base64 data")
                    return data
                else:
                    self.log_error("Create audio note", "Invalid response structure")
            else:
                self.log_error("Create audio note", f"Status code: {response.status_code}, Response: {response.text}")
        except Exception as e:
            self.log_error("Create audio note", e)
        return None

    def test_get_all_notes(self):
        """Test getting all notes"""
        try:
            response = requests.get(f"{API_BASE}/notes")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_success(f"Get all notes - Found {len(data)} notes")
                    return data
                else:
                    self.log_error("Get all notes", "Response is not a list")
            else:
                self.log_error("Get all notes", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Get all notes", e)
        return None

    def test_get_notes_by_category(self):
        """Test getting notes filtered by category"""
        try:
            response = requests.get(f"{API_BASE}/notes?category=shopping")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    shopping_notes = [note for note in data if note.get('category') == 'shopping']
                    if len(shopping_notes) == len(data):
                        self.log_success("Get notes by category filter")
                        return True
                    else:
                        self.log_error("Category filter", "Some notes don't match category filter")
                else:
                    self.log_error("Get notes by category", "Response is not a list")
            else:
                self.log_error("Get notes by category", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Get notes by category", e)
        return False

    def test_get_specific_note(self, note_id):
        """Test getting a specific note by ID"""
        try:
            response = requests.get(f"{API_BASE}/notes/{note_id}")
            if response.status_code == 200:
                data = response.json()
                if data.get('id') == note_id:
                    self.log_success("Get specific note by ID")
                    return data
                else:
                    self.log_error("Get specific note", "Note ID mismatch")
            else:
                self.log_error("Get specific note", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Get specific note", e)
        return None

    def test_update_note(self, note_id):
        """Test updating a note"""
        try:
            update_data = {
                "title": "مهمة محدثة",
                "is_completed": True
            }
            
            response = requests.put(f"{API_BASE}/notes/{note_id}", json=update_data)
            if response.status_code == 200:
                data = response.json()
                if data.get('title') == update_data['title'] and data.get('is_completed') == True:
                    self.log_success("Update note")
                    return data
                else:
                    self.log_error("Update note", "Update data not reflected in response")
            else:
                self.log_error("Update note", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Update note", e)
        return None

    def test_upcoming_reminders(self):
        """Test getting upcoming reminders"""
        try:
            response = requests.get(f"{API_BASE}/notes/reminders/upcoming")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list):
                    self.log_success(f"Get upcoming reminders - Found {len(data)} reminders")
                    return data
                else:
                    self.log_error("Upcoming reminders", "Response is not a list")
            else:
                self.log_error("Upcoming reminders", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Upcoming reminders", e)
        return None

    def test_statistics(self):
        """Test getting statistics"""
        try:
            response = requests.get(f"{API_BASE}/stats")
            if response.status_code == 200:
                data = response.json()
                required_fields = ['total_notes', 'text_notes', 'audio_notes', 'completed_notes', 'pending_reminders']
                if all(field in data for field in required_fields):
                    self.log_success("Get statistics - All required fields present")
                    print(f"   Stats: {data}")
                    return data
                else:
                    missing_fields = [field for field in required_fields if field not in data]
                    self.log_error("Statistics", f"Missing fields: {missing_fields}")
            else:
                self.log_error("Statistics", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Statistics", e)
        return None

    def test_delete_note(self, note_id):
        """Test deleting a note"""
        try:
            response = requests.delete(f"{API_BASE}/notes/{note_id}")
            if response.status_code == 200:
                data = response.json()
                if "deleted successfully" in data.get('message', ''):
                    self.log_success("Delete note")
                    return True
                else:
                    self.log_error("Delete note", "Unexpected response message")
            else:
                self.log_error("Delete note", f"Status code: {response.status_code}")
        except Exception as e:
            self.log_error("Delete note", e)
        return False

    def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Arabic Note-Taking App")
        print("=" * 60)
        
        # Test root endpoint
        if not self.test_root_endpoint():
            print("❌ Root endpoint failed - stopping tests")
            return self.test_results
        
        # Test CRUD operations
        print("\n📝 Testing Note CRUD Operations...")
        
        # Create notes
        text_note = self.test_create_text_note()
        audio_note = self.test_create_audio_note()
        
        if text_note and audio_note:
            # Test reading operations
            self.test_get_all_notes()
            self.test_get_notes_by_category()
            self.test_get_specific_note(text_note['id'])
            
            # Test update
            self.test_update_note(text_note['id'])
            
            # Mark CRUD as successful if we got this far
            self.test_results['crud_operations'] = True
            self.test_results['voice_storage'] = True
        
        # Test reminder system
        print("\n⏰ Testing Reminder System...")
        reminders = self.test_upcoming_reminders()
        if reminders is not None:
            self.test_results['reminders'] = True
        
        # Test statistics
        print("\n📊 Testing Statistics...")
        stats = self.test_statistics()
        if stats is not None:
            self.test_results['statistics'] = True
        
        # Clean up - delete created notes
        print("\n🧹 Cleaning up test data...")
        for note_id in self.created_note_ids:
            self.test_delete_note(note_id)
        
        return self.test_results

    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 60)
        print("📋 TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results) - 1  # Exclude 'errors' key
        passed_tests = sum(1 for k, v in self.test_results.items() if k != 'errors' and v)
        
        print(f"✅ CRUD Operations: {'PASS' if self.test_results['crud_operations'] else 'FAIL'}")
        print(f"🎤 Voice Storage: {'PASS' if self.test_results['voice_storage'] else 'FAIL'}")
        print(f"📊 Statistics: {'PASS' if self.test_results['statistics'] else 'FAIL'}")
        print(f"⏰ Reminders: {'PASS' if self.test_results['reminders'] else 'FAIL'}")
        
        print(f"\n🎯 Overall: {passed_tests}/{total_tests} tests passed")
        
        if self.test_results['errors']:
            print(f"\n❌ Errors encountered ({len(self.test_results['errors'])}):")
            for error in self.test_results['errors']:
                print(f"   • {error}")
        else:
            print("\n🎉 No errors encountered!")

if __name__ == "__main__":
    tester = BackendTester()
    results = tester.run_all_tests()
    tester.print_summary()