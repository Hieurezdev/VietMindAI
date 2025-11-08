from google import genai
from app.config.config import get_settings

class Client:
    def __init__(self, api_key: str | None = None) -> None:
        settings = get_settings()
        self.api_key = api_key or settings.gemini_api_key
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY not configured. Please set it in your .env file.")
        self.client = genai.Client(api_key=self.api_key)

    def get_client(self) -> genai.Client:
        return self.client

    
    
    
