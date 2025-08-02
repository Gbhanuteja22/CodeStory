from google import genai
import os
import logging
import json
from datetime import datetime
from pathlib import Path

class AIResponseLogger:
    def __init__(self):
        self.log_folder = Path(os.getenv("LOG_DIR", "logs"))
        self.log_folder.mkdir(exist_ok=True)
        
        current_date = datetime.now().strftime('%Y%m%d')
        self.log_file_path = self.log_folder / f"ai_interactions_{current_date}.log"
        
        self.interaction_logger = logging.getLogger("ai_interaction_logger")
        self.interaction_logger.setLevel(logging.INFO)
        self.interaction_logger.propagate = False
        
        file_handler = logging.FileHandler(self.log_file_path, encoding='utf-8')
        formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        file_handler.setFormatter(formatter)
        self.interaction_logger.addHandler(file_handler)
        
    def log_request(self, user_prompt: str) -> None:
        self.interaction_logger.info(f"USER_PROMPT: {user_prompt}")
        
    def log_response(self, ai_response: str) -> None:
        self.interaction_logger.info(f"AI_RESPONSE: {ai_response}")

class ResponseCacheManager:
    def __init__(self, cache_file_name: str = "ai_response_cache.json"):
        self.cache_file_path = Path(cache_file_name)
        self.response_cache = {}
        self._load_existing_cache()
        
    def _load_existing_cache(self) -> None:
        if self.cache_file_path.exists():
            try:
                with open(self.cache_file_path, "r", encoding="utf-8") as cache_file:
                    self.response_cache = json.load(cache_file)
            except Exception as cache_error:
                print(f"Warning: Failed to load AI response cache - {cache_error}")
                self.response_cache = {}
                
    def get_cached_response(self, user_prompt: str) -> str:
        return self.response_cache.get(user_prompt)
        
    def cache_response(self, user_prompt: str, ai_response: str) -> None:
        self.response_cache[user_prompt] = ai_response
        try:
            with open(self.cache_file_path, "w", encoding="utf-8") as cache_file:
                json.dump(self.response_cache, cache_file, indent=2, ensure_ascii=False)
        except Exception as save_error:
            print(f"Warning: Failed to save AI response cache - {save_error}")

class LanguageModelConnector:
    def __init__(self):
        self.logger = AIResponseLogger()
        self.cache_manager = ResponseCacheManager()
        self.api_key = os.environ.get('GEMINI_API_KEY')
        
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY environment variable must be set")
            
    def _create_ai_client(self):
        return genai.Client(api_key=self.api_key)
        
    def generate_response(self, user_prompt: str, enable_caching: bool = True) -> str:
        self.logger.log_request(user_prompt)
        
        if enable_caching:
            cached_response = self.cache_manager.get_cached_response(user_prompt)
            if cached_response:
                self.logger.log_response(cached_response)
                return cached_response
                
        try:
            ai_client = self._create_ai_client()
            model_response = ai_client.models.generate_content(
                model='gemini-2.0-flash-exp',
                contents=user_prompt
            )
            
            generated_text = model_response.text
            
            if enable_caching:
                self.cache_manager.cache_response(user_prompt, generated_text)
                
            self.logger.log_response(generated_text)
            return generated_text
            
        except Exception as generation_error:
            error_message = f"AI response generation failed: {generation_error}"
            self.logger.log_response(error_message)
            raise RuntimeError(error_message)

_model_connector_instance = None

def query_language_model(user_prompt: str, use_cache: bool = True) -> str:
    global _model_connector_instance
    
    if _model_connector_instance is None:
        _model_connector_instance = LanguageModelConnector()
        
    return _model_connector_instance.generate_response(user_prompt, enable_caching=use_cache)
