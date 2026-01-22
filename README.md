# 🍽️ RestaurantAI - Modern Restaurant Recommendation System

[![Django](https://img.shields.io/badge/Django-4.2-green.svg)](https://djangoproject.com/)
[![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4-blue.svg)](https://openai.com/)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com/)
[![Bootstrap](https://img.shields.io/badge/Bootstrap-5.3-purple.svg)](https://getbootstrap.com/)

A cutting-edge, AI-powered restaurant recommendation platform built with Django, featuring a modern responsive design, intelligent chat assistant, and seamless user experience.

## ✨ Features

### 🤖 AI-Powered Assistant
- **GPT-4 Integration**: Advanced natural language processing for restaurant recommendations
- **Contextual Responses**: Intelligent understanding of user preferences and requirements
- **Real-time Chat**: Streaming responses for instant feedback

### 🎨 Modern UI/UX
- **Responsive Design**: Beautiful interface that works on all devices
- **Gradient Themes**: Eye-catching visual design with smooth animations
- **Interactive Elements**: Hover effects, transitions, and micro-interactions
- **Accessibility**: WCAG compliant design with proper contrast and navigation

### 🔍 Advanced Search
- **Smart Filtering**: Filter by cuisine, price range, location, and dietary preferences
- **Real-time Results**: Instant search with live filtering
- **Multiple View Modes**: Grid and list views for restaurant listings
- **Rating System**: Star-based ratings with detailed reviews

### 📱 User Experience
- **One-Click Reservations**: Streamlined booking process
- **Personal Dashboard**: User profiles with reservation history
- **Social Features**: Review system and restaurant ratings
- **Mobile-First**: Optimized for mobile devices

## 🚀 Quick Start

### Prerequisites
- Docker and Docker Compose
- OpenAI API Key

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/mrchandrayee/Restaurant-Recommender-AI.git
   cd Restaurant-Recommender-AI
   ```

2. **Set up environment variables**
   ```bash
   export OPENAI_API_KEY="your-openai-api-key-here"
   ```

3. **Run with Docker**
   ```bash
   docker compose up --build
   ```

4. **Access the application**
   - Open [http://localhost:8000](http://localhost:8000) in your browser
   - Create an account or login to start exploring

## 🏗️ Architecture

### Tech Stack
- **Backend**: Django 4.2 (Python)
- **Frontend**: Bootstrap 5.3, Custom CSS, JavaScript
- **AI**: OpenAI GPT-4 API
- **Database**: SQLite (development) / PostgreSQL (production)
- **Deployment**: Docker & Docker Compose

### Project Structure
```
Restaurant-Recommender-AI/
├── core/                    # Main Django app
│   ├── models.py           # Database models
│   ├── views.py            # Business logic
│   ├── templates/          # HTML templates
│   └── static/             # CSS, JS, images
├── restaurant/             # Django project settings
├── static/                 # Global static files
├── Dockerfile             # Docker configuration
├── docker-compose.yml     # Multi-container setup
└── requirements.txt       # Python dependencies
```

## 🎯 Key Components

### AI Chat Interface
- Streaming responses for real-time conversation
- Markdown support for rich text formatting
- Quick suggestion buttons for common queries
- Auto-resizing text input with keyboard shortcuts

### Modern Design System
- CSS Variables for consistent theming
- Gradient backgrounds and hover effects
- Smooth animations and transitions
- Mobile-responsive grid layouts

### Enhanced Functionality
- Advanced search with multiple filters
- Interactive restaurant cards
- User authentication and profiles
- Reservation management system

## 🔧 Development

### Local Development Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Run development server
python manage.py runserver
```

### Docker Development
```bash
# Build and run
docker compose up --build

# Run in background
docker compose up -d

# View logs
docker compose logs -f

# Stop containers
docker compose down
```

## 📊 API Endpoints

- `GET /` - Home page with featured restaurants
- `GET /search/` - Restaurant search with filters
- `GET /chat/` - AI assistant interface
- `POST /api/chat/` - Chat API endpoint
- `POST /api/reservations/create/` - Create reservation
- `GET /api/restaurants/search/` - Search restaurants API

## 🎨 Design Highlights

### Color Palette
- **Primary**: Indigo gradient (#6366f1 to #4f46e5)
- **Secondary**: Amber (#f59e0b)
- **Accent**: Emerald (#10b981)
- **Background**: Light gray (#f8fafc)

### Typography
- **Headings**: Playfair Display (serif)
- **Body**: Inter (sans-serif)
- **Weights**: 300-800 for various emphasis levels

### Animations
- Fade-in animations on scroll
- Hover transformations
- Loading spinners
- Smooth page transitions

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

