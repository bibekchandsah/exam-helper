from openai import OpenAI
import logging
import time
from typing import Optional

class LLMClient:
    def __init__(self, api_key: str, model: str = "gpt-3.5-turbo"):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        self.model = model
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            self.client = None
            self.logger.warning("No OpenAI API key provided")
            
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum seconds between requests
        
        # Available models (commonly used ones)
        self.available_models = [
            "gpt-4o",
            "gpt-4o-mini", 
            "gpt-4-turbo",
            "gpt-4",
            "gpt-3.5-turbo"
        ]
        
        # Cache for working models to avoid repeated API calls
        self.working_models = []
        self.models_checked = False
        
    def get_answer(self, question: str, response_mode: str = 'short') -> str:
        """Get answer from OpenAI GPT"""
        if not self.client:
            return "Error: No OpenAI API key configured. Please set your API key in settings."
            
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
                
            # Make API call using the selected model
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Question: {question}"}
                ],
                max_tokens=500 if response_mode == 'short' else 1000,
                temperature=0.3
            )
            
            self.last_request_time = time.time()
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "api key" in error_msg:
                return "Error: Invalid OpenAI API key. Please check your API key in settings."
            elif "rate limit" in error_msg:
                return "Error: Rate limit exceeded. Please wait a moment before asking another question."
            elif "quota" in error_msg:
                return "Error: API quota exceeded. Please check your OpenAI account."
            elif "model" in error_msg and "does not exist" in error_msg:
                return f"Error: Model '{self.model}' is not available. Please select a different model."
            else:
                self.logger.error(f"LLM error: {e}")
                return f"Error: {str(e)}"
            
    def validate_api_key(self) -> bool:
        """Validate if the API key is working"""
        if not self.client:
            return False
            
        try:
            # Make a simple test request
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5
            )
            return True
            
        except Exception as e:
            self.logger.error(f"API key validation error: {e}")
            return False
            
    def get_quick_answer(self, question: str) -> str:
        """Get a very quick, one-sentence answer"""
        if not self.client:
            return "Error: No API key configured."
            
        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "Provide only a single, direct sentence answer. Be extremely concise."},
                    {"role": "user", "content": question}
                ],
                max_tokens=50,
                temperature=0.1
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Quick answer error: {e}")
            return "Error getting quick answer."
            
    def analyze_question_type(self, question: str) -> str:
        """Analyze what type of question this is"""
        question_lower = question.lower()
        
        if any(word in question_lower for word in ['calculate', 'solve', 'find', 'compute']):
            return 'math'
        elif any(word in question_lower for word in ['define', 'what is', 'meaning']):
            return 'definition'
        elif any(word in question_lower for word in ['explain', 'how', 'why']):
            return 'explanation'
        elif any(word in question_lower for word in ['list', 'name', 'identify']):
            return 'listing'
        else:
            return 'general'
            
    def get_contextual_answer(self, question: str, context: str = "") -> str:
        """Get answer with additional context"""
        if not self.client:
            return "Error: No API key configured."
            
        try:
            prompt = f"Context: {context}\n\nQuestion: {question}" if context else question
            
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a helpful exam assistant. Use the provided context to give accurate answers."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=800,
                temperature=0.3
            )
            
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Contextual answer error: {e}")
            return f"Error: {str(e)}"
            
    def analyze_image(self, base64_image: str, response_mode: str = 'short', custom_prompt: str = None) -> str:
        """Analyze image using GPT-4 Vision and provide answers"""
        if not self.client:
            return "Error: No OpenAI API key configured. Please set your API key in settings."
            
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
            
            # Prepare the message with image
            messages = [
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
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            # Make API call to GPT-4 Vision
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=800 if response_mode == 'short' else 1500,
                temperature=0.3
            )
            
            self.last_request_time = time.time()
            
            answer = response.choices[0].message.content.strip()
            return answer
            
        except Exception as e:
            error_msg = str(e).lower()
            if "authentication" in error_msg or "api key" in error_msg:
                return "Error: Invalid OpenAI API key. Please check your API key in settings."
            elif "rate limit" in error_msg:
                return "Error: Rate limit exceeded. Please wait a moment before trying again."
            elif "quota" in error_msg:
                return "Error: API quota exceeded. Please check your OpenAI account."
            elif "model" in error_msg and "vision" in error_msg:
                return "Error: GPT-4 Vision model not available. Please check your OpenAI plan."
            else:
                self.logger.error(f"Vision API error: {e}")
                return f"Error analyzing image: {str(e)}"
                
    def analyze_image_with_question(self, base64_image: str, question: str, response_mode: str = 'short') -> str:
        """Analyze image with a specific question"""
        if not self.client:
            return "Error: No OpenAI API key configured."
            
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
            
            messages = [
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
                                "url": f"data:image/png;base64,{base64_image}",
                                "detail": "high"
                            }
                        }
                    ]
                }
            ]
            
            response = self.client.chat.completions.create(
                model="gpt-4-vision-preview",
                messages=messages,
                max_tokens=800 if response_mode == 'short' else 1500,
                temperature=0.3
            )
            
            self.last_request_time = time.time()
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            self.logger.error(f"Vision API with question error: {e}")
            return f"Error analyzing image with question: {str(e)}"
    
    def get_working_models(self) -> list:
        """Get list of working models for the current API key"""
        if not self.client:
            return []
            
        if self.models_checked and self.working_models:
            return self.working_models
            
        working_models = []
        
        for model in self.available_models:
            try:
                # Test each model with a simple request
                response = self.client.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": "Hi"}],
                    max_tokens=5,
                    timeout=10
                )
                working_models.append(model)
                self.logger.info(f"Model {model} is working")
                
            except Exception as e:
                error_msg = str(e).lower()
                if "model" in error_msg and ("does not exist" in error_msg or "not found" in error_msg):
                    self.logger.info(f"Model {model} not available")
                elif "authentication" in error_msg or "api key" in error_msg:
                    self.logger.error("API key authentication failed")
                    break  # No point testing other models
                else:
                    self.logger.warning(f"Model {model} test failed: {e}")
                    
        self.working_models = working_models
        self.models_checked = True
        return working_models
    
    def set_model(self, model: str):
        """Set the model to use for requests"""
        self.model = model
        self.logger.info(f"Model changed to: {model}")
    
    def get_current_model(self) -> str:
        """Get the currently selected model"""
        return self.model