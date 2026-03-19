import gradio as gr
import requests
import speech_recognition as sr
import pyttsx3
import wave
import tempfile
import numpy as np
import os
import google.generativeai as genai

MURF_API_KEY = "ap2_c06b75d6-225e-4b5c-b599-1510cbf0b004"
GEMINI_API_KEY = "AIzaSyDKdHj9xJXqYkXvZqF5J8Z4vLmP9nR7wXc"  

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-1.5-flash")

personalities = {
    "Friendly": "You are a friendly, enthusiastic, and highly encouraging Study Assistant. Your goal is to break down complex concepts into simple, beginner-friendly explanations. Use analogies and real-world examples that beginners can relate to. Always end with a simple follow-up question to check understanding.",
    "Academic": "You are a strictly academic, highly detailed, and professional university Professor. Use precise, formal terminology, cite key concepts, provide structured explanations with clear headings, and include relevant formulas or definitions where applicable."
}

def speech_to_text(audio_file):
    try:
        recognizer = sr.Recognizer()
        with sr.AudioFile(audio_file) as source:
            audio = recognizer.record(source)
            return recognizer.recognize_google(audio, language="en-IN")
    except Exception as e:
        return f"ERROR: {str(e)}"

def save_audio_from_numpy(audio_data, sample_rate, filename):
    with wave.open(filename, 'wb') as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        audio_int16 = (audio_data * 32767).astype(np.int16)
        wav_file.writeframes(audio_int16.tobytes())

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
        if response.status_code == 200:
            res = response.json()
            return res.get("audioFile") or res.get("audio_url")
        else:
            return None
    except Exception as e:
        print("Murf Error:", e)
        return None

def offline_tts(text):
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    if len(voices) > 0:
        engine.setProperty('voice', voices[0].id)
    file_path = "output.mp3"
    engine.save_to_file(text, file_path)
    engine.runAndWait()
    return file_path

def get_llm_response(transcribed_text, personality):
    try:
        persona_prompt = personalities.get(personality, "")
        prompt = f"{persona_prompt}\n\nQuestion from student: {transcribed_text}\n\nAnswer in a clear, concise way that can be easily converted to speech (avoid tables, special characters, and formatting). Keep the answer under 300 words."
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print("Gemini Error:", e)
        return f"Sorry, I could not process your question right now. Please try again."

def voice_study_assistant(audio_path, text_input, personality):
    transcribed_text = ""
    if audio_path:
        transcribed_text = speech_to_text(audio_path)
    elif text_input:
        transcribed_text = text_input
    
    if isinstance(transcribed_text, str) and transcribed_text.startswith("ERROR"):
        return transcribed_text, None
    
    if not transcribed_text:
        return "Please provide some input (speech or text).", None
    
    llm_response_text = get_llm_response(transcribed_text, personality)
    
    audio_output_url = murf_tts(llm_response_text)
    if audio_output_url:
        return llm_response_text, audio_output_url
    else:
        print("Murf TTS failed, falling back to offline TTS.")
        offline_audio_path = offline_tts(llm_response_text)
        return llm_response_text, offline_audio_path

css = """
body {
    background: white;
    color: black;
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
    gr.Markdown("## 🎙️ AI Voice Study Assistant")
    gr.Markdown("Tap and speak your question")
    circle = gr.HTML("<div class='circle'></div>")
    audio_input = gr.Audio(sources=["microphone"], type="filepath", label="🎤 Speak")
    text_input = gr.Textbox(placeholder="Or type your question here...", label="📝 Text Input", visible=True)
    persona = gr.Radio(
        list(personalities.keys()),
        value="Friendly",
        label="🎭 Mode"
    )
    output_text = gr.Markdown()
    output_audio = gr.Audio(autoplay=True)
    speak_btn = gr.Button("🎤 Speak Now", variant="primary")
    
    def run_assistant(audio, text, persona_name):
        text_result, voice = voice_study_assistant(audio, text, persona_name)
        return text_result, voice
    
    speak_btn.click(
        run_assistant,
        inputs=[audio_input, text_input, persona],
        outputs=[output_text, output_audio]
    )
demo.launch(share=True, debug=True)
