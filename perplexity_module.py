import requests
import logging
import time
from typing import Optional
import json

class PerplexityClient:
    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.base_url = "https://api.perplexity.ai/chat/completions"
        
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum seconds between requests
        
    def analyze_image(self, base64_image: str, response_mode: str = 'short', custom_prompt: str = None) -> str:
        """Analyze image using Perplexity Vision API"""
        if not self.api_key:
            return "Error: No Perplexity API key configured. Please set your API key in settings."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Prepare prompt based on response mode
            if custom_prompt:
                system_prompt = custom_prompt
            elif response_mode == 'detailed':
                system_prompt = """You are an intelligent exam helper with vision capabilities. Analyze the image and:
1. Identify any questions, problems, or text that needs answering
2. Provide detailed, comprehensive answers with explanations
3. Include step-by-step solutions for math problems
4. Explain concepts and provide relevant context
5. If multiple questions are visible, answer all of them clearly

Be thorough and educational in your responses."""
            else:
                system_prompt = """You are an intelligent exam helper with vision capabilities. Analyze the image and:
1. Identify any questions, problems, or text that needs answering
2. Provide concise, direct answers
3. Be brief but accurate
4. Focus on the essential information needed

If multiple questions are visible, answer all of them concisely."""
            
            # Prepare the request payload
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.2-11b-vision-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": "Please analyze this image and answer any questions or problems you can see."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 800 if response_mode == 'short' else 1500,
                "temperature": 0.3,
                "stream": False
            }
            
            # Make API call
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    answer = result['choices'][0]['message']['content'].strip()
                    return answer
                else:
                    return "Error: No response from Perplexity API"
            else:
                error_msg = f"API Error {response.status_code}: {response.text}"
                self.logger.error(error_msg)
                
                if response.status_code == 401:
                    return "Error: Invalid Perplexity API key. Please check your API key in settings."
                elif response.status_code == 429:
                    return "Error: Rate limit exceeded. Please wait a moment before trying again."
                elif response.status_code == 402:
                    return "Error: API quota exceeded. Please check your Perplexity account."
                else:
                    return f"Error: API request failed ({response.status_code})"
                    
        except requests.exceptions.Timeout:
            return "Error: Request timed out. Please try again."
        except requests.exceptions.ConnectionError:
            return "Error: Connection failed. Please check your internet connection."
        except Exception as e:
            self.logger.error(f"Perplexity API error: {e}")
            return f"Error analyzing image: {str(e)}"
            
    def analyze_image_with_question(self, base64_image: str, question: str, response_mode: str = 'short') -> str:
        """Analyze image with a specific question using Perplexity"""
        if not self.api_key:
            return "Error: No Perplexity API key configured."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Prepare prompt
            if response_mode == 'detailed':
                system_prompt = "You are an intelligent exam helper. Analyze the image and provide detailed answers with explanations."
            else:
                system_prompt = "You are an intelligent exam helper. Analyze the image and provide concise, direct answers."
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.2-11b-vision-instruct",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": f"Question: {question}\n\nPlease analyze this image and answer the question above."
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/png;base64,{base64_image}"
                                }
                            }
                        ]
                    }
                ],
                "max_tokens": 800 if response_mode == 'short' else 1500,
                "temperature": 0.3,
                "stream": False
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return "Error: No response from Perplexity API"
            else:
                return f"Error: API request failed ({response.status_code})"
                
        except Exception as e:
            self.logger.error(f"Perplexity API with question error: {e}")
            return f"Error analyzing image with question: {str(e)}"
            
    def get_text_answer(self, question: str, response_mode: str = 'short') -> str:
        """Get text-based answer using Perplexity (fallback for non-vision queries)"""
        if not self.api_key:
            return "Error: No Perplexity API key configured."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Prepare prompt based on response mode
            if response_mode == 'detailed':
                system_prompt = """You are an intelligent exam helper. Provide detailed, comprehensive answers with explanations, examples, and step-by-step solutions when applicable. Include relevant context and background information."""
            else:
                system_prompt = """You are an intelligent exam helper. Provide concise, direct answers. Be brief but accurate. Focus on the essential information needed to answer the question."""
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Question: {question}"
                    }
                ],
                "max_tokens": 500 if response_mode == 'short' else 1000,
                "temperature": 0.3,
                "stream": False
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=30)
            self.last_request_time = time.time()
            
            if response.status_code == 200:
                result = response.json()
                if 'choices' in result and len(result['choices']) > 0:
                    return result['choices'][0]['message']['content'].strip()
                else:
                    return "Error: No response from Perplexity API"
            else:
                return f"Error: API request failed ({response.status_code})"
                
        except Exception as e:
            self.logger.error(f"Perplexity text API error: {e}")
            return f"Error: {str(e)}"
            
    def validate_api_key(self) -> bool:
        """Validate if the Perplexity API key is working"""
        if not self.api_key:
            return False
            
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {"role": "user", "content": "Hello"}
                ],
                "max_tokens": 5
            }
            
            response = requests.post(self.base_url, headers=headers, json=payload, timeout=10)
            return response.status_code == 200
            
        except Exception as e:
            self.logger.error(f"Perplexity API key validation error: {e}")
            return False