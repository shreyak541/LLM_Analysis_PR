"""
Test script to verify the quiz solver setup
"""
import asyncio
import os
from dotenv import load_dotenv
from quiz_solver import QuizSolver

load_dotenv()

async def test_demo():
    """Test with the demo endpoint"""
    email = os.getenv("STUDENT_EMAIL")
    secret = os.getenv("STUDENT_SECRET")
    openai_key = os.getenv("OPENAI_API_KEY")
    
    if not all([email, secret, openai_key]):
        print("❌ Missing environment variables. Check your .env file.")
        return
    
    print("🧪 Testing Quiz Solver with demo endpoint...")
    print(f"Email: {email}")
    print(f"Secret: {'*' * len(secret)}")
    
    solver = QuizSolver(email, secret, openai_key)
    
    demo_url = "https://tds-llm-analysis.s-anand.net/demo"
    print(f"\n🎯 Solving quiz at: {demo_url}")
    
    try:
        await solver.solve_quiz_chain(demo_url)
        print("\n✅ Test completed!")
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_demo())
