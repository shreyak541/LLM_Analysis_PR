import os
import logging
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from dotenv import load_dotenv
import uvicorn
from quiz_solver import QuizSolver

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = FastAPI(title="LLM Analysis Quiz API")

# Configuration from environment
STUDENT_EMAIL = os.getenv("STUDENT_EMAIL")
STUDENT_SECRET = os.getenv("STUDENT_SECRET")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Validate configuration
if not all([STUDENT_EMAIL, STUDENT_SECRET, OPENAI_API_KEY]):
    logger.error("Missing required environment variables. Check your .env file.")
    raise ValueError("Missing required environment variables")


class QuizRequest(BaseModel):
    email: str
    secret: str
    url: str


@app.post("/")
async def handle_quiz(request: QuizRequest, background_tasks: BackgroundTasks):
    """
    Main endpoint to receive quiz tasks.
    
    Returns:
        - 200: Secret verified, quiz solving initiated
        - 400: Invalid JSON payload
        - 403: Invalid secret
    """
    try:
        # Verify email and secret
        if request.email != STUDENT_EMAIL:
            logger.warning(f"Invalid email: {request.email}")
            raise HTTPException(status_code=403, detail="Invalid email")
        
        if request.secret != STUDENT_SECRET:
            logger.warning(f"Invalid secret for email: {request.email}")
            raise HTTPException(status_code=403, detail="Invalid secret")
        
        logger.info(f"Received valid quiz request for URL: {request.url}")
        
        # Start quiz solving in background
        background_tasks.add_task(solve_quiz_task, request.email, request.secret, request.url)
        
        return {
            "status": "accepted",
            "message": "Quiz solving initiated",
            "url": request.url
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing request: {str(e)}", exc_info=True)
        raise HTTPException(status_code=400, detail="Invalid request")


async def solve_quiz_task(email: str, secret: str, url: str):
    """Background task to solve the quiz"""
    try:
        logger.info(f"Starting quiz solver for URL: {url}")
        solver = QuizSolver(email, secret, OPENAI_API_KEY)
        await solver.solve_quiz_chain(url)
        logger.info(f"Quiz solving completed for URL: {url}")
    except Exception as e:
        logger.error(f"Error solving quiz: {str(e)}", exc_info=True)


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "email_configured": bool(STUDENT_EMAIL),
        "secret_configured": bool(STUDENT_SECRET),
        "openai_configured": bool(OPENAI_API_KEY)
    }


if __name__ == "__main__":
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    logger.info(f"Starting server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
