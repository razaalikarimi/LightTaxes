"""
LLM Engine - Unified interface for multiple LLM providers
Supports OpenAI, Anthropic (Claude), Google (Gemini), and Mock mode
"""

import os
from typing import Optional, Dict, List, Any
from enum import Enum
import openai
import anthropic
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()


class LLMProvider(str, Enum):
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GOOGLE = "google"
    MOCK = "mock"


class LLMEngine:
    """Unified LLM interface for tax agent system"""
    
    def __init__(
        self, 
        provider: Optional[str] = None,
        model: Optional[str] = None,
        temperature: float = 0.1,
        max_tokens: int = 4096
    ):
        self.provider = provider or os.getenv("DEFAULT_LLM", "openai")
        self.temperature = temperature or float(os.getenv("LLM_TEMPERATURE", "0.1"))
        self.max_tokens = max_tokens or int(os.getenv("LLM_MAX_TOKENS", "4096"))
        
        # Set model based on provider
        if model:
            self.model = model
        elif self.provider == "openai":
            self.model = os.getenv("OPENAI_MODEL", "gpt-4-turbo-preview")
        elif self.provider == "anthropic":
            self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        elif self.provider == "google":
            self.model = os.getenv("GOOGLE_MODEL", "gemini-1.5-pro")
        elif self.provider == "mock":
            self.model = "mock-model"
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the appropriate LLM client"""
        if self.provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not found in environment")
            self.client = openai.OpenAI(api_key=api_key)
            
        elif self.provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not found in environment")
            self.client = anthropic.Anthropic(api_key=api_key)
            
        elif self.provider == "google":
            api_key = os.getenv("GOOGLE_API_KEY")
            if not api_key:
                raise ValueError("GOOGLE_API_KEY not found in environment")
            genai.configure(api_key=api_key)
            self.client = genai.GenerativeModel(self.model)
            
        elif self.provider == "mock":
            # No client needed for mock
            self.client = None
            
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def generate(
        self, 
        prompt: str, 
        system_prompt: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None
    ) -> str:
        """
        Generate completion from LLM
        
        Args:
            prompt: User prompt
            system_prompt: System instructions
            temperature: Override default temperature
            max_tokens: Override default max tokens
            
        Returns:
            Generated text response
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens
        
        if self.provider == "openai":
            return self._generate_openai(prompt, system_prompt, temp, tokens)
        elif self.provider == "anthropic":
            return self._generate_anthropic(prompt, system_prompt, temp, tokens)
        elif self.provider == "google":
            return self._generate_google(prompt, system_prompt, temp, tokens)
        elif self.provider == "mock":
            return self._generate_mock(prompt, system_prompt, temp, tokens)
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def _generate_openai(
        self, 
        prompt: str, 
        system_prompt: Optional[str], 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate using OpenAI API"""
        messages = []
        
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        messages.append({"role": "user", "content": prompt})
        
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        return response.choices[0].message.content
    
    def _generate_anthropic(
        self, 
        prompt: str, 
        system_prompt: Optional[str], 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate using Anthropic Claude API"""
        kwargs = {
            "model": self.model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        if system_prompt:
            kwargs["system"] = system_prompt
        
        response = self.client.messages.create(**kwargs)
        
        return response.content[0].text
    
    def _generate_google(
        self, 
        prompt: str, 
        system_prompt: Optional[str], 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate using Google Gemini API"""
        # Combine system prompt and user prompt for Gemini
        full_prompt = prompt
        if system_prompt:
            full_prompt = f"{system_prompt}\n\n{prompt}"
        
        generation_config = genai.types.GenerationConfig(
            temperature=temperature,
            max_output_tokens=max_tokens
        )
        
        response = self.client.generate_content(
            full_prompt,
            generation_config=generation_config
        )
        
        return response.text
    
    def _generate_mock(
        self, 
        prompt: str, 
        system_prompt: Optional[str], 
        temperature: float, 
        max_tokens: int
    ) -> str:
        """Generate simulated responses for testing/demo purposes"""
        prompt_lower = prompt.lower()
        
        # Return generic low number to be safe, or specific if detected
        if "wages" in prompt_lower or "line 1z" in prompt_lower:
            # Try to extract from context if available, otherwise default
            return "50000"
        elif "interest" in prompt_lower or "line 2b" in prompt_lower:
            return "0"
        elif "dividends" in prompt_lower:
            return "0"
        elif "adjustments" in prompt_lower or "line 10" in prompt_lower:
            return "0"
        elif "deduction" in prompt_lower:
            # Deterministic tool should handle this, but if LLM asked:
            return "14600"
        elif "line 15" in prompt_lower: # Taxable income
            return "35400"
        elif "tax" in prompt_lower and "line 16" in prompt_lower:
            return "4027"
        elif "child tax credit" in prompt_lower:
            return "0"
        elif "withheld" in prompt_lower or "line 25a" in prompt_lower:
            return "5000"
        else:
            return "0"
    
    def generate_structured(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        schema: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate structured JSON output"""
        import json
        
        if self.provider == "mock":
            # Return dummy JSON for mock mode
            return {"status": "success", "mock_data": True}
        
        # Add JSON instruction to prompt
        json_prompt = f"""{prompt}

Please respond with valid JSON only. No additional text or markdown.
"""
        
        response = self.generate(json_prompt, system_prompt)
        
        # Try to extract JSON from response
        try:
            # Remove markdown code blocks if present
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0].strip()
            elif "```" in response:
                response = response.split("```")[1].split("```")[0].strip()
            
            return json.loads(response)
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON from LLM response: {e}\n\nResponse: {response}")


# Convenience function for quick usage
def create_llm(
    provider: Optional[str] = None,
    model: Optional[str] = None,
    **kwargs
) -> LLMEngine:
    """Create LLM engine with optional overrides"""
    return LLMEngine(provider=provider, model=model, **kwargs)
