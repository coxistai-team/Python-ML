import whisper
from pydub import AudioSegment
import os
import tempfile

def preprocess_audio(file_path):
    """Preprocess audio file for better transcription"""
    try:
        audio = AudioSegment.from_file(file_path)
        audio = audio.set_channels(1).set_frame_rate(16000)
        
        # Create a temporary file for the cleaned audio
        temp_dir = os.path.dirname(file_path)
        clean_path = os.path.join(temp_dir, "cleaned_" + os.path.basename(file_path))
        audio.export(clean_path, format="wav")
        return clean_path
    except Exception as e:
        print(f"Audio preprocessing failed: {e}")
        return file_path  # Return original if preprocessing fails

# Load the model once when the module is imported
model = whisper.load_model("tiny")

def transcribe_audio(file_path):
    """
    Transcribe audio file to text
    Args:
        file_path (str): Path to the audio file
    Returns:
        dict: {'language_code': str, 'transcription': str}
    """
    clean_file = None
    try:
        # Preprocess the audio
        clean_file = preprocess_audio(file_path)
        
        # Transcribe using Whisper
        result = model.transcribe(clean_file)
        
        return {
            "language_code": result["language"],
            "transcription": result["text"]
        }
        
    except Exception as e:
        print(f"Transcription failed: {e}")
        return {
            "language_code": "unknown",
            "transcription": ""
        }
    
    finally:
        # Clean up the temporary processed audio file
        if clean_file and clean_file != file_path and os.path.exists(clean_file):
            try:
                os.remove(clean_file)
            except:
                pass  # Ignore cleanup errors

# Run it
if __name__ == "__main__":
    input_file = "hindi_sample.mp3"
    output = transcribe_audio(input_file)
    print("Detected Language:", output["language_code"])
    print("Transcription:", output["transcription"])