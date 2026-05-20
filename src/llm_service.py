import os
import httpx
from jinja2 import Environment, FileSystemLoader

env = Environment(loader=FileSystemLoader('templates'))
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

async def generate_text(prompt: str) -> str:
    model = os.getenv("OLLAMA_MODEL", "mistral:7b")
    endpoints = [
        "/api/generate",
        "/v1/generate",
        "/v1/completions",
        "/api/completions",
        "/v1/chat/completions",
        "/openai/v1/chat/completions",
        "/v1/complete",
    ]

    # Try several payload shapes (ollama native, openai-compatible, simple)
    payloads = [
        {"model": model, "prompt": prompt, "stream": False},
        {"model": model, "input": prompt, "stream": False},
        {"model": model, "messages": [{"role": "user", "content": prompt}]},
        {"model": model, "prompt": [{"role": "user", "content": prompt}]},
    ]

    async with httpx.AsyncClient(timeout=120.0) as client:
        for ep in endpoints:
            full_url = OLLAMA_BASE_URL.rstrip("/") + ep
            for payload in payloads:
                try:
                    resp = await client.post(full_url, json=payload)
                except Exception as e:
                    # Couldn't connect or other transport error; try next
                    # print(f"Attempt to {full_url} failed: {e}")
                    continue

                if resp.status_code != 200:
                    # Try next payload/endpoint
                    # print(f"{full_url} returned {resp.status_code}")
                    continue

                try:
                    data = resp.json()
                except Exception:
                    text = resp.text or ""
                    if text:
                        return text.strip()
                    continue

                # Common response shapes
                # 1) Ollama older: {"response": "..."}
                if isinstance(data, dict):
                    if "response" in data and isinstance(data["response"], str):
                        return data["response"].strip()

                    # 2) OpenAI-like: {"choices": [{"message": {"content": "..."}}]} or {"choices":[{"text":"..."}]}
                    if "choices" in data and isinstance(data["choices"], list) and len(data["choices"]) > 0:
                        choice = data["choices"][0]
                        if isinstance(choice, dict):
                            # message.content
                            msg = choice.get("message") or choice.get("delta")
                            if isinstance(msg, dict) and "content" in msg:
                                return msg["content"].strip()
                            if "text" in choice:
                                return choice.get("text", "").strip()

                    # 3) Some APIs return {"output": [{"content":["..."]}]}
                    if "output" in data and isinstance(data["output"], list) and len(data["output"]) > 0:
                        out0 = data["output"][0]
                        if isinstance(out0, dict):
                            # nested content
                            content = out0.get("content")
                            if isinstance(content, list) and len(content) > 0:
                                return "\n".join([str(c) for c in content]).strip()
                            if isinstance(content, str):
                                return content.strip()

                # If we get here, unable to parse; return raw text if present
                txt = resp.text
                if txt:
                    return txt.strip()

    print("Error calling Ollama: no working endpoint found or all endpoints failed")
    return "Could not generate content at this time."

async def generate_newsletter_section(template_name: str, **kwargs) -> str:
    template = env.get_template(f"{template_name}.j2")
    prompt = template.render(**kwargs)
    text = await generate_text(prompt)
    # If the LLM failed or returned a placeholder, provide a deterministic fallback
    if not text or text.strip() == "Could not generate content at this time.":
        # Build simple, safe summaries so the newsletter can be generated even when Ollama isn't available
        try:
            if template_name == "events":
                events = kwargs.get('events', [])
                if not events:
                    return "No upcoming events."
                lines = []
                for e in events:
                    date = e.get('event_date', '')
                    name = e.get('name', '')
                    desc = e.get('description', '')
                    lines.append(f"- {name} on {date}: {desc}")
                return "\n".join(lines)

            if template_name == "courses":
                courses = kwargs.get('courses', [])
                if not courses:
                    return "No course reminders."
                lines = []
                for c in courses:
                    name = c.get('name', '')
                    reminder = c.get('reminder', '')
                    due = c.get('due_date', '')
                    lines.append(f"- {name}: {reminder} (Due: {due})")
                return "\n".join(lines)

            if template_name == "weather":
                weather = kwargs.get('weather', [])
                if not weather:
                    return "Weather data unavailable."
                lines = []
                for w in weather:
                    d = w.get('date', '')
                    t = w.get('temp', '')
                    cnd = w.get('condition', '')
                    lines.append(f"- {d}: {t}°C, {cnd}")
                return "\n".join(lines)

        except Exception:
            return "Could not generate content at this time."

    return text
