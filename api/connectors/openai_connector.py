import os
import openai
from dotenv import load_dotenv

load_dotenv()


class OpenAIConnector:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")

    def complete(self, prompt: str, model: str = "gpt-4-turbo") -> dict:
        try:
            response = openai.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Tu fais partie du système Zéro Obstacle Canada."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=1500,
            )
            content = response.choices[0].message.content.strip()
            return {"status": "success", "result": content}
        except Exception as e:
            return {"status": "error", "error": str(e)}
