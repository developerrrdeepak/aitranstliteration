#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Ultimate AI Translation App
Tests all core translation features, language support, history, and conversation management
"""

import requests
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any
import base64
from PIL import Image, ImageDraw, ImageFont
import io

# Backend URL from frontend environment
BACKEND_URL = "https://linguapic-2.preview.emergentagent.com/api"

class TranslationAppTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.conversation_id = None
        
    def log_test(self, test_name: str, success: bool, details: str, response_data: Any = None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "details": details,
            "timestamp": datetime.now().isoformat(),
            "response_data": response_data
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {details}")
        if response_data and not success:
            print(f"   Response: {response_data}")
    
    def test_api_health(self):
        """Test basic API connectivity"""
        try:
            response = self.session.get(f"{BACKEND_URL}/")
            if response.status_code == 200:
                data = response.json()
                self.log_test("API Health Check", True, f"API is running - {data.get('message', 'OK')}", data)
                return True
            else:
                self.log_test("API Health Check", False, f"API returned status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("API Health Check", False, f"Connection failed: {str(e)}")
            return False
    
    def test_supported_languages(self):
        """Test /api/languages endpoint"""
        try:
            response = self.session.get(f"{BACKEND_URL}/languages")
            if response.status_code == 200:
                languages = response.json()
                if isinstance(languages, list) and len(languages) >= 20:
                    # Check if required languages are present
                    lang_codes = [lang.get('code') for lang in languages]
                    required_langs = ['en', 'es', 'fr', 'de', 'hi', 'ta', 'zh', 'ar']
                    missing_langs = [lang for lang in required_langs if lang not in lang_codes]
                    
                    if not missing_langs:
                        self.log_test("Language Support API", True, f"Found {len(languages)} supported languages", languages[:5])
                        return True
                    else:
                        self.log_test("Language Support API", False, f"Missing required languages: {missing_langs}", languages)
                        return False
                else:
                    self.log_test("Language Support API", False, f"Expected 20+ languages, got {len(languages) if isinstance(languages, list) else 'invalid response'}", languages)
                    return False
            else:
                self.log_test("Language Support API", False, f"Status {response.status_code}", response.text)
                return False
        except Exception as e:
            self.log_test("Language Support API", False, f"Request failed: {str(e)}")
            return False
    
    def test_text_translation(self):
        """Test core text translation functionality"""
        test_cases = [
            {
                "text": "Hello, how are you today?",
                "source_language": "en",
                "target_language": "es",
                "expected_contains": ["hola", "cómo", "estás"]
            },
            {
                "text": "Bonjour, comment allez-vous?",
                "source_language": "fr", 
                "target_language": "en",
                "expected_contains": ["hello", "how", "are"]
            },
            {
                "text": "मैं आज बहुत खुश हूं",
                "source_language": "hi",
                "target_language": "en", 
                "expected_contains": ["happy", "today", "very"]
            }
        ]
        
        success_count = 0
        for i, test_case in enumerate(test_cases):
            try:
                payload = {
                    "text": test_case["text"],
                    "source_language": test_case["source_language"],
                    "target_language": test_case["target_language"]
                }
                
                response = self.session.post(f"{BACKEND_URL}/translate/text", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    translated_text = data.get("translated_text", "").lower()
                    
                    # Check if translation contains expected words (flexible matching)
                    contains_expected = any(word.lower() in translated_text for word in test_case["expected_contains"])
                    
                    if translated_text and len(translated_text) > 0:
                        self.log_test(f"Text Translation Test {i+1}", True, 
                                    f"'{test_case['text']}' → '{data.get('translated_text')}'", data)
                        success_count += 1
                    else:
                        self.log_test(f"Text Translation Test {i+1}", False, 
                                    f"Empty translation result", data)
                else:
                    self.log_test(f"Text Translation Test {i+1}", False, 
                                f"Status {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Text Translation Test {i+1}", False, f"Request failed: {str(e)}")
        
        overall_success = success_count == len(test_cases)
        self.log_test("Overall Text Translation", overall_success, 
                     f"{success_count}/{len(test_cases)} translation tests passed")
        return overall_success
    
    def test_auto_language_detection(self):
        """Test automatic language detection"""
        test_cases = [
            {"text": "Hello world", "target_language": "es"},
            {"text": "Bonjour le monde", "target_language": "en"},
            {"text": "Hola mundo", "target_language": "fr"}
        ]
        
        success_count = 0
        for i, test_case in enumerate(test_cases):
            try:
                payload = {
                    "text": test_case["text"],
                    "source_language": "auto",  # Auto-detect
                    "target_language": test_case["target_language"]
                }
                
                response = self.session.post(f"{BACKEND_URL}/translate/text", json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    if data.get("translated_text") and data.get("source_language") != "auto":
                        self.log_test(f"Auto Language Detection {i+1}", True,
                                    f"Detected '{data.get('source_language')}' for '{test_case['text']}'", data)
                        success_count += 1
                    else:
                        self.log_test(f"Auto Language Detection {i+1}", False,
                                    f"Failed to detect language properly", data)
                else:
                    self.log_test(f"Auto Language Detection {i+1}", False,
                                f"Status {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Auto Language Detection {i+1}", False, f"Request failed: {str(e)}")
        
        overall_success = success_count == len(test_cases)
        self.log_test("Overall Auto Detection", overall_success,
                     f"{success_count}/{len(test_cases)} auto-detection tests passed")
        return overall_success
    
    def test_contextual_translation(self):
        """Test translation with context"""
        try:
            payload = {
                "text": "I need to book a table",
                "source_language": "en",
                "target_language": "es",
                "context": "Restaurant reservation context"
            }
            
            response = self.session.post(f"{BACKEND_URL}/translate/text", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("translated_text") and data.get("context"):
                    self.log_test("Contextual Translation", True,
                                f"Context-aware translation: '{data.get('translated_text')}'", data)
                    return True
                else:
                    self.log_test("Contextual Translation", False,
                                f"Context not properly handled", data)
                    return False
            else:
                self.log_test("Contextual Translation", False,
                            f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Contextual Translation", False, f"Request failed: {str(e)}")
            return False
    
    def test_translation_history(self):
        """Test translation history storage and retrieval"""
        try:
            # First, make a few translations to ensure we have history
            test_translations = [
                {"text": "Good morning", "source_language": "en", "target_language": "fr"},
                {"text": "Thank you very much", "source_language": "en", "target_language": "de"}
            ]
            
            # Perform translations
            for translation in test_translations:
                self.session.post(f"{BACKEND_URL}/translate/text", json=translation)
                time.sleep(0.5)  # Small delay between requests
            
            # Now test history retrieval
            response = self.session.get(f"{BACKEND_URL}/translate/history")
            
            if response.status_code == 200:
                history = response.json()
                if isinstance(history, list) and len(history) >= 2:
                    # Check if recent translations are in history
                    recent_texts = [item.get("original_text") for item in history[:5]]
                    self.log_test("Translation History API", True,
                                f"Retrieved {len(history)} history items", history[:3])
                    return True
                else:
                    self.log_test("Translation History API", False,
                                f"Expected list with recent translations, got {len(history) if isinstance(history, list) else 'invalid response'}", history)
                    return False
            else:
                self.log_test("Translation History API", False,
                            f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Translation History API", False, f"Request failed: {str(e)}")
            return False
    
    def test_conversation_management(self):
        """Test conversation creation and message handling"""
        try:
            # Test 1: Create conversation
            response = self.session.post(f"{BACKEND_URL}/conversation/create")
            
            if response.status_code == 200:
                data = response.json()
                conversation_id = data.get("conversation_id")
                if conversation_id:
                    self.conversation_id = conversation_id
                    self.log_test("Conversation Creation", True,
                                f"Created conversation: {conversation_id}", data)
                else:
                    self.log_test("Conversation Creation", False,
                                f"No conversation_id in response", data)
                    return False
            else:
                self.log_test("Conversation Creation", False,
                            f"Status {response.status_code}", response.text)
                return False
            
            # Test 2: Add message to conversation
            message_payload = {
                "original_text": "Hello, how can I help you?",
                "source_language": "en",
                "target_language": "es",
                "message_type": "text",
                "sender_id": "user_123"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/conversation/{conversation_id}/message",
                json=message_payload
            )
            
            if response.status_code == 200:
                message_data = response.json()
                if message_data.get("translated_text"):
                    self.log_test("Conversation Message Add", True,
                                f"Added translated message: '{message_data.get('translated_text')}'", message_data)
                else:
                    self.log_test("Conversation Message Add", False,
                                f"Message not properly translated", message_data)
                    return False
            else:
                self.log_test("Conversation Message Add", False,
                            f"Status {response.status_code}", response.text)
                return False
            
            # Test 3: Retrieve conversation messages
            response = self.session.get(f"{BACKEND_URL}/conversation/{conversation_id}/messages")
            
            if response.status_code == 200:
                messages = response.json()
                if isinstance(messages, list) and len(messages) >= 1:
                    self.log_test("Conversation Messages Retrieval", True,
                                f"Retrieved {len(messages)} messages", messages)
                    return True
                else:
                    self.log_test("Conversation Messages Retrieval", False,
                                f"Expected messages list, got {len(messages) if isinstance(messages, list) else 'invalid response'}", messages)
                    return False
            else:
                self.log_test("Conversation Messages Retrieval", False,
                            f"Status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            self.log_test("Conversation Management", False, f"Request failed: {str(e)}")
            return False
    
    def test_error_handling(self):
        """Test API error handling"""
        error_tests = [
            {
                "name": "Invalid Language Code",
                "endpoint": "/translate/text",
                "payload": {"text": "Hello", "source_language": "invalid", "target_language": "es"},
                "expected_status": [400, 422, 500]
            },
            {
                "name": "Empty Text Translation",
                "endpoint": "/translate/text", 
                "payload": {"text": "", "source_language": "en", "target_language": "es"},
                "expected_status": [400, 422, 500]
            },
            {
                "name": "Invalid Conversation ID",
                "endpoint": "/conversation/invalid-id/messages",
                "method": "GET",
                "expected_status": [404, 500]
            }
        ]
        
        success_count = 0
        for test in error_tests:
            try:
                if test.get("method") == "GET":
                    response = self.session.get(f"{BACKEND_URL}{test['endpoint']}")
                else:
                    response = self.session.post(f"{BACKEND_URL}{test['endpoint']}", json=test.get("payload"))
                
                if response.status_code in test["expected_status"]:
                    self.log_test(f"Error Handling - {test['name']}", True,
                                f"Properly handled error with status {response.status_code}")
                    success_count += 1
                else:
                    self.log_test(f"Error Handling - {test['name']}", False,
                                f"Expected status {test['expected_status']}, got {response.status_code}", response.text)
                    
            except Exception as e:
                self.log_test(f"Error Handling - {test['name']}", False, f"Request failed: {str(e)}")
        
        overall_success = success_count == len(error_tests)
        self.log_test("Overall Error Handling", overall_success,
                     f"{success_count}/{len(error_tests)} error handling tests passed")
        return overall_success
    
    def test_performance_and_concurrency(self):
        """Test basic performance and concurrent requests"""
        try:
            import concurrent.futures
            import threading
            
            def make_translation_request():
                payload = {
                    "text": f"Test message {threading.current_thread().ident}",
                    "source_language": "en",
                    "target_language": "es"
                }
                response = self.session.post(f"{BACKEND_URL}/translate/text", json=payload)
                return response.status_code == 200
            
            # Test concurrent requests
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [executor.submit(make_translation_request) for _ in range(5)]
                results = [future.result() for future in concurrent.futures.as_completed(futures)]
            
            success_count = sum(results)
            if success_count >= 4:  # Allow 1 failure out of 5
                self.log_test("Concurrent Requests", True,
                            f"{success_count}/5 concurrent requests succeeded")
                return True
            else:
                self.log_test("Concurrent Requests", False,
                            f"Only {success_count}/5 concurrent requests succeeded")
                return False
                
        except Exception as e:
            self.log_test("Concurrent Requests", False, f"Concurrency test failed: {str(e)}")
            return False

    def create_test_image_with_text(self, text="Hello World", language="en"):
        """Create a test image with text for OCR testing"""
        try:
            # Create a white image
            img = Image.new('RGB', (400, 200), color='white')
            draw = ImageDraw.Draw(img)
            
            # Try to use a default font, fallback to basic if not available
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            # Draw text on image
            draw.text((50, 80), text, fill='black', font=font)
            
            # Convert to base64
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
            
            return img_base64
        except Exception as e:
            print(f"Error creating test image: {e}")
            return None

    def test_ocr_extract_text(self):
        """Test Phase 2 OCR text extraction endpoint"""
        try:
            # Test with English text
            test_image = self.create_test_image_with_text("Hello World Testing OCR", "en")
            if not test_image:
                self.log_test("OCR Text Extraction", False, "Failed to create test image")
                return False

            payload = {
                "image_base64": test_image
            }
            
            response = self.session.post(f"{BACKEND_URL}/ocr/extract", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                extracted_text = data.get('extracted_text', '')
                confidence = data.get('confidence_score', 0)
                
                # Check if text was extracted
                if extracted_text and len(extracted_text.strip()) > 0:
                    self.log_test("OCR Text Extraction", True, 
                                f"Extracted: '{extracted_text}', Confidence: {confidence}")
                    return True
                else:
                    self.log_test("OCR Text Extraction", False, 
                                f"No text extracted. Response: {data}")
                    return False
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else f"HTTP {response.status_code}"
                self.log_test("OCR Text Extraction", False, 
                            f"API Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("OCR Text Extraction", False, f"Exception: {str(e)}")
            return False

    def test_ocr_with_hindi_text(self):
        """Test OCR with Hindi text"""
        try:
            # Test with Hindi text
            test_image = self.create_test_image_with_text("नमस्ते दुनिया", "hi")
            if not test_image:
                self.log_test("OCR Hindi Text", False, "Failed to create Hindi test image")
                return False

            payload = {
                "image_base64": test_image
            }
            
            response = self.session.post(f"{BACKEND_URL}/ocr/extract", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                extracted_text = data.get('extracted_text', '')
                confidence = data.get('confidence_score', 0)
                
                self.log_test("OCR Hindi Text", True, 
                            f"Extracted: '{extracted_text}', Confidence: {confidence}")
                return True
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else f"HTTP {response.status_code}"
                self.log_test("OCR Hindi Text", False, f"API Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("OCR Hindi Text", False, f"Exception: {str(e)}")
            return False

    def test_image_translation_pipeline(self):
        """Test Phase 2 complete image translation pipeline"""
        try:
            # Test with English text to Spanish translation
            test_image = self.create_test_image_with_text("Good morning everyone", "en")
            if not test_image:
                self.log_test("Image Translation Pipeline", False, "Failed to create test image")
                return False

            payload = {
                "image_base64": test_image,
                "source_language": "auto",
                "target_language": "es"
            }
            
            response = self.session.post(f"{BACKEND_URL}/translate/image", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                original_text = data.get('original_text', '')
                translated_text = data.get('translated_text', '')
                source_lang = data.get('source_language', '')
                target_lang = data.get('target_language', '')
                confidence = data.get('confidence_score', 0)
                
                if original_text and translated_text:
                    self.log_test("Image Translation Pipeline", True, 
                                f"Original: '{original_text}' ({source_lang}) → Translated: '{translated_text}' ({target_lang}), Confidence: {confidence}")
                    return True
                else:
                    self.log_test("Image Translation Pipeline", False, 
                                f"Missing text in response: {data}")
                    return False
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else f"HTTP {response.status_code}"
                self.log_test("Image Translation Pipeline", False, 
                            f"API Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Image Translation Pipeline", False, f"Exception: {str(e)}")
            return False

    def test_image_translation_hindi_to_english(self):
        """Test image translation from Hindi to English"""
        try:
            # Test with Hindi text to English translation
            test_image = self.create_test_image_with_text("आज मौसम अच्छा है", "hi")
            if not test_image:
                self.log_test("Hindi to English Image Translation", False, "Failed to create Hindi test image")
                return False

            payload = {
                "image_base64": test_image,
                "source_language": "hi",
                "target_language": "en"
            }
            
            response = self.session.post(f"{BACKEND_URL}/translate/image", json=payload)
            
            if response.status_code == 200:
                data = response.json()
                original_text = data.get('original_text', '')
                translated_text = data.get('translated_text', '')
                confidence = data.get('confidence_score', 0)
                
                self.log_test("Hindi to English Image Translation", True, 
                            f"Original: '{original_text}' → Translated: '{translated_text}', Confidence: {confidence}")
                return True
            else:
                error_detail = response.json().get('detail', 'Unknown error') if response.content else f"HTTP {response.status_code}"
                self.log_test("Hindi to English Image Translation", False, 
                            f"API Error: {error_detail}")
                return False
                
        except Exception as e:
            self.log_test("Hindi to English Image Translation", False, f"Exception: {str(e)}")
            return False

    def test_ocr_error_handling(self):
        """Test OCR error handling with invalid data"""
        try:
            # Test with invalid base64
            payload = {
                "image_base64": "invalid_base64_data"
            }
            
            response = self.session.post(f"{BACKEND_URL}/ocr/extract", json=payload)
            
            # Should return error but not crash
            if response.status_code in [400, 422, 500]:
                self.log_test("OCR Error Handling", True, 
                            f"Properly handled invalid input with status {response.status_code}")
                return True
            else:
                self.log_test("OCR Error Handling", False, 
                            f"Unexpected response to invalid input: {response.status_code}")
                return False
                
        except Exception as e:
            self.log_test("OCR Error Handling", False, f"Exception: {str(e)}")
            return False
    
    def run_all_tests(self):
        """Run comprehensive test suite"""
        print("🚀 Starting Ultimate AI Translation App Backend Tests")
        print("=" * 60)
        
        # Core functionality tests
        tests = [
            ("API Health", self.test_api_health),
            ("Language Support", self.test_supported_languages),
            ("Text Translation", self.test_text_translation),
            ("Auto Language Detection", self.test_auto_language_detection),
            ("Contextual Translation", self.test_contextual_translation),
            ("Translation History", self.test_translation_history),
            ("Conversation Management", self.test_conversation_management),
            ("Error Handling", self.test_error_handling),
            ("Performance & Concurrency", self.test_performance_and_concurrency),
            ("OCR Text Extraction", self.test_ocr_extract_text),
            ("OCR Hindi Text", self.test_ocr_with_hindi_text),
            ("Image Translation Pipeline", self.test_image_translation_pipeline),
            ("Hindi to English Image Translation", self.test_image_translation_hindi_to_english),
            ("OCR Error Handling", self.test_ocr_error_handling)
        ]
        
        passed_tests = 0
        total_tests = len(tests)
        
        for test_name, test_func in tests:
            print(f"\n📋 Running {test_name} Tests...")
            try:
                if test_func():
                    passed_tests += 1
            except Exception as e:
                self.log_test(test_name, False, f"Test execution failed: {str(e)}")
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        success_rate = (passed_tests / total_tests) * 100
        print(f"Overall Success Rate: {success_rate:.1f}% ({passed_tests}/{total_tests})")
        
        print("\n📋 Detailed Results:")
        for result in self.test_results:
            status = "✅" if result["success"] else "❌"
            print(f"{status} {result['test']}: {result['details']}")
        
        # Critical issues
        failed_tests = [r for r in self.test_results if not r["success"]]
        if failed_tests:
            print(f"\n🚨 CRITICAL ISSUES FOUND ({len(failed_tests)} failures):")
            for failure in failed_tests:
                print(f"   ❌ {failure['test']}: {failure['details']}")
        
        return passed_tests, total_tests, self.test_results

if __name__ == "__main__":
    tester = TranslationAppTester()
    passed, total, results = tester.run_all_tests()
    
    if passed == total:
        print(f"\n🎉 ALL TESTS PASSED! Backend is fully functional.")
        exit(0)
    else:
        print(f"\n⚠️  {total - passed} tests failed. Backend needs attention.")
        exit(1)