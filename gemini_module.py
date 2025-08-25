import google.generativeai as genai
import logging
import time
from typing import Optional
import io
import base64
from PIL import Image

class GeminiClient:
    def __init__(self, api_key: str):
        self.logger = logging.getLogger(__name__)
        self.api_key = api_key
        
        if api_key:
            genai.configure(api_key=api_key)
            # Use current Gemini models - gemini-1.5-flash supports both text and vision
            self.model = genai.GenerativeModel('gemini-1.5-flash')
            self.text_model = genai.GenerativeModel('gemini-1.5-flash')
        else:
            self.model = None
            self.text_model = None
            self.logger.warning("No Gemini API key provided")
            
        # Rate limiting
        self.last_request_time = 0
        self.min_request_interval = 1  # Minimum seconds between requests
        
    def analyze_image(self, base64_image: str, response_mode: str = 'short', custom_prompt: str = None) -> str:
        """Analyze image using Gemini Vision API"""
        if not self.model:
            return "Error: No Gemini API key configured. Please set your API key in settings."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Convert base64 to PIL Image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Prepare prompt based on response mode
            if custom_prompt:
                prompt = custom_prompt
            elif response_mode == 'detailed':
                prompt = """You are an intelligent exam helper with vision capabilities. Analyze this image and:

1. Identify any questions, problems, or text that needs answering
2. Provide detailed, comprehensive answers with explanations
3. Include step-by-step solutions for math problems
4. Explain concepts and provide relevant context
5. If multiple questions are visible, answer all of them clearly

Be thorough and educational in your responses. Look carefully at all text, diagrams, charts, and mathematical expressions in the image."""
            else:
                prompt = """You are an intelligent exam helper with vision capabilities. Analyze this image and:

1. Identify any questions, problems, or text that needs answering
2. Provide concise, direct answers
3. Be brief but accurate
4. Focus on the essential information needed

If multiple questions are visible, answer all of them concisely. Look at all text and content in the image."""
            
            # Generate response
            response = self.model.generate_content([prompt, image])
            
            self.last_request_time = time.time()
            
            if response.text:
                return response.text.strip()
            else:
                return "Error: No response generated from Gemini API"
                
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                return "Error: Invalid Gemini API key. Please check your API key in settings."
            elif "quota" in error_msg or "limit" in error_msg:
                return "Error: API quota exceeded or rate limit reached. Please wait and try again."
            elif "safety" in error_msg:
                return "Error: Content was blocked by safety filters. Please try with different content."
            else:
                self.logger.error(f"Gemini Vision API error: {e}")
                return f"Error analyzing image: {str(e)}"
                
    def analyze_image_with_question(self, base64_image: str, question: str, response_mode: str = 'short') -> str:
        """Analyze image with a specific question using Gemini"""
        if not self.model:
            return "Error: No Gemini API key configured."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Convert base64 to PIL Image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Prepare prompt
            if response_mode == 'detailed':
                prompt = f"""You are an intelligent exam helper. Look at this image and answer the following question with detailed explanations:

Question: {question}

Please analyze the image carefully and provide a comprehensive answer with explanations."""
            else:
                prompt = f"""You are an intelligent exam helper. Look at this image and answer the following question concisely:

Question: {question}

Please analyze the image and provide a direct, brief answer."""
            
            response = self.model.generate_content([prompt, image])
            self.last_request_time = time.time()
            
            if response.text:
                return response.text.strip()
            else:
                return "Error: No response generated from Gemini API"
                
        except Exception as e:
            self.logger.error(f"Gemini Vision API with question error: {e}")
            return f"Error analyzing image with question: {str(e)}"
            
    def get_text_answer(self, question: str, response_mode: str = 'short') -> str:
        """Get text-based answer using Gemini (fallback for non-vision queries)"""
        if not self.text_model:
            return "Error: No Gemini API key configured."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Prepare prompt based on response mode
            if response_mode == 'detailed':
                prompt = f"""You are an intelligent exam helper. Provide detailed, comprehensive answers with explanations, examples, and step-by-step solutions when applicable. Include relevant context and background information.

Question: {question}"""
            else:
                prompt = f"""You are an intelligent exam helper. Provide concise, direct answers. Be brief but accurate. Focus on the essential information needed to answer the question.

Question: {question}"""
            
            response = self.text_model.generate_content(prompt)
            self.last_request_time = time.time()
            
            if response.text:
                return response.text.strip()
            else:
                return "Error: No response generated from Gemini API"
                
        except Exception as e:
            self.logger.error(f"Gemini text API error: {e}")
            return f"Error: {str(e)}"
            
    def validate_api_key(self) -> bool:
        """Validate if the Gemini API key is working"""
        if not self.text_model:
            return False
            
        try:
            # Make a simple test request
            response = self.text_model.generate_content("Hello, this is a test.")
            return response.text is not None
            
        except Exception as e:
            self.logger.error(f"Gemini API key validation error: {e}")
            return False
            
    def get_available_models(self):
        """Get list of available Gemini models"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
            return models
        except Exception as e:
            self.logger.error(f"Error getting available models: {e}")
            return []
            
    def extract_text_content(self, base64_image: str, response_mode: str = 'short') -> str:
        """Extract and format text content from image using Gemini OCR capabilities"""
        if not self.model:
            return "Error: No Gemini API key configured. Please set your API key in settings."
            
        try:
            # Rate limiting
            current_time = time.time()
            if current_time - self.last_request_time < self.min_request_interval:
                time.sleep(self.min_request_interval - (current_time - self.last_request_time))
            
            # Convert base64 to PIL Image
            image_data = base64.b64decode(base64_image)
            image = Image.open(io.BytesIO(image_data))
            
            # Prepare OCR-focused prompt
            if response_mode == 'detailed':
                prompt = """You are an intelligent OCR assistant. Analyze this image and extract all text content in a well-organized format:

1. **QUESTIONS**: If there are any questions, list them clearly with numbers/letters
2. **MULTIPLE CHOICE OPTIONS**: If there are options (A, B, C, D, etc.), format them properly
3. **TEXT CONTENT**: Extract all readable text, maintaining structure and formatting
4. **MATHEMATICAL EXPRESSIONS**: Preserve mathematical notation and formulas
5. **TABLES/LISTS**: Format any tabular data or lists clearly

Please organize the extracted text in a readable, structured format. If there are questions with options, present them clearly. Include any instructions, headings, or important text elements."""
            else:
                prompt = """You are an intelligent OCR assistant. Extract and organize all text from this image:

- List any QUESTIONS clearly
- Show MULTIPLE CHOICE OPTIONS (A, B, C, D) if present
- Extract all readable TEXT content
- Preserve MATHEMATICAL expressions
- Maintain structure and formatting

Present the extracted text in a clear, organized format."""
            
            # Generate response
            response = self.model.generate_content([prompt, image])
            
            self.last_request_time = time.time()
            
            if response.text:
                return response.text.strip()
            else:
                return "Error: No text content extracted from the image"
                
        except Exception as e:
            error_msg = str(e).lower()
            if "api key" in error_msg or "authentication" in error_msg:
                return "Error: Invalid Gemini API key. Please check your API key in settings."
            elif "quota" in error_msg or "limit" in error_msg:
                return "Error: API quota exceeded or rate limit reached. Please wait and try again."
            elif "safety" in error_msg:
                return "Error: Content was blocked by safety filters. Please try with different content."
            else:
                self.logger.error(f"Gemini OCR error: {e}")
                return f"Error extracting text: {str(e)}"
    
    def get_model_info(self):
        """Get information about current models"""
        return {
            'vision_model': 'gemini-1.5-flash',
            'text_model': 'gemini-1.5-flash',
            'api_key_configured': bool(self.api_key),
            'models_initialized': bool(self.model and self.text_model)
        }