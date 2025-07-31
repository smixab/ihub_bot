from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import json
import os
from dotenv import load_dotenv
import openai
from sentence_transformers import SentenceTransformer
import faiss
import numpy as np
import pickle
from datetime import datetime
import time
from moderation import moderation

load_dotenv()

app = Flask(__name__)
CORS(app)

# Initialize sentence transformer model for semantic search
model = SentenceTransformer('all-MiniLM-L6-v2')

class SchoolKnowledgeBase:
    def __init__(self):
        self.tools_data = []
        self.embeddings = None
        self.index = None
        self.load_knowledge_base()
        
    def load_knowledge_base(self):
        """Load the knowledge base from JSON file"""
        try:
            with open('knowledge_base.json', 'r') as f:
                data = json.load(f)
                self.tools_data = data.get('tools', [])
            
            # Load or create embeddings
            if os.path.exists('embeddings.pkl') and os.path.exists('faiss_index.idx'):
                with open('embeddings.pkl', 'rb') as f:
                    self.embeddings = pickle.load(f)
                self.index = faiss.read_index('faiss_index.idx')
            else:
                self.create_embeddings()
        except FileNotFoundError:
            print("Knowledge base not found, using default data")
            self.create_default_knowledge_base()
            self.create_embeddings()
    
    def create_default_knowledge_base(self):
        """Create a default knowledge base with sample school tools and information"""
        default_data = {
            "tools": [
                {
                    "id": 1,
                    "name": "3D Printers (Bambu Lab X1C)",
                    "category": "Fabrication",
                    "location": "Maker Space - Room 101",
                    "description": "Three Bambu Lab X1C 3D printers for high-quality prototyping and creating plastic parts with automatic multi-material capabilities",
                    "availability": "Available during lab hours (9 AM - 5 PM)",
                    "training_required": True,
                    "contact": "Dr. Smith - ext. 1234",
                    "keywords": ["3d printing", "prototyping", "plastic", "maker", "fabrication", "bambu lab", "x1c", "multi-material", "ams"]
                },
                {
                    "id": 2,
                    "name": "Laser Cutter",
                    "category": "Fabrication",
                    "location": "Maker Space - Room 102",
                    "description": "CO2 laser cutter for cutting and engraving wood, acrylic, and fabric",
                    "availability": "Available with supervision Mon-Fri 10 AM - 4 PM",
                    "training_required": True,
                    "contact": "Prof. Johnson - ext. 5678",
                    "keywords": ["laser cutting", "engraving", "wood", "acrylic", "cutting"]
                },
                {
                    "id": 3,
                    "name": "Computer Lab",
                    "category": "Computing",
                    "location": "Building A - Room 205",
                    "description": "30 computers with design software including AutoCAD, SolidWorks, and Adobe Creative Suite",
                    "availability": "24/7 with student ID card access",
                    "training_required": False,
                    "contact": "IT Help Desk - ext. 9999",
                    "keywords": ["computer", "software", "autocad", "solidworks", "adobe", "design"]
                },
                {
                    "id": 4,
                    "name": "Electronics Lab",
                    "category": "Electronics",
                    "location": "Engineering Building - Room 150",
                    "description": "Oscilloscopes, function generators, multimeters, and breadboarding supplies",
                    "availability": "Open lab hours: Mon-Thu 1 PM - 8 PM, Fri 1 PM - 5 PM",
                    "training_required": True,
                    "contact": "Lab Manager - ext. 4321",
                    "keywords": ["electronics", "oscilloscope", "multimeter", "breadboard", "circuits"]
                },
                {
                    "id": 5,
                    "name": "Library Study Rooms",
                    "category": "Study Space",
                    "location": "Main Library - 2nd Floor",
                    "description": "Quiet study rooms for individual and group work, equipped with whiteboards",
                    "availability": "Reservable online, 2-hour time slots",
                    "training_required": False,
                    "contact": "Library Front Desk - ext. 1111",
                    "keywords": ["study", "library", "quiet", "group work", "whiteboard", "reservation"]
                },
                {
                    "id": 6,
                    "name": "Microscopy Lab",
                    "category": "Research",
                    "location": "Science Building - Room 301",
                    "description": "Light and electron microscopes for material analysis and biological samples",
                    "availability": "By appointment only",
                    "training_required": True,
                    "contact": "Dr. Williams - ext. 7890",
                    "keywords": ["microscope", "microscopy", "electron", "analysis", "samples"]
                }
            ]
        }
        
        with open('knowledge_base.json', 'w') as f:
            json.dump(default_data, f, indent=2)
        
        self.tools_data = default_data['tools']
    
    def create_embeddings(self):
        """Create embeddings for all tools in the knowledge base"""
        if not self.tools_data:
            return
        
        # Create text representations of each tool
        texts = []
        for tool in self.tools_data:
            text = f"{tool['name']} {tool['category']} {tool['description']} {' '.join(tool['keywords'])}"
            texts.append(text)
        
        # Generate embeddings
        self.embeddings = model.encode(texts)
        
        # Create FAISS index
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatIP(dimension)
        
        # Normalize embeddings for cosine similarity
        faiss.normalize_L2(self.embeddings)
        self.index.add(self.embeddings)
        
        # Save embeddings and index
        with open('embeddings.pkl', 'wb') as f:
            pickle.dump(self.embeddings, f)
        faiss.write_index(self.index, 'faiss_index.idx')
    
    def search_tools(self, query, top_k=5):
        """Search for tools using semantic similarity"""
        if not self.index or not self.tools_data:
            return []
        
        # Generate embedding for query
        query_embedding = model.encode([query])
        faiss.normalize_L2(query_embedding)
        
        # Search
        scores, indices = self.index.search(query_embedding, min(top_k, len(self.tools_data)))
        
        results = []
        for i, (score, idx) in enumerate(zip(scores[0], indices[0])):
            if idx < len(self.tools_data):
                tool = self.tools_data[idx].copy()
                tool['relevance_score'] = float(score)
                results.append(tool)
        
        return results

# Initialize knowledge base
kb = SchoolKnowledgeBase()

@app.route('/')
def index():
    """Serve the main chatbot interface"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Handle chat messages and return AI responses"""
    start_time = time.time()
    
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'error': 'No message provided'}), 400
        
        # Moderate the message
        moderation_result = moderation.moderate_message(user_message)
        
        if not moderation_result['allowed']:
            return jsonify({
                'error': moderation_result['message'],
                'reason': moderation_result['reason'],
                'retry_after': moderation_result.get('retry_after')
            }), 429 if moderation_result['reason'] == 'rate_limited' else 403
        
        # Search knowledge base
        relevant_tools = kb.search_tools(user_message, top_k=3)
        
        # Prepare context for AI
        context = "You are a helpful assistant for students at a school. You help them find tools, locations, and information.\n\n"
        
        if relevant_tools:
            context += "Here are some relevant tools/resources I found:\n\n"
            for tool in relevant_tools:
                context += f"**{tool['name']}** ({tool['category']})\n"
                context += f"Location: {tool['location']}\n"
                context += f"Description: {tool['description']}\n"
                context += f"Availability: {tool['availability']}\n"
                context += f"Training Required: {'Yes' if tool['training_required'] else 'No'}\n"
                context += f"Contact: {tool['contact']}\n\n"
        
        context += f"User question: {user_message}\n\n"
        context += "Please provide a helpful response based on the information above. If you found relevant tools, mention them specifically. Be conversational and helpful."
        
        # Generate AI response (fallback if no OpenAI key)
        if os.getenv('OPENAI_API_KEY'):
            try:
                client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": context},
                        {"role": "user", "content": user_message}
                    ],
                    max_tokens=500,
                    temperature=0.7
                )
                ai_response = response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI API error: {e}")
                ai_response = generate_fallback_response(user_message, relevant_tools)
        else:
            ai_response = generate_fallback_response(user_message, relevant_tools)
        
        return jsonify({
            'response': ai_response,
            'relevant_tools': relevant_tools,
            'timestamp': datetime.now().isoformat()
        })
        
    except Exception as e:
        print(f"Error in chat endpoint: {e}")
        return jsonify({'error': 'Internal server error'}), 500

def generate_fallback_response(user_message, relevant_tools):
    """Generate a response when OpenAI API is not available"""
    if not relevant_tools:
        return "I couldn't find any specific tools matching your request. You might want to contact the main office at ext. 0000 for more information, or try rephrasing your question with different keywords."
    
    response = "I found some relevant resources for you:\n\n"
    
    for i, tool in enumerate(relevant_tools, 1):
        response += f"{i}. **{tool['name']}** - {tool['description']}\n"
        response += f"   📍 Location: {tool['location']}\n"
        response += f"   🕒 {tool['availability']}\n"
        if tool['training_required']:
            response += f"   ⚠️ Training required - Contact: {tool['contact']}\n"
        response += "\n"
    
    response += "Would you like more specific information about any of these resources?"
    return response

@app.route('/api/tools', methods=['GET'])
def get_all_tools():
    """Get all available tools"""
    return jsonify({'tools': kb.tools_data})

@app.route('/api/search', methods=['POST'])
def search_tools():
    """Search tools by query"""
    try:
        data = request.get_json()
        query = data.get('query', '')
        limit = data.get('limit', 10)
        
        results = kb.search_tools(query, top_k=limit)
        return jsonify({'results': results})
        
    except Exception as e:
        print(f"Error in search endpoint: {e}")
        return jsonify({'error': 'Search failed'}), 500

@app.route('/api/categories', methods=['GET'])
def get_categories():
    """Get all unique categories"""
    categories = list(set(tool['category'] for tool in kb.tools_data))
    return jsonify({'categories': sorted(categories)})

# Admin routes for moderation and monitoring
@app.route('/admin')
def admin_dashboard():
    """Admin dashboard for monitoring and moderation"""
    return render_template('admin.html')

@app.route('/api/admin/stats', methods=['GET'])
def get_admin_stats():
    """Get overall moderation statistics"""
    try:
        stats = moderation.get_user_stats()
        recent_activity = moderation.get_recent_activity(hours=24, limit=50)
        
        return jsonify({
            'stats': stats,
            'recent_activity': recent_activity
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/user/<ip>', methods=['GET'])
def get_user_info(ip):
    """Get detailed information about a specific user"""
    try:
        user_stats = moderation.get_user_stats(ip)
        return jsonify({'user': user_stats})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/block', methods=['POST'])
def block_user():
    """Block a user"""
    try:
        data = request.get_json()
        ip = data.get('ip')
        reason = data.get('reason', 'Manual block by admin')
        duration = data.get('duration_hours', 24)
        
        if not ip:
            return jsonify({'error': 'IP address required'}), 400
        
        moderation.block_user(ip, reason, duration, 'admin')
        return jsonify({'success': True, 'message': f'User {ip} blocked for {duration} hours'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/unblock', methods=['POST'])
def unblock_user():
    """Unblock a user"""
    try:
        data = request.get_json()
        ip = data.get('ip')
        
        if not ip:
            return jsonify({'error': 'IP address required'}), 400
        
        moderation.unblock_user(ip, 'admin')
        return jsonify({'success': True, 'message': f'User {ip} unblocked'})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/config', methods=['GET', 'POST'])
def manage_moderation_config():
    """Get or update moderation configuration"""
    try:
        if request.method == 'GET':
            return jsonify({'config': moderation.config})
        else:
            data = request.get_json()
            moderation.config.update(data)
            moderation.save_config()
            return jsonify({'success': True, 'config': moderation.config})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/admin/bad-words', methods=['GET', 'POST'])
def manage_bad_words():
    """Get or update bad words list"""
    try:
        if request.method == 'GET':
            return jsonify({
                'words': moderation.bad_words,
                'patterns': moderation.bad_patterns
            })
        else:
            data = request.get_json()
            if 'words' in data:
                moderation.bad_words = data['words']
            if 'patterns' in data:
                moderation.bad_patterns = data['patterns']
            moderation.save_bad_words()
            return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)