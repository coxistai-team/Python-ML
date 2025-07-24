from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import tempfile
from werkzeug.utils import secure_filename
import logging
import json
from dotenv import load_dotenv

from modules.image_ocr import extract_text_from_image
from modules.pdf_parser import extract_text_from_file
# from modules.voice_input import transcribe_audio
from modules.text_classifier import is_educational
from modules.query import SmartDeepSeek
# from modules.tts import TextToSpeech


app = Flask(__name__)
CORS(app, resources={
    r"/*": {
        "origins": os.getenv("ALLOWED_ORIGINS", "*").split(","),
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.config['UPLOAD_FOLDER'] = 'temp_uploads'

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
tts_engine = TextToSpeech(output_dir='temp_uploads')


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
if not OPENROUTER_API_KEY:
    raise RuntimeError("OPENROUTER_API_KEY not set in environment variables.")

assistant = SmartDeepSeek(OPENROUTER_API_KEY)

ALLOWED_EXTENSIONS = {
    'image': {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'tiff'},
    'document': {'pdf', 'docx'},
    'audio': {'mp3', 'wav', 'm4a'}
}

def allowed_file(filename, file_type):
    """Check if the file extension is allowed for the given type"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())


def improve_question_prompt(text):
    """Enhance the text with better prompting for clean, well-formatted responses"""
    if not text or not isinstance(text, str):
        return "Please provide more information to help you better."
    
    text_lower = text.lower()
    
    base_format = """Please provide a clean, well-structured response following these guidelines:
- Use bold text for important terms and key points
- Organize information with bullet points or numbered lists when appropriate
- No extra spaces or line breaks between sections
- Direct answers without repeating the question
- No special symbols or unnecessary formatting
- Clear and concise explanations
- Professional and readable format

"""
    
    if any(word in text_lower for word in ['what is', 'define', 'definition']):
        return f"""{base_format}Provide a comprehensive definition for: {text}

Include:
1. Clear, concise definition
2. Key characteristics or properties
3. Examples if applicable
4. Context or background information"""
        
    elif any(word in text_lower for word in ['explain', 'how does', 'why does', 'how to']):
        return f"""{base_format}Explain in detail: {text}

Include:
1. Step-by-step explanation
2. Key concepts involved
3. Examples to illustrate the concept
4. Practical applications if relevant"""
        
    elif any(word in text_lower for word in ['compare', 'difference', 'vs', 'versus']):
        return f"""{base_format}Compare and contrast: {text}

Include:
1. Key similarities
2. Main differences
3. Advantages and disadvantages of each
4. When to use which option"""
        
    elif any(word in text_lower for word in ['solve', 'calculate', 'find', 'determine']):
        return f"""{base_format}Solve and explain: {text}

Include:
1. Step-by-step solution process
2. Clear mathematical steps if applicable
3. Explanation of methods used
4. Final answer clearly highlighted"""
        
    elif any(word in text_lower for word in ['analyze', 'analysis', 'examine']):
        return f"""{base_format}Analyze: {text}

Include:
1. Overview of the topic
2. Key points of analysis
3. Evidence or supporting details
4. Conclusions or implications"""
        
    elif any(word in text_lower for word in ['who is', 'who was', 'chief minister', 'president', 'minister']):
        return f"""{base_format}Provide information about: {text}

Include:
1. Name and current position
2. Party affiliation
3. Key background information
4. Recent achievements or notable facts
5. Timeline if relevant"""
        
    else:
        return f"""{base_format}Provide a detailed response about: {text}

Include relevant examples, context, and well-structured information."""
def extract_text_from_file_input(file_path, file_type):
    """Extract text from different file types using your modules"""
    try:
        if file_type == 'image':
            text = extract_text_from_image(file_path)
            return text, True if text and text.strip() else False
        elif file_type == 'document':
            text, success = extract_text_from_file(file_path)
            return text, success
        # elif file_type == 'audio':
        #     result = transcribe_audio(file_path)
        #     transcription = result.get('transcription', '')
        #     return transcription, True if transcription and transcription.strip() else False
        else:
            return None, False
    except Exception as e:
        logger.error(f"Error extracting text from {file_type}: {str(e)}")
        return None, False

@app.route('/')
def index():
    """API info endpoint"""
    return jsonify({
        'message': 'SparkTutor API is running',
        'endpoints': {
            'POST /api/chat/text': 'Process text questions',
            'POST /api/chat/file': 'Process file uploads',
            'POST /api/classify': 'Test text classification',
            'POST /api/extract': 'Extract text only from files'
        }
    })

@app.route('/api/chat/text', methods=['POST'])
def chat_text():
    """Process text input from frontend"""
    try:
        data = request.get_json()
        
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        if not message:
            return jsonify({'error': 'Message cannot be empty'}), 400
        
        if not is_educational(message):
            return jsonify({
                'success': True,
                'ai_response': "I specialize in educational content. Please ask about academic subjects like math, science, history, or other learning topics.",
                'is_educational': False,
                'type': 'text_input'
            })
        
        enhanced_question = improve_question_prompt(message)
        
        try:
            response = assistant.get_response(enhanced_question)
            return jsonify({
                'success': True,
                'ai_response': response,
                'is_educational': True,
                'type': 'text_input'
            })
        except Exception as ai_error:
            logger.error(f"AI response error: {str(ai_error)}")
            return jsonify({
                'success': False,
                'error': 'Failed to generate response. Please try again.',
                'type': 'ai_error'
            }), 500
        
    except Exception as e:
        logger.error(f"Error in chat_text: {str(e)}")
        return jsonify({'error': 'Failed to process message'}), 500

@app.route('/api/chat/file', methods=['POST'])
def chat_file():
    """Process file upload from frontend"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        file_type = None
        
        for ftype, extensions in ALLOWED_EXTENSIONS.items():
            if allowed_file(filename, ftype):
                file_type = ftype
                break
        
        if not file_type:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            extracted_text, success = extract_text_from_file_input(temp_path, file_type)
            
            if not success or not extracted_text:
                return jsonify({
                    'success': False,
                    'error': f'Failed to extract text from {file_type} file.',
                    'type': 'extraction_error'
                }), 400
            
            if not is_educational(extracted_text):
                return jsonify({
                    'success': True,
                    'ai_response': "This content doesn't appear to be educational. I can help with textbooks, research papers, and other academic materials.",
                    'extracted_text': extracted_text[:500] + '...' if len(extracted_text) > 500 else extracted_text,
                    'is_educational': False,
                    'type': 'file_input'
                })
            
            enhanced_question = improve_question_prompt(extracted_text)
            
            try:
                response = assistant.get_response(enhanced_question)
                return jsonify({
                    'success': True,
                    'ai_response': response,
                    'extracted_text': extracted_text[:1000] + '...' if len(extracted_text) > 1000 else extracted_text,
                    'is_educational': True,
                    'type': 'file_input'
                })
            except Exception as ai_error:
                logger.error(f"AI response error: {str(ai_error)}")
                return jsonify({
                    'success': False,
                    'error': 'Failed to generate response.',
                    'type': 'ai_error'
                }), 500
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
                
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return jsonify({'error': 'Failed to process file'}), 500

@app.route('/api/classify', methods=['POST'])
def classify_text():
    """Test text classification"""
    try:
        data = request.get_json()
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
        
        text = data['text']
        return jsonify({
            'text': text[:200] + '...' if len(text) > 200 else text,
            'is_educational': is_educational(text)
        })
    except Exception as e:
        logger.error(f"Classification error: {str(e)}")
        return jsonify({'error': 'Classification failed'}), 500

@app.route('/api/extract', methods=['POST'])
def extract_only():
    """Extract text from files without processing"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
            
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        filename = secure_filename(file.filename)
        file_type = None
        
        for ftype, extensions in ALLOWED_EXTENSIONS.items():
            if allowed_file(filename, ftype):
                file_type = ftype
                break
        
        if not file_type:
            return jsonify({'error': 'Unsupported file type'}), 400
        
        temp_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(temp_path)
        
        try:
            extracted_text, success = extract_text_from_file_input(temp_path, file_type)
            
            if success and extracted_text:
                return jsonify({
                    'success': True,
                    'extracted_text': extracted_text,
                    'is_educational': is_educational(extracted_text),
                    'file_type': file_type
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Failed to extract text'
                }), 400
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
    except Exception as e:
        logger.error(f"Extraction error: {str(e)}")
        return jsonify({'error': 'Extraction failed'}), 500
    
    
# Add this with your other endpoints
@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """
    Dedicated TTS endpoint
    Expects JSON: {'text': 'text to speak', 'lang': 'en', 'play': True}
    """
    try:
        data = request.get_json()
        
        # Validate input
        if not data or 'text' not in data:
            return jsonify({'error': 'Text is required'}), 400
            
        text = data['text'].strip()
        if not text:
            return jsonify({'error': 'Text cannot be empty'}), 400
            
        lang = data.get('lang', 'en')
        play = data.get('play', True)  # Default to playing immediately
        
        # Process TTS
        if play:
            success = tts_engine.text_to_speech(text, lang=lang)
            return jsonify({
                'success': success,
                'message': 'Audio played successfully' if success else 'Failed to play audio'
            })
        else:
            audio_path = tts_engine.text_to_speech(text, lang=lang, play=False)
            if audio_path:
                return jsonify({
                    'success': True,
                    'audio_path': audio_path,
                    'message': 'Audio generated successfully'
                })
            return jsonify({'success': False, 'error': 'Failed to generate audio'}), 500
            
    except Exception as e:
        logger.error(f"TTS endpoint error: {str(e)}")
        return jsonify({'error': 'Failed to process TTS request'}), 500
    
    
@app.route('/api/tts/cleanup', methods=['POST'])
def tts_cleanup():
    """Clean up TTS audio files"""
    try:
        data = request.get_json()
        audio_path = data.get('audio_path')
        
        if audio_path:
            # Clean specific file
            if os.path.exists(audio_path):
                os.remove(audio_path)
                return jsonify({'success': True, 'message': 'File removed'})
            return jsonify({'error': 'File not found'}), 404
        else:
            # Clean all TTS files in directory
            tts_files = [f for f in os.listdir(tts_engine.output_dir) 
                        if f.startswith('tts_') and f.endswith('.mp3')]
            for file in tts_files:
                os.remove(os.path.join(tts_engine.output_dir, file))
            return jsonify({
                'success': True,
                'message': f'Removed {len(tts_files)} audio files'
            })
    except Exception as e:
        logger.error(f"TTS cleanup error: {str(e)}")
        return jsonify({'error': 'Cleanup failed'}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'supported_files': ALLOWED_EXTENSIONS
    })

@app.errorhandler(413)
def too_large(e):
    return jsonify({'error': 'File too large. Maximum size is 16MB.'}), 413

@app.errorhandler(404)
def not_found(e):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(e):
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
