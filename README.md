# Instagram Lead Generator

A powerful Instagram lead generation tool that scrapes user data by hashtags/niches using dual scraping methods (Apify + Playwright) with MongoDB storage and JSON export capabilities.

## 🚀 Features

- **Dual Scraping Approach**: Primary Apify scraping with Playwright fallback for maximum reliability
- **Smart User Filtering**: Filter by follower count, verification status, and account type
- **Data Export**: Export scraped data to JSON files for integration with n8n, CRM systems, or other tools
- **MongoDB Integration**: Persistent storage with efficient querying and deduplication
- **REST API**: Complete FastAPI backend with interactive documentation
- **Monitoring \& Metrics**: Built-in performance tracking and alerting system
- **Proxy Support**: Rotating proxy support to avoid rate limiting
- **Session Management**: Cookie persistence for authenticated scraping
- **Rate Limiting**: Configurable request limits to stay within platform constraints


## 🛠 Tech Stack

### Backend

- **FastAPI** - Modern Python web framework
- **MongoDB** - Document database with Motor async driver
- **Pydantic** - Data validation and settings management
- **Apify** - Professional web scraping platform
- **Playwright** - Browser automation for fallback scraping


### Frontend

- **Next.js** - React framework for the user interface
- **TypeScript** - Type-safe JavaScript


### Infrastructure

- **Docker** - Containerization support
- **Uvicorn** - ASGI server for FastAPI


## 📋 Prerequisites

- Python 3.8+
- Node.js 16+
- MongoDB 4.4+
- Apify account and API token


## 🔧 Installation \& Setup

### 1. Clone the Repository

```bash
git clone https://github.com/your-username/instagram-lead-generator.git
cd instagram-lead-generator
```


### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install
```


### 3. Environment Configuration

Create a `.env` file in the root directory:

```env
# Database Configuration
MONGODB_URL=mongodb://localhost:27017
DATABASE_NAME=instagram_leads

# Apify Configuration
APIFY_API_TOKEN=your_apify_api_token_here

# API Configuration
MAX_REQUESTS_PER_MINUTE=30
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000/api

# Frontend Configuration
NEXT_PUBLIC_DEFAULT_NICHE=fitness
NEXT_PUBLIC_MIN_FOLLOWERS=1000
NEXT_PUBLIC_MAX_RESULTS=50

# Optional: Instagram Credentials
INSTAGRAM_USERNAME=your_username
INSTAGRAM_PASSWORD=your_password

# Session Management
COOKIE_FILE_PATH=cookies.json
```


### 4. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install

# Build the project
npm run build
```


### 5. Start MongoDB

Make sure MongoDB is running on your system:

```bash
# Using MongoDB service
sudo systemctl start mongod

# Or using Docker
docker run -d -p 27017:27017 --name mongodb mongo:latest
```


## 🚀 Usage

### Starting the Application

**Backend:**

```bash
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Frontend:**

```bash
cd frontend
npm run dev
```


### API Endpoints

- **API Documentation**: `http://localhost:8000/docs`
- **Health Check**: `http://localhost:8000/health`
- **Scrape Users**: `GET /api/scraper/users`
- **Export Data**: `GET /api/export/users/{niche}`
- **Metrics**: `GET /metrics/`


### Basic Scraping Example

```bash
# Scrape fitness niche users with 5000+ followers
curl "http://localhost:8000/api/scraper/users?niche=fitness&min_followers=5000&target_count=20"
```


### Response Format

```json
{
  "status": "success",
  "scraper_used": "apify+playwright",
  "total_users": 15,
  "file_path": "/path/to/exported/file.json",
  "timestamp": "2025-08-26T09:46:00"
}
```


## 📊 Data Structure

### User Model

```json
{
  "username": "example_user",
  "full_name": "Example User",
  "follower_count": 10000,
  "following_count": 500,
  "is_verified": false,
  "is_private": false,
  "profile_pic_url": "https://...",
  "niche": "fitness",
  "scraped_at": "2025-08-26T09:46:00"
}
```


### Profile Model (Detailed)

```json
{
  "username": "example_user",
  "bio": "Fitness enthusiast 💪",
  "email": "contact@example.com",
  "recent_posts": [...],
  "engagement_rate": 3.5,
  "top_hashtags": ["fitness", "gym", "health"]
}
```


## ⚙️ Configuration

### Scraping Parameters

| Parameter | Description | Default |
| :-- | :-- | :-- |
| `niche` | Instagram hashtag (without \#) | Required |
| `min_followers` | Minimum follower count | 5000 |
| `target_count` | Target number of users to collect | 10 |
| `max_results` | Maximum results to return | 100 |
| `use_playwright_only` | Skip Apify, use only Playwright | false |

### Environment Variables

| Variable | Description | Required |
| :-- | :-- | :-- |
| `APIFY_API_TOKEN` | Your Apify API token | Yes |
| `MONGODB_URL` | MongoDB connection string | Yes |
| `MAX_REQUESTS_PER_MINUTE` | Rate limiting | No |

## 🔒 Security Considerations

- **Never commit** your `.env` file to version control
- **Rotate API tokens** regularly
- **Use proxy services** for large-scale scraping
- **Respect rate limits** to avoid account restrictions
- **Review Terms of Service** of platforms being scraped


## 📁 Project Structure

```
instagram-lead-generator/
├── backend/
│   ├── app/
│   │   ├── models/          # Pydantic models
│   │   ├── routers/         # FastAPI route handlers
│   │   ├── services/        # Business logic services
│   │   ├── utils/           # Utilities and config
│   │   └── main.py          # FastAPI application
│   ├── data/                # Exported data storage
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── pages/               # Next.js pages
│   ├── components/          # React components
│   ├── lib/                 # Utility functions
│   └── package.json         # Node dependencies
├── .env                     # Environment variables
├── .gitignore              # Git ignore rules
└── README.md               # This file
```


## 🔍 Monitoring

The application includes built-in monitoring:

- **Metrics Endpoint**: `/metrics/` - View scraping statistics
- **Performance Tracking**: Success rates, error counts, yield analysis
- **Alerting**: Low yield and error notifications
- **Health Checks**: Database connectivity monitoring


## 🐛 Troubleshooting

### Common Issues

1. **Apify Authentication Errors**
    - Verify your `APIFY_API_TOKEN` is correct
    - Check token permissions in Apify console
2. **Playwright Browser Issues**
    - Run `playwright install` to ensure browsers are installed
    - Check system compatibility
3. **MongoDB Connection Errors**
    - Ensure MongoDB is running
    - Verify `MONGODB_URL` in `.env`
4. **Rate Limiting**
    - Reduce `MAX_REQUESTS_PER_MINUTE`
    - Implement proxy rotation
    - Add delays between requests

### Logs

Check application logs for detailed error information:

```bash
# Backend logs
tail -f backend/logs.txt

# MongoDB logs
sudo journalctl -u mongod -f
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## ⚠️ Disclaimer

This tool is for educational and research purposes. Users are responsible for complying with Instagram's Terms of Service and applicable laws. The developers are not liable for any misuse of this tool.

***

**Built with ❤️ by Dhruv**

For questions or support, please open an issue on GitHub or contact [vakhariadhruv526@gmail.com].