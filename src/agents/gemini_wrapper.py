"""
Gemini API Wrapper for Agent Reasoning
Provides LLM reasoning capabilities for all agents
"""

import google.generativeai as genai
import json
import os
from typing import Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class GeminiLLM:
    """
    Wrapper for Google Gemini API
    Used by all agents for reasoning
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-pro",
        temperature: float = 0.7,
        max_tokens: int = 2048
    ):
        """
        Initialize Gemini LLM

        Args:
            api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            model_name: Model to use
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens in response
        """
        # Get API key
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        if not self.api_key:
            raise ValueError(
                "Gemini API key not found. Set GEMINI_API_KEY environment variable "
                "or pass api_key parameter"
            )

        # Configure Gemini
        genai.configure(api_key=self.api_key)

        # Model configuration
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create model
        self.model = genai.GenerativeModel(
            model_name=model_name,
            generation_config={
                'temperature': temperature,
                'max_output_tokens': max_tokens,
            }
        )

        print(f"✓ Gemini LLM initialized: {model_name}")

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
            # Combine system instruction with prompt if provided
            full_prompt = prompt
            if system_instruction:
                full_prompt = f"{system_instruction}\n\n{prompt}"

            # Generate response
            response = self.model.generate_content(full_prompt)

            # Extract text
            text = response.text

            # Parse JSON if requested
            if json_mode:
                # Try to extract JSON from markdown code blocks
                if '```json' in text:
                    # Extract content between ```json and ```
                    json_start = text.find('```json') + 7
                    json_end = text.find('```', json_start)
                    json_text = text[json_start:json_end].strip()
                elif '```' in text:
                    # Extract content between ``` and ```
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
                    # Return as dict with text
                    return {"text": text, "parse_error": str(e)}
            else:
                return {"text": text}

        except Exception as e:
            print(f"Error generating response: {e}")
            return {"error": str(e), "text": ""}

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
    """Get or create global Gemini LLM instance"""
    global _gemini_instance

    if _gemini_instance is None:
        # Get settings from environment
        model_name = os.getenv('GEMINI_MODEL', 'gemini-1.5-pro')
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
