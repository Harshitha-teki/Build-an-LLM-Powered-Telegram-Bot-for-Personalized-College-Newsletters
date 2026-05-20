import os
import httpx
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

async def generate_text(prompt: str) -> str:
    url = f"{OLLAMA_BASE_URL}/api/generate"
    payload = {
        "model": "llama3.1:8b",
        "prompt": prompt,
        "stream": False
    }
    try:
        # Generous timeout for local inference
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("response", "").strip()
    except Exception as e:
        print(f"Error calling Ollama: {e}")
        return "Could not generate content at this time."

async def generate_newsletter_section(template_name: str, **kwargs) -> str:
    template = env.get_template(f"{template_name}.j2")
    prompt = template.render(**kwargs)
    return await generate_text(prompt)
