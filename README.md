# LLM Analysis Quiz - Automated Quiz Solver

An intelligent automated system that solves data analysis quizzes in real-time using AI and web automation.

## API Documentation

### Endpoints

#### `POST /`
Receives quiz tasks and initiates automated solving.

**Request Body:**
```json
{
  "email": "your-email@example.com",
  "secret": "your-secret-string",
  "url": "https://example.com/quiz-url"
}
```

**Responses:**

- **200 OK**: Quiz solving initiated
  ```json
  {
    "status": "accepted",
    "message": "Quiz solving initiated",
    "url": "https://example.com/quiz-url"
  }
  ```

- **403 Forbidden**: Invalid credentials
  ```json
  {
    "detail": "Invalid email or secret"
  }
  ```

- **400 Bad Request**: Malformed JSON payload

#### `GET /health`
Health check endpoint for monitoring.

**Response:**
```json
{
  "status": "healthy",
  "email_configured": true,
  "secret_configured": true,
  "openai_configured": true
}
```

## Testing

This project implements an automated quiz-solving API that:
- Accepts quiz tasks via REST API
- Renders JavaScript-heavy web pages using headless browser automation
- Extracts and parses questions using Large Language Models
- Downloads and analyzes data files (CSV, Excel, PDF)
- Generates accurate answers through AI-powered analysis
- Submits results automatically within time constraints

Built with FastAPI, Playwright, OpenAI GPT-4, and Pandas for robust data processing capabilities.

## Features

### Core Capabilities
- ✨ **RESTful API**: FastAPI-based endpoint for receiving quiz tasks
- 🌐 **Browser Automation**: Playwright headless browser for JavaScript rendering
- 🤖 **AI Integration**: OpenAI GPT-4 for intelligent question parsing and solving
- 📊 **Data Processing**: Comprehensive support for CSV, Excel, PDF, and JSON files
- ⚡ **Real-time Solving**: Automated answer generation and submission
- 🔗 **Chain Handling**: Sequential quiz solving with automatic URL following
- 🎯 **Multi-format Answers**: Support for numbers, strings, booleans, JSON, and base64 files

### Technical Highlights
- Asynchronous processing for non-blocking operations
- Robust error handling and retry mechanisms
- Secure credential management with environment variables
- Comprehensive logging for debugging and monitoring

## Quick Start

### Prerequisites
- Python 3.9 or higher
- OpenAI API key with available credits
- Git (for cloning the repository)

```powershell
# Windows PowerShell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

```bash
# Linux/Mac
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

3. **Configure environment variables**

Create a `.env` file in the project root:

```env
STUDENT_EMAIL=your-email@example.com
STUDENT_SECRET=your-unique-secret
OPENAI_API_KEY=sk-your-api-key-here
HOST=0.0.0.0
PORT=8000
```

> **Note**: Get your OpenAI API key from [platform.openai.com/api-keys](https://platform.openai.com/api-keys)

4. **Run the server**

```powershell
.\venv\Scripts\Activate.ps1
python app.py
```

```bash
python app.py
```

The server will start at `http://localhost:8000`

## Architecture

### System Design

```
┌─────────────────┐
│  Quiz Server    │ POST /quiz
│  (External)     │────────────────┐
└─────────────────┘                │
                                   ▼
                        ┌──────────────────────┐
                        │   FastAPI Server     │
                        │   - Validation       │
                        │   - Background Tasks │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │   Quiz Solver        │
                        │   - Playwright       │
                        │   - GPT-4 Parser     │
                        │   - File Downloader  │
                        └──────────┬───────────┘
                                   │
                         ┌─────────┴─────────┐
                         ▼                   ▼
              ┌──────────────────┐  ┌──────────────────┐
              │  Data Analyzer   │  │  OpenAI GPT-4    │
              │  - CSV/Excel     │  │  - Parse Q&A     │
              │  - PDF Extract   │  │  - Generate Ans  │
              │  - Visualization │  │  - Reasoning     │
              └──────────────────┘  └──────────────────┘
```

### Workflow

1. **Request Reception**: API endpoint receives POST request with quiz URL
2. **Validation**: Email and secret verification
3. **Page Rendering**: Playwright navigates to URL and executes JavaScript
4. **Content Extraction**: Parse HTML and extract quiz details
5. **LLM Parsing**: GPT-4 identifies question, files, and submission endpoint
6. **Data Retrieval**: Download required files (PDF, CSV, Excel, etc.)
7. **Analysis**: Process data using Pandas and generate insights
8. **Answer Generation**: GPT-4 formulates the correct answer
9. **Submission**: POST answer to the specified endpoint
10. **Chain Handling**: Process next URL if provided, repeat from step 3

Test with demo endpoint:

```powershell
# Windows PowerShell
$body = @{
    email = "your-email@example.com"
    secret = "your-secret"
    url = "https://tds-llm-analysis.s-anand.net/demo"
} | ConvertTo-Json

Invoke-WebRequest -Uri http://localhost:8000/ -Method POST -Body $body -ContentType "application/json"
```

```bash
# Linux/Mac
curl -X POST http://localhost:8000/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "your-email@example.com",
    "secret": "your-secret",
    "url": "https://tds-llm-analysis.s-anand.net/demo"
  }'
```

Or use the test script:

```powershell
python test_solver.py
```

## API Endpoints

### POST /
Accepts quiz tasks and initiates solving.

**Request:**
```json
{
  "email": "your-email@example.com",
  "secret": "your-secret",
  "url": "https://example.com/quiz-url"
}
```

**Response:**
```json
{
  "status": "accepted",
  "message": "Quiz solving initiated",
  "url": "https://example.com/quiz-url"
}
```

**Status Codes:**
- `200`: Valid request, quiz solving started
- `400`: Invalid JSON payload
- `403`: Invalid email or secret

### GET /health
Health check endpoint.

**Response:**
```json
{
  "status": "healthy",
  "email_configured": true,
  "secret_configured": true,
  "openai_configured": true
}
```

## How It Works

1. **Receive Request**: API receives POST with quiz URL
2. **Validate**: Checks email and secret match configuration
3. **Fetch Quiz**: Playwright navigates to URL and renders JavaScript
4. **Parse Question**: GPT-4 extracts question, submit URL, and file URLs
5. **Download Files**: Fetches required data files (PDF, CSV, Excel, etc.)
6. **Solve**: GPT-4 analyzes data and generates answer
7. **Submit**: Posts answer to submission endpoint
8. **Chain**: If new URL provided, repeats process

## Answer Format Support

- **Numbers**: `12345` or `123.45`
- **Strings**: `"text answer"`
- **Booleans**: `true` or `false`
- **JSON Objects**: `{"key": "value"}`
- **Base64 Files**: `data:image/png;base64,...`

## Project Structure

```
LLM_Analysis_PR/
│
├── app.py                  # FastAPI server application
├── quiz_solver.py          # Core quiz-solving logic
├── data_utils.py           # Data analysis utilities
├── test_solver.py          # Testing script
│
├── requirements.txt        # Python dependencies
├── .env                    # Environment variables (not in repo)
├── .gitignore             # Git ignore rules
├── LICENSE                # MIT License
└── README.md              # This file
```

### Key Components

- **`app.py`**: FastAPI server with endpoint handling, validation, and background task management
- **`quiz_solver.py`**: Implements browser automation, LLM integration, and quiz-solving workflow
- **`data_utils.py`**: Utilities for processing various file formats (CSV, Excel, PDF) and data visualization
- **`test_solver.py`**: Script for testing the system with demo quizzes

## Technologies Used

### Backend & API
- **FastAPI** - Modern async web framework
- **Uvicorn** - ASGI server
- **Pydantic** - Data validation

### Browser Automation & Web
- **Playwright** - Headless browser automation
- **BeautifulSoup4** - HTML parsing
- **Requests/HTTPX** - HTTP client libraries

### AI & Machine Learning
- **OpenAI API** - GPT-4 for natural language processing
- **LangChain-ready architecture** - Modular LLM integration

### Data Processing
- **Pandas** - Data manipulation and analysis
- **NumPy** - Numerical computing
- **Matplotlib** - Data visualization
- **PyPDF2** - PDF text extraction
- **openpyxl** - Excel file handling

### Configuration & Utilities
- **python-dotenv** - Environment variable management
- **aiofiles** - Async file operations

## Deployment

This application can be deployed on various platforms:

### Recommended: Render.com

1. Fork/clone this repository to your GitHub account
2. Create a new Web Service on [Render.com](https://render.com)
3. Connect your GitHub repository
4. Configure environment variables in the dashboard
5. Deploy automatically

### Alternative: Railway.app

1. Connect your repository to [Railway.app](https://railway.app)
2. Set environment variables
3. Deploy with one click

### Local Development with Tunneling

Use [ngrok](https://ngrok.com) to expose your local server:

```bash
ngrok http 8000
```

Use the provided HTTPS URL for external access.

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `STUDENT_EMAIL` | Your email address | Yes |
| `STUDENT_SECRET` | Unique secret for request verification | Yes |
| `OPENAI_API_KEY` | OpenAI API key | Yes |
| `HOST` | Server host address | No (default: 0.0.0.0) |
| `PORT` | Server port | No (default: 8000) |

### OpenAI API Setup

1. Create an account at [OpenAI Platform](https://platform.openai.com)
2. Generate an API key from [API Keys page](https://platform.openai.com/api-keys)
3. Add billing information and credits at [Billing page](https://platform.openai.com/account/billing)
4. Set the API key in your `.env` file

> **Note**: Estimated API cost is $5-20 depending on usage and quiz complexity.

## Troubleshooting

### Common Issues

#### OpenAI API Quota Error
**Error**: `insufficient_quota`  
**Solution**: Add credits at [OpenAI Billing](https://platform.openai.com/account/billing)

#### Playwright Browser Not Found
**Error**: Browser executable not found  
**Solution**:
```bash
playwright install chromium
```

#### Port Already in Use
**Error**: Address already in use  
**Solution**: Change PORT in `.env` or kill the process using the port

#### Module Import Errors
**Solution**: Ensure all dependencies are installed
```bash
pip install -r requirements.txt
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built using OpenAI's GPT-4 API
- Playwright for reliable browser automation
- FastAPI for modern Python web development

## Contact

**Repository**: [https://github.com/shreyak541/LLM_Analysis_PR](https://github.com/shreyak541/LLM_Analysis_PR)

For issues and questions, please use the GitHub Issues tab.

---

**Note**: This project is designed for educational purposes as part of a data analysis and LLM integration assessment.
