import torch
from faster_whisper import WhisperModel
from openai import OpenAI
import os
import json
import base64
import urllib.request

# Try to load keys from keys.py if available
try:
    import keys
    if hasattr(keys, "OPENAI_API_KEY"):
        os.environ.setdefault("OPENAI_API_KEY", keys.OPENAI_API_KEY)
    if hasattr(keys, "GEMINI_API_KEY"):
        os.environ.setdefault("GEMINI_API_KEY", keys.GEMINI_API_KEY)
except ImportError:
    pass

def get_model(use_api=False, use_gemini=False):
    """Factory function to instantiate the selected transcription model."""
    if use_gemini or (use_api and (os.environ.get("GEMINI_API_KEY") or (os.environ.get("OPENAI_API_KEY", "").startswith("AIza")))):
        return GeminiTranscriber()
    elif use_api:
        return APIWhisperTranscriber()
    else:
        return FasterWhisperTranscriber()

class FasterWhisperTranscriber:
    """Local multilingual Whisper transcriber using faster-whisper.
    Default model is 'base' (multilingual) which supports Polish, English, German, etc.
    """
    def __init__(self, model_name=None):
        model_name = model_name or os.environ.get("WHISPER_MODEL", "base")
        print(f"[INFO] Loading Faster Whisper multilingual model ('{model_name}')...")
        self.model = WhisperModel(
            model_name, 
            device="cuda" if torch.cuda.is_available() else "cpu", 
            compute_type="float32" if torch.cuda.is_available() else "int8"
        )
        print(f"[INFO] Faster Whisper loaded successfully (GPU Acceleration: {torch.cuda.is_available()})")

    def get_transcription(self, wav_file_path, language=None):
        try:
            # If language is 'auto' or None, Whisper automatically detects the spoken language
            lang_param = None if (not language or language == "auto") else language
            segments, _ = self.model.transcribe(wav_file_path, beam_size=5, language=lang_param)
            full_text = " ".join(segment.text for segment in segments)
            return full_text.strip()
        except Exception as e:
            print(f"[Whisper Error]: {e}")
            return ''

class APIWhisperTranscriber:
    """Cloud OpenAI Whisper API transcriber."""
    def __init__(self, api_key=None):
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        self.client = OpenAI(api_key=api_key)
    
    def get_transcription(self, wav_file_path, language=None):
        try:
            lang_param = None if (not language or language == "auto") else language
            with open(wav_file_path, "rb") as audio_file:
                kwargs = {"model": "whisper-1", "file": audio_file}
                if lang_param:
                    kwargs["language"] = lang_param
                result = self.client.audio.transcriptions.create(**kwargs)
            return result.text.strip()
        except Exception as e:
            print(f"[OpenAI Whisper Error]: {e}")
            return ''

class GeminiTranscriber:
    """Google Gemini Audio Transcriber using direct REST API."""
    def __init__(self, api_key=None, model_name=None):
        self.api_key = api_key or os.environ.get("GEMINI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        self.model_name = model_name or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash-lite")
        try:
            import keys
            if hasattr(keys, "GEMINI_MODEL") and keys.GEMINI_MODEL:
                self.model_name = keys.GEMINI_MODEL
        except Exception:
            pass
        print(f"[INFO] Initialized Gemini Audio Transcriber (Model: {self.model_name})")

    def get_transcription(self, wav_file_path, language=None):
        if not self.api_key:
            print("[Gemini Error] No GEMINI_API_KEY or OPENAI_API_KEY found.")
            return ''
        try:
            with open(wav_file_path, "rb") as audio_file:
                audio_bytes = audio_file.read()
            
            b64_audio = base64.b64encode(audio_bytes).decode('utf-8')
            
            prompt = "Transcribe the spoken audio in this recording accurately."
            if language and language != "auto":
                prompt += f" The language spoken is '{language}'."
            prompt += " Return ONLY the raw transcribed text."

            url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{
                    "parts": [
                        {
                            "inline_data": {
                                "mime_type": "audio/wav",
                                "data": b64_audio
                            }
                        },
                        {
                            "text": prompt
                        }
                    ]
                }],
                "generationConfig": {
                    "temperature": 0.0
                }
            }
            
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'}
            )
            
            with urllib.request.urlopen(req) as resp:
                result = json.loads(resp.read().decode('utf-8'))
                
            text = result['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
        except Exception as e:
            print(f"[Gemini Transcribe Error]: {e}")
            return ''