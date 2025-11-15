"""
LLM API Wrapper for Agent Reasoning
Provides LLM reasoning capabilities for all agents
Supports both OpenAI and Gemini
"""

import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Try OpenAI first, fall back to Gemini
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False


class GeminiLLM:
    """
    Wrapper for LLM APIs (OpenAI or Gemini)
    Used by all agents for reasoning
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gpt-4o-mini",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize LLM

        Args:
            api_key: API key (if None, reads from env)
            model_name: Model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        """
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Determine which API to use
        openai_key = api_key or os.getenv('OPENAI_API_KEY')
        gemini_key = os.getenv('GEMINI_API_KEY')

        if openai_key and OPENAI_AVAILABLE:
            # Use OpenAI
            self.api_type = 'openai'
            self.client = OpenAI(api_key=openai_key)
            print(f"✓ OpenAI LLM initialized: {model_name}")
        elif gemini_key and GEMINI_AVAILABLE:
            # Use Gemini
            self.api_type = 'gemini'
            genai.configure(api_key=gemini_key)
            self.model = genai.GenerativeModel(
                model_name=model_name,
                generation_config={
                    'temperature': temperature,
                    'max_output_tokens': max_tokens,
                }
            )
            print(f"✓ Gemini LLM initialized: {model_name}")
        else:
            raise ValueError(
                "No LLM API available. Set OPENAI_API_KEY or GEMINI_API_KEY environment variable"
            )

    def generate(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True
    ) -> Dict[str, Any]:
        """
        Generate response from prompt

        Args:
            prompt: User prompt
            system_instruction: Optional system instruction
            json_mode: If True, expect JSON response

        Returns:
            Parsed JSON response (if json_mode) or text
        """
        try:
            if self.api_type == 'openai':
                return self._generate_openai(prompt, system_instruction, json_mode)
            else:
                return self._generate_gemini(prompt, system_instruction, json_mode)
        except Exception as e:
            print(f"Error generating response: {e}")
            return self._get_fallback_response(json_mode)

    def _generate_openai(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True
    ) -> Dict[str, Any]:
        """Generate response using OpenAI API"""

        messages = []

        # System instruction
        if system_instruction:
            messages.append({"role": "system", "content": system_instruction})
        else:
            messages.append({"role": "system", "content": "You are a helpful assistant that responds in JSON format."})

        # User prompt
        messages.append({"role": "user", "content": prompt})

        # Call OpenAI API
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
            response_format={"type": "json_object"} if json_mode else {"type": "text"}
        )

        # Extract text
        text = response.choices[0].message.content

        # Parse JSON if requested
        if json_mode:
            try:
                return json.loads(text)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parse failed: {e}")
                print(f"Response text: {text[:200]}...")
                return {"text": text, "parse_error": str(e)}
        else:
            return {"text": text}

    def _generate_gemini(
        self,
        prompt: str,
        system_instruction: Optional[str] = None,
        json_mode: bool = True
    ) -> Dict[str, Any]:
        """Generate response using Gemini API"""

        # Combine system instruction with prompt if provided
        full_prompt = prompt
        if system_instruction:
            full_prompt = f"{system_instruction}\n\n{prompt}"

        # Generate response
        response = self.model.generate_content(full_prompt)

        # Check if response has valid content
        if not response.parts:
            # Response was blocked or empty
            finish_reason = response.candidates[0].finish_reason if response.candidates else "UNKNOWN"
            print(f"Warning: Empty response (finish_reason: {finish_reason})")
            return self._get_fallback_response(json_mode)

        # Extract text
        text = response.text

        # Parse JSON if requested
        if json_mode:
            # Try to extract JSON from markdown code blocks
            if '```json' in text:
                json_start = text.find('```json') + 7
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            elif '```' in text:
                json_start = text.find('```') + 3
                json_end = text.find('```', json_start)
                json_text = text[json_start:json_end].strip()
            else:
                json_text = text.strip()

            try:
                return json.loads(json_text)
            except json.JSONDecodeError as e:
                print(f"Warning: JSON parse failed: {e}")
                print(f"Response text: {text[:200]}...")
                return {"text": text, "parse_error": str(e)}
        else:
            return {"text": text}

    def _get_fallback_response(self, json_mode: bool) -> Dict[str, Any]:
        """Generate fallback response when API fails"""
        if json_mode:
            return {
                "analysis": "API response unavailable, using fallback",
                "status": "NORMAL",
                "recommendation": "CONTINUE",
                "confidence": 0.5,
                "priority": "MEDIUM"
            }
        else:
            return {"text": "API response unavailable"}

    def generate_structured(
        self,
        prompt: str,
        expected_fields: list,
        system_instruction: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate structured response with expected fields

        Args:
            prompt: User prompt
            expected_fields: List of expected field names
            system_instruction: Optional system instruction

        Returns:
            Dict with expected fields
        """
        # Add field requirements to prompt
        enhanced_prompt = f"""{prompt}

IMPORTANT: Return your response as valid JSON with exactly these fields:
{json.dumps(expected_fields, indent=2)}

Do not include any text outside the JSON structure.
"""

        return self.generate(enhanced_prompt, system_instruction, json_mode=True)


# Global instance (lazy loaded)
_gemini_instance = None


def get_gemini_llm() -> GeminiLLM:
    """Get or create global LLM instance (OpenAI or Gemini)"""
    global _gemini_instance

    if _gemini_instance is None:
        # Get settings from environment
        model_name = os.getenv('LLM_MODEL', os.getenv('GEMINI_MODEL', 'gpt-4o-mini'))
        temperature = float(os.getenv('AGENT_TEMPERATURE', '0.7'))
        max_tokens = int(os.getenv('AGENT_MAX_TOKENS', '2048'))

        _gemini_instance = GeminiLLM(
            model_name=model_name,
            temperature=temperature,
            max_tokens=max_tokens
        )

    return _gemini_instance


if __name__ == "__main__":
    """Test Gemini wrapper"""

    print("="*60)
    print("Gemini API Wrapper - Testing")
    print("="*60)
    print()

    # Test API key
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        print("❌ GEMINI_API_KEY not set in environment")
        print("Please create a .env file with your API key:")
        print("GEMINI_API_KEY=your_key_here")
        exit(1)

    print(f"API Key found: {api_key[:20]}...")

    # Create LLM
    try:
        llm = GeminiLLM()

        # Test simple generation
        print("\n=== Test 1: Simple Generation ===")
        prompt = """
You are analyzing a wastewater pumping station.

Current situation:
- Water level: 3.5m
- Inflow: 850 m³/15min
- Electricity price: 5.2 EUR/kWh

Should we pump more water now or wait? Respond in JSON:
{
  "recommendation": "pump_now or wait",
  "reasoning": "explain why"
}
"""

        response = llm.generate(prompt, json_mode=True)
        print("Response:")
        print(json.dumps(response, indent=2))

        # Test structured generation
        print("\n=== Test 2: Structured Generation ===")
        prompt2 = "Analyze the wastewater system status"
        fields = ["status", "risk_level", "action_needed", "confidence"]

        response2 = llm.generate_structured(
            prompt2,
            expected_fields=fields,
            system_instruction="You are a water system expert."
        )
        print("Structured Response:")
        print(json.dumps(response2, indent=2))

        print("\n✓ Gemini wrapper tests passed!")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
