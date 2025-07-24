from gtts import gTTS
import pygame
import os
from datetime import datetime
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class TextToSpeech:
    def __init__(self, output_dir="temp_uploads"):
        self.output_dir = output_dir
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        pygame.mixer.init()
    
    def generate_audio(self, text, lang='en', slow=False):
        """Generate audio file from text and return its path"""
        try:
            if not text or not isinstance(text, str):
                raise ValueError("Invalid text input")
                
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            audio_path = os.path.join(self.output_dir, f"tts_{timestamp}.mp3")
            
            tts = gTTS(text=text, lang=lang, slow=slow)
            tts.save(audio_path)
            return audio_path
            
        except Exception as e:
            logger.error(f"TTS generation error: {str(e)}")
            return None

    def play_audio(self, audio_path):
        """Play audio and return status"""
        try:
            if not os.path.exists(audio_path):
                logger.error(f"Audio file not found: {audio_path}")
                return False
                
            pygame.mixer.music.load(audio_path)
            pygame.mixer.music.play()
            
            # Wait for playback to finish
            while pygame.mixer.music.get_busy():
                pygame.time.Clock().tick(10)
                
            return True
        except Exception as e:
            logger.error(f"Audio playback error: {str(e)}")
            return False

    def text_to_speech(self, text, lang='en', play=True):
        """Full TTS pipeline: generate, play, and clean up"""
        audio_path = self.generate_audio(text, lang)
        if not audio_path:
            return False
            
        if play:
            play_status = self.play_audio(audio_path)
            os.remove(audio_path)  # Clean up after playing
            return play_status
        return audio_path  # Return path if not playing immediately