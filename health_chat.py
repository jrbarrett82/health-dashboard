#!/usr/bin/env python3
"""Interactive chat interface for health data analysis using Ollama."""
import os
import sys
import json
from datetime import datetime, timedelta
from typing import List, Dict
import requests
from dotenv import load_dotenv

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from database import HealthDatabase

load_dotenv()


class HealthChatbot:
    """Chat interface for analyzing health data with Ollama."""
    
    def __init__(self):
        self.db = HealthDatabase()
        self.ollama_host = os.getenv('OLLAMA_HOST', 'http://192.168.1.26:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'qwen2.5:7b-instruct')
        
    def query_recent_data(self, days: int = 30) -> List[Dict]:
        """Query recent nutrition data."""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        return self.db.query_date_range(start_date, end_date)
    
    def query_date_range(self, start: str, end: str) -> List[Dict]:
        """Query data for specific date range."""
        start_date = datetime.fromisoformat(start)
        end_date = datetime.fromisoformat(end)
        return self.db.query_date_range(start_date, end_date)
    
    def format_data_summary(self, data: List[Dict]) -> str:
        """Create a human-readable summary of nutrition data."""
        if not data:
            return "No data available for this period."
        
        # Calculate statistics
        total_days = len(data)
        avg_calories = sum(d.get('calories', 0) for d in data) / total_days
        avg_protein = sum(d.get('protein_g', 0) for d in data) / total_days
        avg_carbs = sum(d.get('carbs_g', 0) for d in data) / total_days
        avg_fat = sum(d.get('fat_g', 0) for d in data) / total_days
        
        # Weight data
        weights = [d.get('weight_lbs') for d in data if d.get('weight_lbs')]
        weight_summary = ""
        if weights:
            weight_change = weights[-1] - weights[0]
            weight_summary = f"\nWeight: {weights[0]:.1f} → {weights[-1]:.1f} lbs ({weight_change:+.1f} lbs)"
        
        summary = f"""Data Summary ({total_days} days):
Period: {data[0]['time'][:10]} to {data[-1]['time'][:10]}
Average Daily Intake:
  • Calories: {avg_calories:.0f} kcal
  • Protein: {avg_protein:.1f}g
  • Carbs: {avg_carbs:.1f}g
  • Fat: {avg_fat:.1f}g{weight_summary}
"""
        return summary
    
    def chat_with_ollama(self, user_message: str, context_data: List[Dict]) -> str:
        """Send message to Ollama with health data context."""
        # Prepare data context
        data_summary = self.format_data_summary(context_data)
        
        # Build system prompt
        system_prompt = f"""You are a health and nutrition analyst. You help users understand their nutrition and weight data from the Lose It! app.

Current data context:
{data_summary}

Provide helpful insights, identify trends, and answer questions about the data. Be concise but informative."""
        
        # Call Ollama API
        try:
            response = requests.post(
                f"{self.ollama_host}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_message}
                    ],
                    "stream": False
                },
                timeout=60
            )
            
            if response.status_code == 200:
                result = response.json()
                return result['message']['content']
            else:
                return f"Error: Ollama API returned status {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return f"Error: Could not connect to Ollama at {self.ollama_host}. Is it running?"
        except Exception as e:
            return f"Error calling Ollama: {e}"
    
    def run_interactive(self):
        """Run interactive chat session."""
        print("=" * 60)
        print("Health Data Chat - Powered by Ollama")
        print("=" * 60)
        print()
        
        # Connect to database
        if not self.db.connect():
            print("✗ Could not connect to database. Is InfluxDB running?")
            return
        
        print(f"Connected to Ollama: {self.ollama_host}")
        print(f"Model: {self.ollama_model}")
        print()
        
        # Load recent data
        print("Loading your recent health data (last 30 days)...")
        context_data = self.query_recent_data(days=30)
        
        if not context_data:
            print("✗ No data found. Run sync_data.py first to import your data.")
            return
        
        print(f"✓ Loaded {len(context_data)} days of data")
        print()
        print("Type your questions about your health data.")
        print("Commands: 'quit' to exit, 'summary' for data overview")
        print("=" * 60)
        print()
        
        while True:
            try:
                user_input = input("You: ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("\nGoodbye!")
                    break
                
                if user_input.lower() == 'summary':
                    print("\n" + self.format_data_summary(context_data))
                    print()
                    continue
                
                # Get AI response
                print("\nAnalyzing... ", end='', flush=True)
                response = self.chat_with_ollama(user_input, context_data)
                print("\r" + " " * 20 + "\r", end='')  # Clear "Analyzing..."
                
                print(f"AI: {response}")
                print()
                
            except KeyboardInterrupt:
                print("\n\nGoodbye!")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print()


def main():
    """Main entry point."""
    chatbot = HealthChatbot()
    chatbot.run_interactive()


if __name__ == '__main__':
    main()
