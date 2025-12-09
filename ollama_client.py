"""
Ollama API Client for Load Testing
Handles communication with Ollama API
"""

import requests
import time
from typing import Dict, Any, Optional


class OllamaClient:
    """Client for interacting with Ollama API"""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        
    def check_connection(self) -> bool:
        """Check if Ollama is running and accessible"""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            print(f"✗ Cannot connect to Ollama: {e}")
            return False
            
    def list_models(self) -> list:
        """List available models"""
        try:
            response = requests.get(f"{self.api_url}/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            print(f"Error listing models: {e}")
            return []
    
    def generate(self, model: str, prompt: str, stream: bool = False) -> Dict[str, Any]:
        """
        Generate response from Ollama model
        Returns: dict with 'response', 'execution_time', 'success'
        """
        start_time = time.time()
        
        try:
            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream
            }
            
            response = requests.post(
                f"{self.api_url}/generate",
                json=payload,
                timeout=120  # 2 minute timeout
            )
            
            execution_time = time.time() - start_time
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response': data.get('response', ''),
                    'execution_time': execution_time,
                    'model': model,
                    'error': None
                }
            else:
                return {
                    'success': False,
                    'response': '',
                    'execution_time': execution_time,
                    'model': model,
                    'error': f"HTTP {response.status_code}: {response.text}"
                }
                
        except requests.exceptions.Timeout:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'response': '',
                'execution_time': execution_time,
                'model': model,
                'error': 'Request timeout (>120s)'
            }
        except Exception as e:
            execution_time = time.time() - start_time
            return {
                'success': False,
                'response': '',
                'execution_time': execution_time,
                'model': model,
                'error': str(e)
            }
    
    def verify_model(self, model_name: str) -> bool:
        """Verify that a model exists"""
        models = self.list_models()
        return model_name in models
