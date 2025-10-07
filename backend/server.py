from fastapi import FastAPI, APIRouter, HTTPException, UploadFile, File, Form
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional
import uuid
from datetime import datetime
import base64
from emergentintegrations.llm.chat import LlmChat, UserMessage
import easyocr
import cv2
import numpy as np
from PIL import Image
import io
import asyncio
import threading

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI()

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Initialize LLM Chat for translations
emergent_llm_key = os.environ.get('EMERGENT_LLM_KEY')

# Models for Translation App
class TranslationRequest(BaseModel):
    text: str
    source_language: Optional[str] = "auto"
    target_language: str
    context: Optional[str] = None

class TranslationResponse(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    original_text: str
    translated_text: str
    source_language: str
    target_language: str
    context: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    confidence_score: Optional[float] = None

class ConversationMessage(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    conversation_id: str
    original_text: str
    translated_text: Optional[str] = None
    source_language: str
    target_language: Optional[str] = None
    message_type: str  # "text", "voice", "image"
    sender_id: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    is_translated: bool = False

class ConversationMessageRequest(BaseModel):
    original_text: str
    source_language: str
    target_language: Optional[str] = None
    message_type: str  # "text", "voice", "image"
    sender_id: str

class VoiceTranslationRequest(BaseModel):
    audio_base64: str
    source_language: Optional[str] = "auto"
    target_language: str

class ImageTranslationRequest(BaseModel):
    image_base64: str
    source_language: Optional[str] = "auto"
    target_language: str
    extract_text_only: bool = False

class Language(BaseModel):
    code: str
    name: str
    native_name: str

# Supported languages
SUPPORTED_LANGUAGES = [
    {"code": "en", "name": "English", "native_name": "English"},
    {"code": "es", "name": "Spanish", "native_name": "Español"},
    {"code": "fr", "name": "French", "native_name": "Français"},
    {"code": "de", "name": "German", "native_name": "Deutsch"},
    {"code": "it", "name": "Italian", "native_name": "Italiano"},
    {"code": "pt", "name": "Portuguese", "native_name": "Português"},
    {"code": "ru", "name": "Russian", "native_name": "Русский"},
    {"code": "ja", "name": "Japanese", "native_name": "日本語"},
    {"code": "ko", "name": "Korean", "native_name": "한국어"},
    {"code": "zh", "name": "Chinese", "native_name": "中文"},
    {"code": "ar", "name": "Arabic", "native_name": "العربية"},
    {"code": "hi", "name": "Hindi", "native_name": "हिंदी"},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা"},
    {"code": "ur", "name": "Urdu", "native_name": "اردو"},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்"},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు"},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം"},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ"},
    {"code": "gu", "name": "Gujarati", "native_name": "ગુજરાતી"},
    {"code": "pa", "name": "Punjabi", "native_name": "ਪੰਜਾਬੀ"}
]

async def create_llm_chat(session_id: str = "default"):
    """Create LLM chat instance for translation"""
    return LlmChat(
        api_key=emergent_llm_key,
        session_id=session_id,
        system_message="You are an expert translator and linguist. Provide accurate, contextual translations while preserving meaning, tone, and cultural nuances. Always respond with just the translated text unless specifically asked for explanations."
    ).with_model("openai", "gpt-4o")

async def detect_language(text: str) -> str:
    """Detect the language of input text using LLM"""
    try:
        chat = await create_llm_chat(f"lang_detect_{uuid.uuid4()}")
        
        prompt = f"""Detect the language of this text and respond with ONLY the ISO 639-1 language code (2 letters):

Text: "{text}"

Respond with only the 2-letter code (like: en, es, fr, de, etc.). No explanations."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        detected_lang = response.strip().lower()
        # Validate if it's a supported language
        supported_codes = [lang["code"] for lang in SUPPORTED_LANGUAGES]
        if detected_lang in supported_codes:
            return detected_lang
        return "en"  # Default to English if detection fails
        
    except Exception as e:
        logger.error(f"Language detection error: {e}")
        return "en"

async def translate_text_with_llm(text: str, source_lang: str, target_lang: str, context: str = None) -> tuple:
    """Translate text using LLM with context awareness"""
    try:
        chat = await create_llm_chat(f"translate_{uuid.uuid4()}")
        
        # Get language names for better context
        source_name = next((lang["name"] for lang in SUPPORTED_LANGUAGES if lang["code"] == source_lang), source_lang)
        target_name = next((lang["name"] for lang in SUPPORTED_LANGUAGES if lang["code"] == target_lang), target_lang)
        
        context_instruction = f"\n\nContext: {context}" if context else ""
        
        prompt = f"""Translate the following text from {source_name} to {target_name}. 
        
Maintain the original meaning, tone, and cultural context. Handle idioms, slang, and cultural references appropriately.{context_instruction}

Text to translate: "{text}"

Respond with ONLY the translated text."""
        
        message = UserMessage(text=prompt)
        response = await chat.send_message(message)
        
        return response.strip(), 0.95  # Return translation and confidence score
        
    except Exception as e:
        logger.error(f"Translation error: {e}")
        raise HTTPException(status_code=500, detail=f"Translation failed: {str(e)}")

# API Routes
@api_router.get("/")
async def root():
    return {"message": "Ultimate AI Translation & Transliteration App API", "version": "1.0.0"}

@api_router.get("/languages", response_model=List[Language])
async def get_supported_languages():
    """Get list of supported languages"""
    return [Language(**lang) for lang in SUPPORTED_LANGUAGES]

@api_router.post("/translate/text", response_model=TranslationResponse)
async def translate_text(request: TranslationRequest):
    """Translate text with context awareness"""
    try:
        # Auto-detect source language if needed
        if request.source_language == "auto":
            detected_lang = await detect_language(request.text)
            source_lang = detected_lang
        else:
            source_lang = request.source_language
            
        # Skip translation if source and target are the same
        if source_lang == request.target_language:
            translated_text = request.text
            confidence = 1.0
        else:
            translated_text, confidence = await translate_text_with_llm(
                request.text, 
                source_lang, 
                request.target_language,
                request.context
            )
        
        # Create translation response
        translation = TranslationResponse(
            original_text=request.text,
            translated_text=translated_text,
            source_language=source_lang,
            target_language=request.target_language,
            context=request.context,
            confidence_score=confidence
        )
        
        # Save to database
        await db.translations.insert_one(translation.dict())
        
        return translation
        
    except Exception as e:
        logger.error(f"Text translation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/translate/history")
async def get_translation_history(limit: int = 50):
    """Get recent translation history"""
    try:
        translations = await db.translations.find().sort("timestamp", -1).limit(limit).to_list(limit)
        return [TranslationResponse(**translation) for translation in translations]
    except Exception as e:
        logger.error(f"History retrieval error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/conversation/create")
async def create_conversation():
    """Create a new conversation session"""
    conversation_id = str(uuid.uuid4())
    conversation = {
        "id": conversation_id,
        "created_at": datetime.utcnow(),
        "messages": []
    }
    await db.conversations.insert_one(conversation)
    return {"conversation_id": conversation_id}

@api_router.post("/conversation/{conversation_id}/message")
async def add_conversation_message(conversation_id: str, message_request: ConversationMessageRequest):
    """Add message to conversation"""
    try:
        # Create full message object
        message = ConversationMessage(
            conversation_id=conversation_id,
            original_text=message_request.original_text,
            source_language=message_request.source_language,
            target_language=message_request.target_language,
            message_type=message_request.message_type,
            sender_id=message_request.sender_id
        )
        
        # Auto-translate if target language is specified
        if message.target_language and message.target_language != message.source_language:
            translated_text, _ = await translate_text_with_llm(
                message.original_text,
                message.source_language,
                message.target_language
            )
            message.translated_text = translated_text
            message.is_translated = True
        
        # Save message
        await db.conversation_messages.insert_one(message.dict())
        
        # Update conversation
        await db.conversations.update_one(
            {"id": conversation_id},
            {"$push": {"messages": message.id}, "$set": {"updated_at": datetime.utcnow()}}
        )
        
        return message
        
    except Exception as e:
        logger.error(f"Conversation message error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/conversation/{conversation_id}/messages")
async def get_conversation_messages(conversation_id: str):
    """Get messages for a conversation"""
    try:
        messages = await db.conversation_messages.find(
            {"conversation_id": conversation_id}
        ).sort("timestamp", 1).to_list(1000)
        
        return [ConversationMessage(**message) for message in messages]
        
    except Exception as e:
        logger.error(f"Get conversation messages error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Basic health check endpoints from original
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()