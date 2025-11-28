from pydantic import BaseModel, Field
from openai import OpenAI
import anthropic
from google import genai


class LLMClient:
    class LLMResponse(BaseModel):
        rating: int = Field(description="Rating score assigned by the LLM judge")
        explanation: str = Field(description="Explanation provided by the LLM judge for the rating")
        
    def __init__(self, judge_model: str, api_key: str):
        self.model = judge_model
        self.api_key = api_key

        # Extract provider from model name (format: provider/model_name)
        if '/' in judge_model:
            self.model_provider = judge_model.split('/')[0]
            self.model_name = judge_model.split('/')[1]
        else:
            self.model_provider = "unknown"
            self.model_name = judge_model

        if self.model_provider == "openai":
            try: 
                self.client = OpenAI(api_key=self.api_key)
                print("Client initialized: OpenAI")
            except Exception as e:
                raise ValueError(f"Failed to initialize OpenAI client: {e}")

        elif self.model_provider == "anthropic":
            try:
                self.client = anthropic.Anthropic(api_key=self.api_key)
                print("Client initialized: Anthropic")
            except Exception as e:
                raise ValueError(f"Failed to initialize Anthropic client: {e}")

        elif self.model_provider == "google":
            try:
                self.client = genai.Client(api_key=self.api_key)
                print("Client initialized: Google Gemini")
            except Exception as e:
                raise ValueError(f"Failed to initialize Google client: {e}")
        
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")


    def generate(self, prompt: str) -> str:
        if self.model_provider == "openai":
            response = self.client.beta.chat.completions.parse(
                model=self.model_name,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                text_format=self.LLMResponse,
            )
            return response.output_parsed
        
        elif self.model_provider == "anthropic":
            response = self.client.beta.messages.create(
                model=self.model_name,
                betas = ["structured-outputs-2025-11-13"],
                messages=[
                    {"role": "user", "content": prompt}
                ],
                output_format={
                    "type": "json_schema",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "rating": {"type": "integer"},
                            "explanation": {"type": "string"}
                        },
                        "required": ["rating", "explanation"],
                        "additionalProperties": False
                    }
                }
            )
            return response.content[0].text
        
        elif self.model_provider == "google":
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config={
                    "response_mime_type": "application/json",
                    "response_json_schema": self.LLMResponse.model_json_schema(),
                }
            )
            return self.LLMResponse.model_validate_json(response.text)
        
        else:
            raise ValueError(f"Unsupported model provider: {self.model_provider}")