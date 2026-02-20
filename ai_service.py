"""
Pollivu - AI Service
Multi-provider AI integration for poll generation and suggestions.
Supports: Google Gemini, OpenAI, Anthropic Claude, Ollama
"""

import json
import logging
import re
from abc import ABC, abstractmethod
from typing import Optional, Dict, List, Any
import requests
import ai_prompts

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract base class for AI providers."""
    
    @abstractmethod
    def generate_poll(self, topic: str, num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        """Generate a poll question and options from a topic."""
        pass
    
    @abstractmethod
    def suggest_improvements(self, question: str, options: List[str]) -> Dict[str, Any]:
        """Suggest improvements for an existing poll."""
        pass
    
    @abstractmethod
    def test_connection(self) -> bool:
        """Test if the API connection is working."""
        pass
    
    def _get_generation_prompt(self, topic: str, num_options: int, style: str) -> str:
        """Get the prompt for poll generation."""
        return ai_prompts.get_generation_prompt(topic, num_options, style)

    def _get_suggestion_prompt(self, question: str, options: List[str]) -> str:
        """Get the prompt for poll suggestions."""
        return ai_prompts.get_suggestion_prompt(question, options)

    def _get_new_options_prompt(self, question: str, existing_options: List[str], num_options: int = 4) -> str:
        """Get the prompt for suggesting new poll options."""
        return ai_prompts.get_new_options_prompt(question, existing_options, num_options)

    def suggest_new_options(self, question: str, existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        """Suggest new options for an existing poll. Default implementation uses generate_poll."""
        raise NotImplementedError("Subclasses should implement suggest_new_options")

    def _parse_json_response(self, response: str) -> Dict[str, Any]:
        """Parse JSON from AI response, handling common formatting issues."""
        # Try to find JSON in the response
        json_match = re.search(r'\{[\s\S]*\}', response)
        if json_match:
            try:
                return json.loads(json_match.group())
            except json.JSONDecodeError:
                pass
        
        # Try cleaning up the response
        cleaned = response.strip()
        if cleaned.startswith('```json'):
            cleaned = cleaned[7:]
        if cleaned.startswith('```'):
            cleaned = cleaned[3:]
        if cleaned.endswith('```'):
            cleaned = cleaned[:-3]
        
        try:
            return json.loads(cleaned.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse AI response as JSON: {e}")


class GeminiProvider(AIProvider):
    """Google Gemini AI provider."""
    
    # Latest models (as of Feb 2026):
    # - gemini-2.5-flash: Best price-performance, thinking & agentic
    # - gemini-2.5-pro: Advanced thinking model for complex tasks
    # - gemini-3-flash: Balanced speed and frontier intelligence
    # - gemini-3-pro: Most intelligent, multimodal understanding
    # - gemini-2.5-flash-lite: Ultra-fast, cost-efficient
    
    def __init__(self, api_key: str, model: str = 'gemini-2.5-flash'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://generativelanguage.googleapis.com/v1beta'

    def _extract_response_text(self, result: Dict) -> str:
        """
        Extract the actual response text from a Gemini API result.
        Gemini 2.5+ "thinking" models return multiple parts:
        - parts with 'thought': true  → internal reasoning (skip)
        - the final part              → actual JSON response
        """
        parts = result['candidates'][0]['content']['parts']
        # Return the last non-thought part (the actual answer)
        for part in reversed(parts):
            if not part.get('thought', False):
                return part['text']
        # Fallback: return last part regardless
        return parts[-1]['text']

    def generate_poll(self, topic: str, num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        prompt = self._get_generation_prompt(topic, num_options, style)
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {'Content-Type': 'application/json'}
        params = {'key': self.api_key}
        
        data = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.7,
                'maxOutputTokens': 8196,
                'responseMimeType': 'application/json'
            }
        }
        
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = self._extract_response_text(result)
        return self._parse_json_response(text)
    
    def suggest_new_options(self, question: str, existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        prompt = self._get_new_options_prompt(question, existing_options, num_options)
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {'Content-Type': 'application/json'}
        params = {'key': self.api_key}
        
        data = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.8,
                'maxOutputTokens': 1024,
                'responseMimeType': 'application/json'
            }
        }
        
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = self._extract_response_text(result)
        return self._parse_json_response(text)

    def suggest_improvements(self, question: str, options: List[str]) -> Dict[str, Any]:
        prompt = self._get_suggestion_prompt(question, options)
        
        url = f"{self.base_url}/models/{self.model}:generateContent"
        headers = {'Content-Type': 'application/json'}
        params = {'key': self.api_key}
        
        data = {
            'contents': [{'parts': [{'text': prompt}]}],
            'generationConfig': {
                'temperature': 0.5,
                'maxOutputTokens': 4096,
                'responseMimeType': 'application/json'
            }
        }
        
        response = requests.post(url, headers=headers, params=params, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = self._extract_response_text(result)
        return self._parse_json_response(text)
    
    def test_connection(self) -> bool:
        url = f"{self.base_url}/models/{self.model}"
        params = {'key': self.api_key}
        
        try:
            response = requests.get(url, params=params, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Gemini connection test failed: {e}")
            return False


class OpenAIProvider(AIProvider):
    """OpenAI GPT provider."""
    
    # Latest models (as of Feb 2026):
    # - gpt-5.2: Best for coding and agentic tasks
    # - gpt-5-mini: Faster, cost-efficient version of GPT-5
    # - gpt-5-nano: Fastest, most cost-efficient GPT-5
    # - gpt-4.1: Smartest non-reasoning model
    # - gpt-4o: Fast, intelligent, flexible
    # - gpt-4o-mini: Affordable small model
    
    def __init__(self, api_key: str, model: str = 'gpt-4.1'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.openai.com/v1'
    
    def generate_poll(self, topic: str, num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        prompt = self._get_generation_prompt(topic, num_options, style)
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant that generates poll questions. Always respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.7,
            'max_tokens': 8196,
            'response_format': {'type': 'json_object'}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['choices'][0]['message']['content']
        return self._parse_json_response(text)
    
    def suggest_improvements(self, question: str, options: List[str]) -> Dict[str, Any]:
        prompt = self._get_suggestion_prompt(question, options)
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant that improves poll questions. Always respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.5,
            'max_tokens': 4096,
            'response_format': {'type': 'json_object'}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['choices'][0]['message']['content']
        return self._parse_json_response(text)

    def suggest_new_options(self, question: str, existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        prompt = self._get_new_options_prompt(question, existing_options, num_options)
        
        url = f"{self.base_url}/chat/completions"
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.api_key}'
        }
        
        data = {
            'model': self.model,
            'messages': [
                {'role': 'system', 'content': 'You are a helpful assistant that suggests poll options. Always respond with valid JSON only.'},
                {'role': 'user', 'content': prompt}
            ],
            'temperature': 0.8,
            'max_tokens': 8196,
            'response_format': {'type': 'json_object'}
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['choices'][0]['message']['content']
        return self._parse_json_response(text)

    def test_connection(self) -> bool:
        url = f"{self.base_url}/models"
        headers = {'Authorization': f'Bearer {self.api_key}'}
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"OpenAI connection test failed: {e}")
            return False


class ClaudeProvider(AIProvider):
    """Anthropic Claude provider."""
    
    # Latest models (as of Feb 2026):
    # - claude-opus-4-6: Most intelligent, agents & coding
    # - claude-sonnet-4-5: Best speed & intelligence balance
    # - claude-haiku-4-5: Fastest, near-frontier intelligence
    
    def __init__(self, api_key: str, model: str = 'claude-sonnet-4-5'):
        self.api_key = api_key
        self.model = model
        self.base_url = 'https://api.anthropic.com/v1'
    
    def generate_poll(self, topic: str, num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        prompt = self._get_generation_prompt(topic, num_options, style)
        
        url = f"{self.base_url}/messages"
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model,
            'max_tokens': 8196,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['content'][0]['text']
        return self._parse_json_response(text)
    
    def suggest_improvements(self, question: str, options: List[str]) -> Dict[str, Any]:
        prompt = self._get_suggestion_prompt(question, options)
        
        url = f"{self.base_url}/messages"
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model,
            'max_tokens': 4096,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['content'][0]['text']
        return self._parse_json_response(text)

    def suggest_new_options(self, question: str, existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        prompt = self._get_new_options_prompt(question, existing_options, num_options)
        
        url = f"{self.base_url}/messages"
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model,
            'max_tokens': 4096,
            'messages': [{'role': 'user', 'content': prompt}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        text = result['content'][0]['text']
        return self._parse_json_response(text)

    def test_connection(self) -> bool:
        # Claude doesn't have a simple test endpoint, so we try a minimal request
        url = f"{self.base_url}/messages"
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': self.api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': self.model,
            'max_tokens': 10,
            'messages': [{'role': 'user', 'content': 'Hi'}]
        }
        
        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Claude connection test failed: {e}")
            return False


class OllamaProvider(AIProvider):
    """Ollama local model provider."""
    
    # Popular models (fetched dynamically from user's Ollama instance):
    # - llama3.3:latest, llama3.1:8b
    # - qwen3:8b, qwen3:4b, qwen3:1.7b
    # - gemma3:12b, gemma3:4b, gemma3:1b
    # - mistral:latest, phi4:latest
    # - deepseek-r1:8b, deepseek-r1:1.5b
    
    def __init__(self, base_url: str = 'http://localhost:11434', model: str = 'qwen3:8b'):
        self.base_url = base_url.rstrip('/').strip()
        self.model = model.strip()  # Remove any trailing whitespace
    
    def generate_poll(self, topic: str, num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        prompt = self._get_generation_prompt(topic, num_options, style)
        
        url = f"{self.base_url}/api/generate"
        data = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {
                'temperature': 0.7
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        text = result['response']
        return self._parse_json_response(text)
    
    def suggest_improvements(self, question: str, options: List[str]) -> Dict[str, Any]:
        prompt = self._get_suggestion_prompt(question, options)
        
        url = f"{self.base_url}/api/generate"
        data = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {
                'temperature': 0.5
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        text = result['response']
        return self._parse_json_response(text)

    def suggest_new_options(self, question: str, existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        prompt = self._get_new_options_prompt(question, existing_options, num_options)
        
        url = f"{self.base_url}/api/generate"
        data = {
            'model': self.model,
            'prompt': prompt,
            'stream': False,
            'format': 'json',
            'options': {
                'temperature': 0.8
            }
        }
        
        response = requests.post(url, json=data, timeout=60)
        response.raise_for_status()
        
        result = response.json()
        text = result['response']
        return self._parse_json_response(text)

    def test_connection(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"Ollama connection test failed: {e}")
            return False
    
    def get_models(self) -> List[str]:
        """Fetch available models from Ollama instance."""
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                data = response.json()
                return [model['name'] for model in data.get('models', [])]
            return []
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models: {e}")
            return []


class AIService:
    """Main AI service that manages providers and handles requests."""
    
    PROVIDERS = {
        'gemini': GeminiProvider,
        'openai': OpenAIProvider,
        'claude': ClaudeProvider,
        'ollama': OllamaProvider
    }
    
    def __init__(self, user=None, secret_key: str = None):
        self.user = user
        self.secret_key = secret_key

    def get_provider(self, provider_name: str) -> Optional[AIProvider]:
        """Get an initialized provider for the user."""
        if provider_name not in self.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}")
        
        if not self.user or not self.secret_key:
            raise ValueError("User authentication required for AI features")
        
        keys = self.user.get_api_keys(self.secret_key)
        
        if provider_name == 'gemini':
            key = keys.get('gemini')
            if not key:
                raise ValueError("Gemini API key not configured")
            model = keys.get('gemini_model', 'gemini-2.5-flash')
            return GeminiProvider(key, model=model)
        
        elif provider_name == 'openai':
            key = keys.get('openai')
            if not key:
                raise ValueError("OpenAI API key not configured")
            model = keys.get('openai_model', 'gpt-4.1')
            return OpenAIProvider(key, model=model)
        
        elif provider_name == 'claude':
            key = keys.get('claude')
            if not key:
                raise ValueError("Claude API key not configured")
            model = keys.get('claude_model', 'claude-sonnet-4-5')
            return ClaudeProvider(key, model=model)
        
        elif provider_name == 'ollama':
            url = keys.get('ollama_url', 'http://localhost:11434')
            model = keys.get('ollama_model', 'qwen3:8b')
            return OllamaProvider(url, model)
        
        return None
    
    def generate_poll(self, provider_name: str, topic: str, 
                      num_options: int = 4, style: str = 'neutral') -> Dict[str, Any]:
        """Generate a poll using the specified provider."""
        provider = self.get_provider(provider_name)
        return provider.generate_poll(topic, num_options, style)
    
    def suggest_improvements(self, provider_name: str, 
                            question: str, options: List[str]) -> Dict[str, Any]:
        """Get AI suggestions for improving a poll."""
        provider = self.get_provider(provider_name)
        return provider.suggest_improvements(question, options)

    def suggest_new_options(self, provider_name: str, question: str,
                           existing_options: List[str], num_options: int = 4) -> Dict[str, Any]:
        """Suggest new options for an existing poll that don't duplicate existing ones."""
        provider = self.get_provider(provider_name)
        return provider.suggest_new_options(question, existing_options, num_options)

    def test_provider(self, provider_name: str) -> bool:
        """Test if a provider is properly configured and working."""
        try:
            provider = self.get_provider(provider_name)
            return provider.test_connection()
        except Exception as e:
            logger.warning(f"Provider test failed for {provider_name}: {e}")
            return False

    def get_available_providers(self) -> List[Dict[str, Any]]:
        """Get list of available providers for the user."""
        if not self.user or not self.secret_key:
            return []
        
        keys = self.user.get_api_keys(self.secret_key)
        providers = []
        
        if keys.get('gemini'):
            providers.append({
                'id': 'gemini',
                'name': 'Google Gemini',
                'configured': True,
                'models': ['gemini-2.5-flash', 'gemini-2.5-pro', 'gemini-3-flash', 'gemini-3-pro', 'gemini-2.5-flash-lite']
            })
        
        if keys.get('openai'):
            providers.append({
                'id': 'openai',
                'name': 'OpenAI',
                'configured': True,
                'models': ['gpt-5.2', 'gpt-5-mini', 'gpt-5-nano', 'gpt-4.1', 'gpt-4.1-mini', 'gpt-4o', 'gpt-4o-mini']
            })
        
        if keys.get('claude'):
            providers.append({
                'id': 'claude',
                'name': 'Anthropic Claude',
                'configured': True,
                'models': ['claude-opus-4-6', 'claude-sonnet-4-5', 'claude-haiku-4-5']
            })
        
        # Ollama only shows if explicitly configured
        if keys.get('ollama_url') or keys.get('ollama_model'):
            providers.append({
                'id': 'ollama',
                'name': 'Ollama (Local)',
                'configured': True,
                'models': ['qwen3:8b', 'llama3.3:latest', 'gemma3:12b', 'mistral:latest', 'deepseek-r1:8b', 'phi4:latest']
            })
        
        return providers

    def get_ollama_models(self, url: str) -> List[str]:
        """Fetch models from a specific Ollama URL."""
        try:
            provider = OllamaProvider(url, '')
            return provider.get_models()
        except Exception as e:
            logger.warning(f"Failed to fetch Ollama models from {url}: {e}")
            return []
