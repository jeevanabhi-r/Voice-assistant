
import gradio as gr
import requests
import speech_recognition as sr
import scipy.io.wavfile as wav
import pyttsx3

import os

MURF_API_KEY = os.getenv("ap2_a88946e5-58cf-417d-881e-b5c77a212a73")
personalities = {
  "Friendly":
  "You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding",
  "Academic":
  "You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts and structure your response. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always ask a follow-up question to check understanding"
}
def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()

        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)

        # ✅ Better accuracy for Indian accent
        return recognizer.recognize_google(audio, language="en-IN")

    except Exception as e:
        return f"ERROR: {str(e)}"
def murf_tts(text):
    try:
        url = "https://api.murf.ai/v1/speech/generate"

        headers = {
            "api-key": MURF_API_KEY,
            "Content-Type": "application/json"
        }

        data = {
            "voiceId": "en-US-natalie",
            "text": text,
            "format": "mp3"
        }

        response = requests.post(url, headers=headers, json=data)

        print("Murf Status:", response.status_code)
        print("Murf Response:", response.text)

        if response.status_code == 200:
            res = response.json()
            return res.get("audioFile") or res.get("audio_url")
        else:
            return None

    except Exception as e:
        print("Murf Error:", e)
        return None

def offline_tts(text):
    import pyttsx3

    engine = pyttsx3.init()

    # 🔥 FIX: Force valid voice
    voices = engine.getProperty('voices')

    if len(voices) > 0:
        engine.setProperty('voice', voices[0].id)  # ✅ always valid

    file_path = "output.mp3"

    engine.save_to_file(text, file_path)
    engine.runAndWait()

    return file_path

def voice_study_assistant(audio_path, text_input, personality):
    transcribed_text = ""
    if audio_path:
        transcribed_text = speech_to_text(audio_path)
    elif text_input:
        transcribed_text = text_input

    if transcribed_text.startswith("ERROR"):
        return transcribed_text, None

    if not transcribed_text:
        return "Please provide some input (speech or text).", None

    # In a real scenario, you would send transcribed_text and persona to an LLM
    # and get a response. For this example, we'll just echo and mention the persona.
    llm_response_text = f"Hello! You said: '{transcribed_text}'. Your persona is '{personality}'."

    # Attempt to generate audio using Murf AI first
    audio_output_url = murf_tts(llm_response_text)
    if audio_output_url:
        return llm_response_text, audio_output_url
    else:
        # Fallback to offline TTS if Murf fails
        print("Murf TTS failed, falling back to offline TTS.")
        offline_audio_path = offline_tts(llm_response_text)
        return llm_response_text, offline_audio_path


css = """
body {
    background: white;
    color: white;
    text-align: center;
}

.circle {
    width: 200px;
    height: 200px;
    border-radius: 50%;
    background: radial-gradient(circle, #ffffff,#800000);
    margin: auto;
    animation: pulse 1.5s infinite;
}

@keyframes pulse {
    0% { transform: scale(1); opacity: 0.7; }
    50% { transform: scale(1.2); opacity: 1; }
    100% { transform: scale(1); opacity: 0.7; }
}
"""

with gr.Blocks(css=css) as demo:

    gr.Markdown("## 🎙️ AI Voice Assistant")
    gr.Markdown("Tap and speak your question")

    circle = gr.HTML("<div class='circle'></div>")

    audio_input = gr.Audio(type="numpy", label="🎤 Speak")
    text_input = gr.Textbox(placeholder="Or type...", visible=False)

    persona = gr.Radio(
        list(personalities.keys()),
        value="Friendly",
        label="🎭 Mode"
    )

    output_text = gr.Markdown()
    output_audio = gr.Audio()

    speak_btn = gr.Button("🎤 Speak Now", variant="primary")

    def run_assistant(audio, persona_name):
        text, voice = voice_study_assistant(audio, "", persona_name)
        return text, voice

    speak_btn.click(
        run_assistant,
        inputs=[audio_input, persona],
        outputs=[output_text, output_audio]
    )

demo.launch()