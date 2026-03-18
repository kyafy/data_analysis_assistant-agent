from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from app.services.chat_service import NL2SQLService
import json
import logging

api_router = APIRouter()
logger = logging.getLogger(__name__)

# Initialize service (Singleton-ish for now)
# In production, use dependency injection
chat_service = NL2SQLService()

class ChatRequest(BaseModel):
    session_id: str
    question: str

@api_router.post("/chat/stream")
async def chat_stream_endpoint(request: ChatRequest):
    """
    SSE Endpoint for chat streaming.
    """
    async def event_generator():
        # Yield initial status
        yield f"data: {json.dumps({'status': 'thinking', 'delta': ''})}\n\n"
        
        try:
            # Stream response from service
            # We assume chat_service.chat_stream yields formatted SSE data lines or partials
            # For now, let's wrap the service generator
            async for chunk in chat_service.chat_stream(request.question, request.session_id):
                yield chunk
            
            # Yield final status if not already done
            yield f"data: {json.dumps({'status': 'final', 'delta': '', 'final': True})}\n\n"
            
        except Exception as e:
            logger.error(f"Chat stream error: {e}")
            yield f"data: {json.dumps({'status': 'error', 'delta': str(e)})}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

# Add REST endpoints for sessions (Mock for Phase 3.4 minimal requirement)
@api_router.post("/sessions")
async def create_session():
    return {"id": "mock_session_123", "title": "New Session"}

@api_router.get("/sessions")
async def list_sessions():
    return [{"id": "mock_session_123", "title": "New Session", "updated_at": "2023-10-27T10:00:00Z"}]

@api_router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: str):
    return []

# Config endpoints
@api_router.get("/config/db")
async def get_db_config():
    """Get current DB configuration."""
    from app.core.db.database import DB_CONFIG_PATH
    import os
    
    if os.path.exists(DB_CONFIG_PATH):
        try:
            with open(DB_CONFIG_PATH, "r") as f:
                config = json.load(f)
                # Mask password
                if "password" in config:
                    config["password"] = "******"
                return config
        except Exception as e:
            logger.error(f"Error reading config: {e}")
            return {}
    return {}

class DBConfigRequest(BaseModel):
    host: str
    port: int
    user: str
    password: str = "" # Default to empty string
    db: str

@api_router.post("/config/db")
async def update_db_config(config: DBConfigRequest):
    """Update DB configuration and reload service."""
    from app.core.db.database import DB_CONFIG_PATH, test_connection
    
    config_dict = config.model_dump()
    
    # Handle "keep password unchanged" logic
    # If password is empty, try to retain existing password from file
    if not config_dict["password"]:
        if os.path.exists(DB_CONFIG_PATH):
            try:
                with open(DB_CONFIG_PATH, "r") as f:
                    old_config = json.load(f)
                    if "password" in old_config:
                        config_dict["password"] = old_config["password"]
            except Exception:
                pass
    
    # Test connection
    if not test_connection(config_dict):
        return {"status": "error", "message": "Connection failed"}
        
    try:
        with open(DB_CONFIG_PATH, "w") as f:
            json.dump(config_dict, f, indent=2)
            
        # Reload service
        chat_service.reload_db()
        
        return {"status": "success", "message": "Configuration updated and reloaded"}
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return {"status": "error", "message": str(e)}
