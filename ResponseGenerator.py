import os
import json
import urllib.request
import urllib.error
import threading
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

class GeminiResponseGenerator:
    def __init__(self, api_key=None):
        self.api_key = api_key
        self.groq_api_key = None
        self.gemini_api_key = None
        self.openai_api_key = None
        self.last_suggestion = ""
        self.is_generating = False
        self.provider = None
        self.refresh_key()

    def refresh_key(self):
        self.model_name = os.getenv("GEMINI_MODEL", "gemini-flash-lite-latest")
        self.groq_model = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")
        
        try:
            import keys
            self.groq_api_key = getattr(keys, "GROQ_API_KEY", None) or os.getenv("GROQ_API_KEY")
            self.gemini_api_key = getattr(keys, "GEMINI_API_KEY", None) or os.getenv("GEMINI_API_KEY")
            self.openai_api_key = getattr(keys, "OPENAI_API_KEY", None) or os.getenv("OPENAI_API_KEY")
        except Exception:
            self.groq_api_key = os.getenv("GROQ_API_KEY")
            self.gemini_api_key = os.getenv("GEMINI_API_KEY")
            self.openai_api_key = os.getenv("OPENAI_API_KEY")

        # Determine active AI provider (Groq > Gemini > OpenAI)
        if self.groq_api_key and "YOUR_KEY" not in self.groq_api_key and self.groq_api_key.strip():
            self.provider = "groq"
            self.api_key = self.groq_api_key.strip()
        elif self.gemini_api_key and "YOUR_KEY" not in self.gemini_api_key and self.gemini_api_key.strip():
            self.provider = "gemini"
            self.api_key = self.gemini_api_key.strip()
        elif self.openai_api_key and "YOUR_KEY" not in self.openai_api_key and self.openai_api_key.strip():
            self.provider = "openai"
            self.api_key = self.openai_api_key.strip()
        else:
            self.provider = None
            self.api_key = None

    def generate_suggestion_async(self, transcript_text, callback=None):
        self.refresh_key()
        if not self.provider or not self.api_key:
            msg = "⚠️ Missing API Key! Please configure GROQ_API_KEY or GEMINI_API_KEY in the .env file."
            self.last_suggestion = msg
            if callback:
                callback(msg)
            return

        if self.is_generating:
            return

        def _worker():
            self.is_generating = True
            try:
                prompt_system = (
                    "You are a real-time AI copilot assistant for a live interview or conversation.\n"
                    "CRITICAL REQUIREMENT: You MUST detect the language of the conversation transcript provided by the user and write your suggested response in the EXACT SAME LANGUAGE as the conversation.\n"
                    "- If the conversation is in English -> reply ONLY in English.\n"
                    "- If the conversation is in Polish -> reply ONLY in Polish.\n"
                    "- If in German -> reply ONLY in German, etc.\n"
                    "Analyze the entire transcript (You = User, Speaker = Interlocutor) and generate a concise, direct, natural response (1-3 sentences) for 'You' to say next."
                )
                
                prompt_user = (
                    "==================== LIVE CONVERSATION TRANSCRIPT ====================\n"
                    f"{transcript_text}\n"
                    "======================================================================\n\n"
                    "Provide a concise 1-3 sentence suggested response for 'You' in the EXACT SAME LANGUAGE as the transcript above:"
                )

                headers = {
                    "Content-Type": "application/json",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                }

                if self.provider == "groq":
                    url = "https://api.groq.com/openai/v1/chat/completions"
                    payload = {
                        "model": self.groq_model,
                        "messages": [
                            {"role": "system", "content": prompt_system},
                            {"role": "user", "content": prompt_user}
                        ],
                        "temperature": 0.7
                    }
                    headers["Authorization"] = f"Bearer {self.api_key}"
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                    with urllib.request.urlopen(req) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                    suggestion = res['choices'][0]['message']['content'].strip()

                elif self.provider == "openai":
                    url = "https://api.openai.com/v1/chat/completions"
                    payload = {
                        "model": "gpt-4o-mini",
                        "messages": [
                            {"role": "system", "content": prompt_system},
                            {"role": "user", "content": prompt_user}
                        ],
                        "temperature": 0.7
                    }
                    headers["Authorization"] = f"Bearer {self.api_key}"
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                    with urllib.request.urlopen(req) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                    suggestion = res['choices'][0]['message']['content'].strip()

                else: # Gemini
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
                    payload = {
                        "contents": [{
                            "parts": [{"text": f"{prompt_system}\n\n{prompt_user}"}]
                        }],
                        "generationConfig": {"temperature": 0.7}
                    }
                    req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers=headers)
                    with urllib.request.urlopen(req) as resp:
                        res = json.loads(resp.read().decode('utf-8'))
                    suggestion = res['candidates'][0]['content']['parts'][0]['text'].strip()

                self.last_suggestion = suggestion
                if callback:
                    callback(suggestion)

            except urllib.error.HTTPError as e:
                err_body = e.read().decode('utf-8', errors='ignore')
                if e.code == 404:
                    err_msg = f"❌ Error 404: Selected AI model is unavailable in {self.provider.upper()} API. Please check your .env configuration."
                elif e.code == 429:
                    err_msg = f"⚠️ Error 429 (Rate Limit / Quota Exceeded): Rate limit reached for {self.provider.upper()} API.\nPlease configure GROQ_API_KEY in .env for free ultrafast responses (https://console.groq.com)."
                else:
                    err_msg = f"HTTP Error {e.code}: {err_body}"
                print(f"[{self.provider.upper()} Error HTTP {e.code}]: {err_body}")
                self.last_suggestion = err_msg
                if callback:
                    callback(err_msg)
            except Exception as e:
                err_msg = f"Error generating suggestion: {e}"
                print(f"[Response Generator Error]: {e}")
                self.last_suggestion = err_msg
                if callback:
                    callback(err_msg)
            finally:
                self.is_generating = False

        threading.Thread(target=_worker, daemon=True).start()
