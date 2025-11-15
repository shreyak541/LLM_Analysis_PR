import os
import json
import logging
import asyncio
import base64
from typing import Dict, Any, Optional
from playwright.async_api import async_playwright, Browser, Page
import requests
from openai import OpenAI
import re
from bs4 import BeautifulSoup
from datetime import datetime
import time
from data_utils import process_file_for_llm, DataAnalyzer

logger = logging.getLogger(__name__)


class QuizSolver:
    """
    Solves quiz tasks using a headless browser and LLM.
    """
    
    def __init__(self, email: str, secret: str, openai_api_key: str):
        self.email = email
        self.secret = secret
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.browser: Optional[Browser] = None
        self.max_time_per_quiz = 180  # 3 minutes in seconds
        
    async def solve_quiz_chain(self, initial_url: str):
        """
        Solve a chain of quizzes starting from the initial URL.
        Continues until no new URL is provided or time limit is reached.
        """
        start_time = time.time()
        current_url = initial_url
        attempt = 0
        
        async with async_playwright() as p:
            self.browser = await p.chromium.launch(headless=True)
            
            try:
                while current_url and (time.time() - start_time) < self.max_time_per_quiz:
                    attempt += 1
                    logger.info(f"Attempt {attempt}: Solving quiz at {current_url}")
                    
                    # Solve the current quiz
                    result = await self.solve_single_quiz(current_url, start_time)
                    
                    if result and result.get("correct"):
                        logger.info(f"Quiz solved correctly!")
                        current_url = result.get("url")
                        if current_url:
                            logger.info(f"Moving to next quiz: {current_url}")
                        else:
                            logger.info("Quiz chain completed - no more URLs")
                            break
                    elif result:
                        logger.warning(f"Quiz answer was incorrect: {result.get('reason', 'Unknown')}")
                        # Check if we got a next URL anyway (skip option)
                        next_url = result.get("url")
                        if next_url:
                            logger.info(f"Skipping to next quiz: {next_url}")
                            current_url = next_url
                        else:
                            logger.error("No next URL provided, stopping")
                            break
                    else:
                        logger.error("Failed to solve quiz (no result), stopping")
                        next_url = None
                        if next_url:
                            logger.info(f"Skipping to next quiz: {next_url}")
                            current_url = next_url
                        else:
                            logger.error("No next URL provided, stopping")
                            break
                    
                    # Prevent too fast requests
                    await asyncio.sleep(1)
                    
            finally:
                await self.browser.close()
                
        logger.info(f"Quiz chain finished after {attempt} attempts")
    
    async def solve_single_quiz(self, url: str, start_time: float) -> Optional[Dict[str, Any]]:
        """
        Solve a single quiz:
        1. Fetch and render the quiz page
        2. Extract the question using LLM
        3. Solve the question using LLM
        4. Submit the answer
        """
        try:
            # Fetch the quiz page
            page = await self.browser.new_page()
            await page.goto(url, wait_until="networkidle", timeout=30000)
            
            # Wait for JavaScript to render
            await asyncio.sleep(2)
            
            # Extract page content
            content = await page.content()
            text_content = await page.inner_text("body")
            
            await page.close()
            
            logger.info(f"Page content extracted, length: {len(text_content)}")
            
            # Parse the quiz content using LLM
            quiz_data = await self.parse_quiz_content(text_content, url)
            
            if not quiz_data:
                logger.error("Failed to parse quiz content")
                return None
            
            logger.info(f"Quiz parsed: {quiz_data.get('question', '')[:100]}...")
            
            # Solve the quiz using LLM
            answer = await self.solve_quiz_with_llm(quiz_data, start_time)
            
            if answer is None:
                logger.error("Failed to generate answer")
                return None
            
            logger.info(f"Generated answer: {str(answer)[:200]}")
            
            # Submit the answer
            submit_url = quiz_data.get("submit_url")
            if not submit_url:
                logger.error("No submit URL found")
                return None
            
            result = await self.submit_answer(submit_url, url, answer)
            return result
            
        except Exception as e:
            logger.error(f"Error solving quiz: {str(e)}", exc_info=True)
            return None
    
    async def parse_quiz_content(self, content: str, url: str) -> Optional[Dict[str, Any]]:
        """
        Use LLM to parse the quiz content and extract:
        - The question/task
        - Submit URL
        - Any file URLs to download
        - Any additional instructions
        """
        prompt = f"""You are parsing a quiz page. Extract the following information:

Page content:
{content}

Extract and return a JSON object with:
- "question": The main question or task being asked
- "submit_url": The URL where the answer should be submitted (look for POST submission URL)
- "file_urls": List of any file URLs that need to be downloaded (PDFs, CSVs, etc.)
- "instructions": Any special instructions or context

Return ONLY valid JSON, nothing else.
"""
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a precise JSON extractor. Return only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            result_text = response.choices[0].message.content.strip()
            
            # Extract JSON from markdown code blocks if present
            if "```json" in result_text:
                result_text = result_text.split("```json")[1].split("```")[0].strip()
            elif "```" in result_text:
                result_text = result_text.split("```")[1].split("```")[0].strip()
            
            quiz_data = json.loads(result_text)
            quiz_data["original_url"] = url
            
            return quiz_data
            
        except Exception as e:
            logger.error(f"Error parsing quiz content: {str(e)}", exc_info=True)
            return None
    
    async def solve_quiz_with_llm(self, quiz_data: Dict[str, Any], start_time: float) -> Any:
        """
        Use LLM to solve the quiz question.
        This may involve downloading files, analyzing data, etc.
        """
        question = quiz_data.get("question", "")
        file_urls = quiz_data.get("file_urls", [])
        instructions = quiz_data.get("instructions", "")
        
        # Download any required files
        downloaded_files = []
        file_analysis = []
        
        for file_url in file_urls:
            try:
                file_data = await self.download_file(file_url)
                if file_data:
                    downloaded_files.append(file_data)
                    # Process file for better LLM understanding
                    analysis = process_file_for_llm(file_data)
                    file_analysis.append({
                        'filename': file_data['filename'],
                        'analysis': analysis
                    })
            except Exception as e:
                logger.warning(f"Error downloading {file_url}: {str(e)}")
        
        # Build context for LLM
        context = f"""Question: {question}

Instructions: {instructions}

Downloaded files: {len(downloaded_files)}
"""
        
        if file_analysis:
            context += "\n=== FILE ANALYSIS ==="
            for item in file_analysis:
                context += f"\n\n{item['filename']}:\n{item['analysis'][:2000]}"
        
        # Ask LLM to solve
        prompt = f"""{context}

Solve this question and provide the answer in the correct format.

IMPORTANT: 
- If the answer is a number, return just the number (e.g., 12345)
- If it's a string, return the string
- If it's a boolean, return true or false
- If it's a complex object, return valid JSON
- If you need to return an image/chart, return it as a base64 data URI

Think step by step and provide your final answer clearly marked as ANSWER: <your answer>
"""
        
        try:
            # Check remaining time
            elapsed = time.time() - start_time
            if elapsed > self.max_time_per_quiz - 30:
                logger.warning("Running out of time, providing quick answer")
            
            response = self.openai_client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You are an expert data analyst. Solve the given task accurately."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0
            )
            
            result = response.choices[0].message.content.strip()
            logger.info(f"LLM response: {result[:300]}")
            
            # Extract the answer
            answer = self.extract_answer(result)
            return answer
            
        except Exception as e:
            logger.error(f"Error solving with LLM: {str(e)}", exc_info=True)
            return None
    
    def extract_answer(self, llm_response: str) -> Any:
        """Extract the final answer from LLM response"""
        # Look for ANSWER: marker
        if "ANSWER:" in llm_response.upper():
            parts = re.split(r'ANSWER:', llm_response, flags=re.IGNORECASE)
            answer_text = parts[-1].strip()
        else:
            answer_text = llm_response.strip()
        
        # Try to parse as JSON first
        try:
            return json.loads(answer_text)
        except:
            pass
        
        # Try to parse as number
        try:
            if '.' in answer_text:
                return float(answer_text)
            return int(answer_text)
        except:
            pass
        
        # Try to parse as boolean
        if answer_text.lower() in ['true', 'yes']:
            return True
        if answer_text.lower() in ['false', 'no']:
            return False
        
        # Return as string
        return answer_text
    
    async def download_file(self, url: str) -> Optional[Dict[str, Any]]:
        """Download a file and return its metadata and preview"""
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            content = response.content
            content_type = response.headers.get('Content-Type', '')
            filename = url.split('/')[-1]
            
            file_info = {
                'url': url,
                'filename': filename,
                'size': len(content),
                'type': content_type,
                'content': content
            }
            
            # Add preview based on file type
            if 'text' in content_type or filename.endswith('.csv'):
                file_info['preview'] = content.decode('utf-8', errors='ignore')[:1000]
            elif filename.endswith('.pdf'):
                file_info['preview'] = "PDF file downloaded"
            
            return file_info
            
        except Exception as e:
            logger.error(f"Error downloading file {url}: {str(e)}")
            return None
    
    async def submit_answer(self, submit_url: str, quiz_url: str, answer: Any) -> Optional[Dict[str, Any]]:
        """Submit the answer to the submission endpoint"""
        payload = {
            "email": self.email,
            "secret": self.secret,
            "url": quiz_url,
            "answer": answer
        }
        
        try:
            logger.info(f"Submitting answer to {submit_url}")
            response = requests.post(submit_url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            logger.info(f"Submission result: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Error submitting answer: {str(e)}", exc_info=True)
            return None
