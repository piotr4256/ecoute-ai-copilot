import threading
import customtkinter as ctk
import queue
import time
import sys
import os
import subprocess
from dotenv import load_dotenv

import AudioRecorder 
import TranscriberModels
from AudioTranscriber import AudioTranscriber
from ResponseGenerator import GeminiResponseGenerator

# Load environment variables from .env
load_dotenv()

def write_in_textbox(textbox, text):
    """Utility function to replace content in a CustomTkinter Textbox."""
    textbox.delete("0.0", "end")
    textbox.insert("0.0", text)

def update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, response_generator, trigger_func, response_mode_var):
    """Periodically refreshes the live transcript box and handles auto-generation if enabled."""
    transcript_string = transcriber.get_transcript()
    write_in_textbox(transcript_textbox, transcript_string)

    # Check if Automatic mode is selected and Speaker just spoke
    if response_mode_var.get() == "auto":
        if transcriber.check_and_reset_speaker_spoke():
            trigger_func()
    else:
        # Clear speaker spoke flag in manual mode
        transcriber.check_and_reset_speaker_spoke()

    transcript_textbox.after(300, update_transcript_UI, transcriber, transcript_textbox, suggestion_textbox, response_generator, trigger_func, response_mode_var)

def clear_context(transcriber, speaker_queue, mic_queue, suggestion_textbox):
    """Clears transcript history and flushes audio queues."""
    transcriber.clear_transcript_data()

    with speaker_queue.mutex:
        speaker_queue.queue.clear()
    with mic_queue.mutex:
        mic_queue.queue.clear()
        
    write_in_textbox(suggestion_textbox, "Conversation history cleared.")

def create_ui_components(root, transcriber, speaker_queue, mic_queue, response_generator):
    """Initializes CustomTkinter UI components with full English interface, mode selector & speech language menu."""
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("dark-blue")
    root.title("Ecoute - Real-time AI Copilot & Transcriber")
    root.geometry("1150x800")

    root.grid_columnconfigure(0, weight=1)
    root.grid_rowconfigure(0, weight=1)
    
    main_frame = ctk.CTkFrame(root)
    main_frame.grid(row=0, column=0, sticky="nsew", padx=15, pady=15)
    
    main_frame.grid_columnconfigure(0, weight=1)
    main_frame.grid_rowconfigure(1, weight=3)  # Transcript box
    main_frame.grid_rowconfigure(5, weight=1)  # Suggestion box

    # --- Section 1: Transcript ---
    t1_label = ctk.CTkLabel(main_frame, text="🎙️ Live Conversation Transcript (You / Speaker)", font=("Arial", 16, "bold"))
    t1_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 2))

    transcript_textbox = ctk.CTkTextbox(
        main_frame, 
        font=("Arial", 18), 
        text_color='#FFFCF2', 
        wrap="word"
    )
    transcript_textbox.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)

    clear_button = ctk.CTkButton(
        main_frame, 
        text="🗑️ Clear Transcript", 
        command=lambda: clear_context(transcriber, speaker_queue, mic_queue, suggestion_textbox)
    )
    clear_button.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

    # --- Section 2: Settings Bar (Mode Switch + Speech Language Dropdown) ---
    settings_frame = ctk.CTkFrame(main_frame, fg_color="#181825")
    settings_frame.grid(row=3, column=0, sticky="ew", padx=10, pady=(5, 5))
    settings_frame.grid_columnconfigure(1, weight=1)
    settings_frame.grid_columnconfigure(3, weight=1)

    # Mode Selector
    mode_label = ctk.CTkLabel(settings_frame, text="⚙️ AI Mode:", font=("Arial", 13, "bold"), text_color="#A6ADC8")
    mode_label.grid(row=0, column=0, padx=(10, 5), pady=8, sticky="w")

    response_mode_var = ctk.StringVar(value="manual")

    mode_segmented_button = ctk.CTkSegmentedButton(
        settings_frame,
        values=["Manual (Button)", "Automatic (Speech)"],
        command=lambda selected: response_mode_var.set("auto" if "Automatic" in selected else "manual"),
        font=("Arial", 12, "bold")
    )
    mode_segmented_button.set("Manual (Button)")
    mode_segmented_button.grid(row=0, column=1, padx=(0, 15), pady=8, sticky="w")

    # Speech Language Selector
    lang_label = ctk.CTkLabel(settings_frame, text="🌐 Speech Language:", font=("Arial", 13, "bold"), text_color="#A6ADC8")
    lang_label.grid(row=0, column=2, padx=(10, 5), pady=8, sticky="w")

    LANG_MAP = {
        "Auto-Detect": "auto",
        "Polish (pl)": "pl",
        "English (en)": "en",
        "German (de)": "de",
        "Spanish (es)": "es",
        "French (fr)": "fr",
        "Italian (it)": "it",
        "Ukrainian (uk)": "uk"
    }

    def on_language_change(choice):
        lang_code = LANG_MAP.get(choice, "auto")
        transcriber.set_language(lang_code)

    lang_option_menu = ctk.CTkOptionMenu(
        settings_frame,
        values=list(LANG_MAP.keys()),
        command=on_language_change,
        font=("Arial", 12, "bold"),
        fg_color="#313244",
        button_color="#45475A",
        button_hover_color="#585B70"
    )
    lang_option_menu.set("Auto-Detect")
    lang_option_menu.grid(row=0, column=3, padx=(0, 10), pady=8, sticky="e")

    # --- Section 3: AI Suggestions ---
    t2_label = ctk.CTkLabel(main_frame, text="💡 AI Copilot Response Suggestion", font=("Arial", 16, "bold"), text_color="#4CC9F0")
    t2_label.grid(row=4, column=0, sticky="w", padx=10, pady=(5, 2))

    suggestion_textbox = ctk.CTkTextbox(
        main_frame,
        font=("Arial", 16),
        text_color='#E0E1DD',
        fg_color="#1E1E2E",
        wrap="word",
        height=130
    )
    suggestion_textbox.grid(row=5, column=0, sticky="nsew", padx=10, pady=5)
    suggestion_textbox.insert("0.0", "Waiting for conversation... (Click 'Generate Response Suggestion Now' or switch Mode to Automatic)")

    def trigger_suggestion():
        current_transcript = transcriber.get_transcript()
        if not current_transcript.strip():
            write_in_textbox(suggestion_textbox, "No transcript available in conversation history.")
            return
        
        write_in_textbox(suggestion_textbox, "⏳ Generating response suggestion via AI Copilot...")
        
        def update_ui(sugg_text):
            root.after(0, lambda: write_in_textbox(suggestion_textbox, sugg_text))
            
        response_generator.generate_suggestion_async(current_transcript, callback=update_ui)

    suggest_button = ctk.CTkButton(
        main_frame,
        text="✨ Generate Response Suggestion Now",
        fg_color="#3A0CA3",
        hover_color="#4361EE",
        font=("Arial", 15, "bold"),
        command=trigger_suggestion
    )
    suggest_button.grid(row=6, column=0, sticky="ew", padx=10, pady=(0, 10))

    return transcript_textbox, suggestion_textbox, trigger_suggestion, response_mode_var

def main():
    # Ensure FFmpeg binary is found in PATH if installed via WinGet or custom directory
    try:
        subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except FileNotFoundError:
        winget_ffmpeg = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0-full_build\bin")
        if os.path.exists(winget_ffmpeg):
            os.environ["PATH"] += os.path.pathsep + winget_ffmpeg
        try:
            subprocess.run(["ffmpeg", "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except FileNotFoundError:
            print("ERROR: The FFmpeg library is not installed. Please install FFmpeg and try again.")
            return

    root = ctk.CTk()
    speaker_queue = queue.Queue()
    mic_queue = queue.Queue()

    response_generator = GeminiResponseGenerator()

    user_audio_recorder = AudioRecorder.DefaultMicRecorder()
    user_audio_recorder.record_into_queue(mic_queue)

    time.sleep(2)

    speaker_audio_recorder = AudioRecorder.DefaultSpeakerRecorder()
    speaker_audio_recorder.record_into_queue(speaker_queue)

    use_api = '--api' in sys.argv
    use_gemini = '--gemini' in sys.argv
    model = TranscriberModels.get_model(use_api=use_api, use_gemini=use_gemini)

    transcriber = AudioTranscriber(user_audio_recorder.source, speaker_audio_recorder.source, model)
    transcribe = threading.Thread(target=transcriber.transcribe_audio_queue, args=(speaker_queue, mic_queue))
    transcribe.daemon = True
    transcribe.start()

    transcript_textbox, suggestion_textbox, trigger_func, response_mode_var = create_ui_components(
        root, transcriber, speaker_queue, mic_queue, response_generator
    )

    print("READY")

    update_transcript_UI(transcriber, transcript_textbox, suggestion_textbox, response_generator, trigger_func, response_mode_var)

    root.mainloop()

if __name__ == "__main__":
    main()