# 🎧 Ecoute - Real-time AI Copilot & Transcriber (Enhanced Fork)

> **Fork & Attribution Disclaimer**  
> This repository is an enhanced fork of the original open-source project **[Ecoute](https://github.com/SevaSk/ecoute)** created by **[Seva Skvortsov (@SevaSk)](https://github.com/SevaSk)** and **[Daniel Zarifpour (@zarifpour)](https://github.com/zarifpour)**.  
> All credit for the core concept, initial architecture, and base transcription engine belongs to the original authors. This fork introduces custom enhancements for real-time AI copilot responses, multi-provider LLM support, dynamic response modes, multilingual speech recognition with language selection, and secure environment configuration.

---

## What's New in this Enhanced Fork

- **Multi-Provider AI Copilot**: Native integration with **Groq** (`llama-3.3-70b-versatile`), **Gemini** (`gemini-flash-lite-latest`), and **OpenAI** (`gpt-4o-mini`).
- **Multilingual Speech Recognition & Speech Language Selector**: Upgraded local Whisper engine from English-only (`tiny.en`) to multilingual models (`base`). Added a live `Speech Language` dropdown in the UI (`Auto-Detect`, `Polish (pl)`, `English (en)`, `German (de)`, `Spanish (es)`, `French (fr)`, `Italian (it)`, `Ukrainian (uk)`).
- **Automatic Language Matching AI**: The AI Copilot detects the language of the conversation in real-time and generates suggestions in the **exact same language**.
- **Dynamic AI Response Modes**:
  - **`Manual Mode (Default)`**: AI suggestions fire strictly when clicking the `Generate Response Suggestion Now` button.
  - **`Automatic Mode`**: AI suggestions trigger automatically whenever the interlocutor (`Speaker`) finishes speaking.
- **Secure `.env` Secret Management**: All API keys are isolated in `.env` (ignored by Git) with a public `.env.example` template for safe GitHub deployment.
- **Python 3.13 / 3.14 Compatibility**: Fully compatible with PEP 594 Python releases using `audioop-lts`.

---

## Original Authors & Attribution

- **Original Repository**: [https://github.com/SevaSk/ecoute](https://github.com/SevaSk/ecoute)
- **Original Contributors**:
  - **Seva Skvortsov** ([@SevaSk](https://github.com/SevaSk))
  - **Daniel Zarifpour** ([@zarifpour](https://github.com/zarifpour))

---

## Core Features

- **Real-Time Dual Audio Transcription**: Captures microphone input (**You**) and system speaker audio (**Speaker**) simultaneously using `Faster-Whisper` or Cloud APIs.
- **Live AI Copilot**: Provides smart, context-aware response suggestions (1-3 sentences) tailored to the conversation history.
- **Modern Dark Interface**: CustomTkinter dark GUI with dedicated live transcript, settings bar, and response suggestion panels.

---

## 🚀 Getting Started

### 📋 Prerequisites

- **Python**: 3.10 to 3.13+
- **FFmpeg**: Installed on your system and added to PATH (or installed via WinGet `winget install FFmpeg`).
- **NVIDIA GPU (Optional)**: CUDA-enabled GPU for faster local Whisper transcription.

### 📥 Installation

#### Option 1: Download Standalone Executable (Recommended)

You can download the pre-compiled, standalone Windows executable directly from GitHub Releases. No Python or command-line experience required!

1. Go to the [Releases](https://github.com/piotr4256/ecoute-ai-copilot/releases) page.
2. Download the latest `Ecoute-AI-Copilot.exe`.
3. Double-click the `.exe` to run the application.
4. On first startup, a window will pop up asking for your API Key. Enter your Groq/Gemini key, and you're ready to go! The key is saved securely in your Windows AppData folder and can be edited anytime via the `🔑 API Keys` button in the app.

#### Option 2: Build from Source (For Developers)

1. **Clone your fork**:
   ```bash
   git clone https://github.com/piotr4256/ecoute-ai-copilot.git
   cd ecoute-ai-copilot
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment Variables (`.env`)**:
   Copy `.env.example` to `.env` and enter your API keys:
   ```bash
   cp .env.example .env
   ```

   Edit `.env`:
   ```env
   GROQ_API_KEY=gsk_your_actual_groq_api_key_here
   GEMINI_API_KEY=your_gemini_api_key_here
   OPENAI_API_KEY=your_openai_api_key_here
   ```

---

## 🏃 Running the Application

### 1. Standard Local Execution (Recommended - Groq AI + Local Multilingual Whisper)
```bash
python main.py
```

### 2. Cloud Whisper API Mode
```bash
python main.py --api
```

### 3. Gemini Audio Model Mode
```bash
python main.py --gemini
```

---

## 🔒 Security Notice

The `.env` file is excluded from Git version control via `.gitignore`. Never commit your real API keys to public repositories!

---

## 📄 License

This project carries the license of the original [Ecoute](https://github.com/SevaSk/ecoute) repository.
