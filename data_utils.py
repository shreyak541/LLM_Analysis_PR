"""
Data analysis utilities for solving quiz questions
"""
import pandas as pd
import io
import base64
from typing import Any, Dict, Optional
import PyPDF2
import logging
import json

logger = logging.getLogger(__name__)


class DataAnalyzer:
    """Helper class for analyzing different types of data"""
    
    @staticmethod
    def analyze_csv(content: bytes) -> Dict[str, Any]:
        """Analyze CSV data"""
        try:
            df = pd.read_csv(io.BytesIO(content))
            
            analysis = {
                "shape": df.shape,
                "columns": df.columns.tolist(),
                "dtypes": df.dtypes.to_dict(),
                "head": df.head().to_dict(),
                "describe": df.describe().to_dict(),
                "null_counts": df.isnull().sum().to_dict()
            }
            
            return analysis
        except Exception as e:
            logger.error(f"Error analyzing CSV: {str(e)}")
            return {}
    
    @staticmethod
    def analyze_excel(content: bytes) -> Dict[str, Any]:
        """Analyze Excel data"""
        try:
            # Read all sheets
            excel_file = pd.ExcelFile(io.BytesIO(content))
            sheets = {}
            
            for sheet_name in excel_file.sheet_names:
                df = pd.read_excel(excel_file, sheet_name=sheet_name)
                sheets[sheet_name] = {
                    "shape": df.shape,
                    "columns": df.columns.tolist(),
                    "head": df.head().to_dict()
                }
            
            return {
                "sheet_names": excel_file.sheet_names,
                "sheets": sheets
            }
        except Exception as e:
            logger.error(f"Error analyzing Excel: {str(e)}")
            return {}
    
    @staticmethod
    def extract_pdf_text(content: bytes) -> str:
        """Extract text from PDF"""
        try:
            pdf_reader = PyPDF2.PdfReader(io.BytesIO(content))
            text = ""
            
            for page_num, page in enumerate(pdf_reader.pages):
                text += f"\n=== Page {page_num + 1} ===\n"
                text += page.extract_text()
            
            return text
        except Exception as e:
            logger.error(f"Error extracting PDF: {str(e)}")
            return ""
    
    @staticmethod
    def dataframe_to_summary(df: pd.DataFrame) -> str:
        """Convert DataFrame to a readable summary"""
        summary = []
        summary.append(f"Shape: {df.shape[0]} rows × {df.shape[1]} columns")
        summary.append(f"Columns: {', '.join(df.columns.tolist())}")
        summary.append(f"\nFirst few rows:\n{df.head().to_string()}")
        summary.append(f"\nStatistics:\n{df.describe().to_string()}")
        
        return "\n".join(summary)
    
    @staticmethod
    def create_visualization_base64(df: pd.DataFrame, chart_type: str = "bar") -> str:
        """Create a simple visualization and return as base64"""
        try:
            import matplotlib.pyplot as plt
            import matplotlib
            matplotlib.use('Agg')  # Non-interactive backend
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            if chart_type == "bar" and len(df.columns) >= 2:
                df.plot(kind='bar', x=df.columns[0], y=df.columns[1], ax=ax)
            elif chart_type == "line" and len(df.columns) >= 2:
                df.plot(kind='line', x=df.columns[0], y=df.columns[1], ax=ax)
            else:
                # Default: just plot first numeric column
                numeric_cols = df.select_dtypes(include=['number']).columns
                if len(numeric_cols) > 0:
                    df[numeric_cols[0]].plot(kind='bar', ax=ax)
            
            # Save to base64
            buffer = io.BytesIO()
            plt.savefig(buffer, format='png', bbox_inches='tight')
            buffer.seek(0)
            image_base64 = base64.b64encode(buffer.read()).decode()
            plt.close(fig)
            
            return f"data:image/png;base64,{image_base64}"
            
        except Exception as e:
            logger.error(f"Error creating visualization: {str(e)}")
            return ""


def process_file_for_llm(file_info: Dict[str, Any]) -> str:
    """Process downloaded file and create LLM-friendly summary"""
    content = file_info.get('content')
    filename = file_info.get('filename', '')
    
    if not content:
        return "No content available"
    
    # Handle different file types
    if filename.endswith('.csv'):
        analysis = DataAnalyzer.analyze_csv(content)
        return f"CSV Analysis:\n{json.dumps(analysis, indent=2, default=str)}"
    
    elif filename.endswith(('.xlsx', '.xls')):
        analysis = DataAnalyzer.analyze_excel(content)
        return f"Excel Analysis:\n{json.dumps(analysis, indent=2, default=str)}"
    
    elif filename.endswith('.pdf'):
        text = DataAnalyzer.extract_pdf_text(content)
        return f"PDF Content:\n{text[:3000]}..."  # First 3000 chars
    
    elif filename.endswith('.json'):
        try:
            data = json.loads(content.decode('utf-8'))
            return f"JSON Data:\n{json.dumps(data, indent=2)[:3000]}"
        except:
            return f"JSON file (could not parse): {content.decode('utf-8', errors='ignore')[:1000]}"
    
    else:
        # Try as text
        try:
            return f"Text content:\n{content.decode('utf-8', errors='ignore')[:3000]}"
        except:
            return f"Binary file: {len(content)} bytes"
