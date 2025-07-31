#!/usr/bin/env python3
"""
Google Gemini Integration for iHub Bot

This module provides integration with Google's Gemini API as an alternative
to OpenAI, offering better privacy control and corporate compliance.
"""

import os
import json
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime

class GeminiChatbot:
    def __init__(self, api_key: str = None, model_name: str = "gemini-1.5-flash"):
        """
        Initialize Gemini chatbot
        
        Args:
            api_key: Google AI API key (can also be set via GEMINI_API_KEY env var)
            model_name: Gemini model to use (gemini-1.5-flash, gemini-1.5-pro, etc.)
        """
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model_name = model_name
        
        if not self.api_key:
            raise ValueError("Gemini API key is required. Set GEMINI_API_KEY environment variable or pass api_key parameter.")
        
        # Configure the Gemini API
        genai.configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = genai.GenerativeModel(model_name)
        
        # Safety settings for educational content
        self.safety_settings = [
            {
                "category": "HARM_CATEGORY_HARASSMENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_HATE_SPEECH",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            },
            {
                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                "threshold": "BLOCK_MEDIUM_AND_ABOVE"
            }
        ]
        
        # Generation configuration for optimal responses
        self.generation_config = {
            "temperature": 0.7,
            "top_p": 0.8,
            "top_k": 40,
            "max_output_tokens": 1024,
        }
    
    def create_system_prompt(self, context: str = "", school_info: Dict = None) -> str:
        """Create a comprehensive system prompt for the school assistant"""
        
        base_prompt = f"""You are iHub Bot, a helpful AI assistant for students at an educational institution. Your primary role is to help students find tools, equipment, locations, and information about resources available at the school.

CORE RESPONSIBILITIES:
- Help students locate tools, equipment, and facilities
- Provide information about availability, training requirements, and contacts
- Answer questions about workflows and procedures
- Maintain a helpful, professional, and educational tone
- Encourage learning and proper use of resources

RESPONSE GUIDELINES:
- Be conversational but informative
- Always mention specific locations, contacts, and availability when relevant
- If training is required, emphasize this and provide contact information
- For safety-critical equipment, remind users about proper training
- If you don't have specific information, direct them to appropriate contacts
- Keep responses concise but complete
- Use emojis sparingly and appropriately

SAFETY & CONDUCT:
- Prioritize student safety and proper equipment use
- Do not provide information that could lead to unsafe practices
- Encourage following all school policies and procedures
- Report any concerning requests appropriately

"""

        if school_info:
            base_prompt += f"""
SCHOOL INFORMATION:
- Institution: {school_info.get('name', 'Educational Institution')}
- Type: {school_info.get('type', 'School/University')}
- Special focus: {school_info.get('focus', 'General education')}
"""

        if context:
            base_prompt += f"""
AVAILABLE RESOURCES CONTEXT:
{context}

Based on the above resources, provide helpful guidance to students. Always reference specific tools, locations, and contacts when relevant to their questions.
"""
        
        base_prompt += """
Remember: You're here to help students succeed in their educational journey by connecting them with the right resources and information!"""
        
        return base_prompt
    
    def generate_response(self, user_message: str, context: str = "", 
                         conversation_history: List[Dict] = None,
                         school_info: Dict = None) -> Dict:
        """
        Generate a response using Gemini
        
        Args:
            user_message: The user's question/message
            context: Context about available tools/resources
            conversation_history: Previous conversation for context
            school_info: Information about the school/institution
            
        Returns:
            Dict with response, metadata, and any errors
        """
        try:
            # Create system prompt
            system_prompt = self.create_system_prompt(context, school_info)
            
            # Build conversation context
            full_prompt = system_prompt + "\n\n"
            
            # Add conversation history if available
            if conversation_history:
                full_prompt += "RECENT CONVERSATION:\n"
                for msg in conversation_history[-3:]:  # Last 3 exchanges
                    role = "Student" if msg.get('role') == 'user' else "Assistant"
                    full_prompt += f"{role}: {msg.get('content', '')}\n"
                full_prompt += "\n"
            
            # Add current question
            full_prompt += f"Current Student Question: {user_message}\n\n"
            full_prompt += "Please provide a helpful response:"
            
            # Generate response
            response = self.model.generate_content(
                full_prompt,
                generation_config=self.generation_config,
                safety_settings=self.safety_settings
            )
            
            # Check if response was blocked
            if response.candidates and response.candidates[0].finish_reason.name in ['SAFETY', 'BLOCKED']:
                return {
                    'success': False,
                    'response': "I apologize, but I can't provide a response to that request. Please ask me about school resources, tools, or educational assistance.",
                    'error': 'Content blocked by safety filters',
                    'finish_reason': response.candidates[0].finish_reason.name
                }
            
            # Extract response text
            response_text = response.text
            
            # Get token usage information if available
            usage_metadata = {}
            if hasattr(response, 'usage_metadata'):
                usage_metadata = {
                    'prompt_token_count': getattr(response.usage_metadata, 'prompt_token_count', 0),
                    'candidates_token_count': getattr(response.usage_metadata, 'candidates_token_count', 0),
                    'total_token_count': getattr(response.usage_metadata, 'total_token_count', 0)
                }
            
            return {
                'success': True,
                'response': response_text,
                'model': self.model_name,
                'timestamp': datetime.now().isoformat(),
                'usage': usage_metadata,
                'finish_reason': response.candidates[0].finish_reason.name if response.candidates else 'STOP'
            }
            
        except Exception as e:
            return {
                'success': False,
                'response': "I'm experiencing technical difficulties. Please try again or contact the help desk for assistance.",
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
    
    def test_connection(self) -> Dict:
        """Test the Gemini API connection"""
        try:
            response = self.model.generate_content(
                "Please respond with 'Hello! Gemini connection successful.' to test the API.",
                generation_config={"max_output_tokens": 50}
            )
            
            return {
                'success': True,
                'message': 'Gemini API connection successful',
                'response': response.text,
                'model': self.model_name
            }
        except Exception as e:
            return {
                'success': False,
                'message': 'Failed to connect to Gemini API',
                'error': str(e)
            }
    
    def get_available_models(self) -> List[str]:
        """Get list of available Gemini models"""
        try:
            models = []
            for model in genai.list_models():
                if 'generateContent' in model.supported_generation_methods:
                    models.append(model.name)
            return models
        except Exception as e:
            print(f"Error fetching models: {e}")
            return ['gemini-1.5-flash', 'gemini-1.5-pro']  # Default fallback
    
    def create_school_context(self, tools_data: List[Dict]) -> str:
        """
        Create formatted context string from tools data for Gemini
        
        Args:
            tools_data: List of tool/resource dictionaries
            
        Returns:
            Formatted context string
        """
        if not tools_data:
            return "No specific resource information available at this time."
        
        context = "AVAILABLE SCHOOL RESOURCES:\n\n"
        
        # Group by category
        categories = {}
        for tool in tools_data:
            category = tool.get('category', 'Other')
            if category not in categories:
                categories[category] = []
            categories[category].append(tool)
        
        # Format by category
        for category, tools in categories.items():
            context += f"📂 {category.upper()}:\n"
            for tool in tools:
                context += f"  • {tool.get('name', 'Unknown Tool')}\n"
                context += f"    📍 Location: {tool.get('location', 'TBD')}\n"
                context += f"    ℹ️  {tool.get('description', 'No description available')}\n"
                context += f"    🕒 {tool.get('availability', 'Contact for availability')}\n"
                
                if tool.get('training_required', False):
                    context += f"    ⚠️  Training required - Contact: {tool.get('contact', 'See staff')}\n"
                else:
                    context += f"    📞 Contact: {tool.get('contact', 'See staff')}\n"
                context += "\n"
            context += "\n"
        
        return context

# Example usage and testing functions
def test_gemini_integration():
    """Test function to verify Gemini integration"""
    try:
        # Initialize chatbot
        chatbot = GeminiChatbot()
        
        # Test connection
        connection_test = chatbot.test_connection()
        print("Connection Test:", connection_test)
        
        if connection_test['success']:
            # Test a sample interaction
            sample_tools = [
                {
                    "name": "3D Printers (Bambu Lab X1C)",
                    "category": "Fabrication",
                    "location": "Maker Space - Room 101",
                    "description": "Three Bambu Lab X1C 3D printers for prototyping",
                    "availability": "9 AM - 5 PM",
                    "training_required": True,
                    "contact": "Dr. Smith - ext. 1234"
                }
            ]
            
            context = chatbot.create_school_context(sample_tools)
            
            response = chatbot.generate_response(
                "Where can I find 3D printers?",
                context=context,
                school_info={"name": "Tech University", "type": "University"}
            )
            
            print("Sample Response:", response)
        
        return connection_test['success']
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    test_gemini_integration()