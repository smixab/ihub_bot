# 🤖 iHub Bot - School Assistant Chatbot

An intelligent AI-powered chatbot helper that guides students to the proper tools, locations, and information at your school. Built with Flask, featuring semantic search capabilities and a modern web interface.

## ✨ Features

- **🔍 Intelligent Search**: Semantic search using sentence transformers for natural language queries
- **💬 AI Chat Interface**: Conversational interface with OpenAI integration (optional fallback)
- **📚 Knowledge Base**: Comprehensive database of school tools, equipment, and resources
- **🏗️ Modern UI**: Responsive web interface with beautiful design
- **⚡ Quick Actions**: Pre-defined buttons for common queries
- **📱 Mobile Friendly**: Responsive design that works on all devices
- **🛠️ Admin Panel**: Easy-to-use command-line tool for managing the knowledge base
- **📊 Analytics**: Built-in search statistics and tool usage tracking

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- pip (Python package installer)

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd ihub_bot
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables** (optional)
   ```bash
   cp .env.example .env
   # Edit .env to add your OpenAI API key if you want enhanced AI responses
   ```

4. **Run the application**
   ```bash
   python app.py
   ```

5. **Open your browser**
   Navigate to `http://localhost:5000`

## 🎯 How It Works

### For Students
Students can interact with the chatbot by:
- **Typing natural questions**: "Where can I find a 3D printer?"
- **Using quick action buttons**: Pre-defined common queries
- **Browsing categories**: Filter tools by type (Fabrication, Computing, etc.)
- **Direct search**: Search for specific tools or equipment

### Sample Interactions
- "I need help with CAD software" → Points to Computer Lab with SolidWorks
- "Where can I 3D print something?" → Shows 3D printer location and training requirements
- "I need a quiet place to study" → Suggests library study rooms with booking info
- "Electronics equipment" → Lists oscilloscopes, multimeters, and lab access hours

## 🛠️ Managing the Knowledge Base

Use the admin panel to manage your school's tools and resources:

```bash
python admin_panel.py
```

### Admin Panel Features
- **Add new tools/resources**: Equipment, software, study spaces
- **Edit existing entries**: Update availability, contacts, descriptions
- **Delete outdated items**: Remove tools no longer available
- **Search and filter**: Find specific entries quickly
- **Import/Export**: Backup and restore knowledge base
- **Statistics**: View usage analytics and tool distribution

### Knowledge Base Structure
Each tool/resource includes:
- **Name**: Equipment or resource name
- **Category**: Type (Fabrication, Computing, Study Space, etc.)
- **Location**: Building and room number
- **Description**: Detailed information about capabilities
- **Availability**: Hours, booking requirements, access info
- **Training Required**: Whether certification is needed
- **Contact**: Person or department for questions
- **Keywords**: Search terms for better discoverability

## 📝 Configuration

### Environment Variables
```bash
# Optional: OpenAI API Key for enhanced responses
OPENAI_API_KEY=your_api_key_here

# Flask settings
FLASK_ENV=development
FLASK_DEBUG=True
```

### Default Sample Data
The application includes sample data for common school resources:
- **3D Printers** (Maker Space)
- **Laser Cutters** (Fabrication)
- **Computer Labs** (CAD/Design Software)
- **Electronics Labs** (Testing Equipment)
- **Study Rooms** (Quiet Spaces)
- **Microscopy Labs** (Research Equipment)

## 🚀 Deployment

### Production Deployment

1. **Install Gunicorn** (included in requirements.txt)
   ```bash
   pip install gunicorn
   ```

2. **Run with Gunicorn**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:5000 app:app
   ```

3. **Use a reverse proxy** (nginx recommended)
   ```nginx
   server {
       listen 80;
       server_name your-domain.com;
       
       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
       }
   }
   ```

### Docker Deployment
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

## 🔧 Customization

### Adding New Categories
1. Use the admin panel or edit `knowledge_base.json`
2. Add tools with new category names
3. Categories will automatically appear in the sidebar

### Styling Customization
- Edit `static/css/style.css` for visual changes
- Modify color scheme using CSS variables in `:root`
- Customize the logo and branding in `templates/index.html`

### AI Responses
- **With OpenAI API**: Rich, contextual responses
- **Without API**: Rule-based fallback responses
- Modify `generate_fallback_response()` in `app.py` for custom logic

## 📊 Features Overview

| Feature | Description |
|---------|-------------|
| **Semantic Search** | Natural language understanding using sentence transformers |
| **Real-time Chat** | Instant responses with typing indicators |
| **Tool Discovery** | Find equipment by function, not just name |
| **Mobile Responsive** | Works perfectly on phones and tablets |
| **Admin Management** | Easy tool addition and editing |
| **Backup/Restore** | Knowledge base import/export |
| **Quick Actions** | One-click common queries |
| **Category Browsing** | Filter by tool type |
| **Contact Integration** | Direct links to staff and departments |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🆘 Support

For questions about setup or customization:
- Open an issue on GitHub
- Check the admin panel help (`python admin_panel.py`)
- Review the sample data in `knowledge_base.json`

## 🎓 Perfect for Educational Institutions

This chatbot is specifically designed for schools, universities, and educational makerspaces where students need quick access to:
- **Lab equipment locations**
- **Software availability**
- **Training requirements**
- **Contact information**
- **Operating hours**
- **Booking procedures**

Transform your school's resource discovery experience with iHub Bot! 🚀