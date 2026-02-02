"""InfluxDB database utilities for health data storage."""
import os
from datetime import datetime
from typing import Dict, List, Optional
from influxdb import InfluxDBClient
from dotenv import load_dotenv

load_dotenv()


class HealthDatabase:
    """Manages InfluxDB connection and data operations."""
    
    def __init__(self):
        self.host = os.getenv('INFLUXDB_HOST', 'localhost')
        self.port = int(os.getenv('INFLUXDB_PORT', 8086))
        self.username = os.getenv('INFLUXDB_USERNAME', 'health_user')
        self.password = os.getenv('INFLUXDB_PASSWORD', 'health_password')
        self.database = os.getenv('INFLUXDB_DATABASE', 'HealthStats')
        
        self.client = None
        
    def connect(self):
        """Establish connection to InfluxDB."""
        try:
            self.client = InfluxDBClient(
                host=self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                database=self.database
            )
            # Create database if it doesn't exist
            databases = self.client.get_list_database()
            if {'name': self.database} not in databases:
                self.client.create_database(self.database)
            print(f"✓ Connected to InfluxDB at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to InfluxDB: {e}")
            return False
    
    def write_daily_nutrition(self, date: datetime, data: Dict):
        """
        Write daily nutrition data to InfluxDB.
        
        Args:
            date: Date of the measurement
            data: Dictionary with nutrition metrics (calories, protein_g, etc.)
        """
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        point = {
            "measurement": "daily_nutrition",
            "time": date.isoformat(),
            "fields": {
                "calories": float(data.get('calories', 0)),
                "protein_g": float(data.get('protein_g', 0)),
                "carbs_g": float(data.get('carbs_g', 0)),
                "fat_g": float(data.get('fat_g', 0)),
                "sodium_mg": float(data.get('sodium_mg', 0)),
                "sugar_g": float(data.get('sugar_g', 0)),
                "fiber_g": float(data.get('fiber_g', 0)),
            }
        }
        
        # Add weight if available
        if data.get('weight_lbs'):
            point['fields']['weight_lbs'] = float(data['weight_lbs'])
        
        try:
            self.client.write_points([point])
            return True
        except Exception as e:
            print(f"Error writing to InfluxDB: {e}")
            return False
    
    def batch_write_nutrition(self, entries: List[Dict]):
        """
        Write multiple nutrition entries in batch.
        
        Args:
            entries: List of dicts with 'date' and nutrition data
        """
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        points = []
        for entry in entries:
            date = entry.get('date')
            if isinstance(date, str):
                date = datetime.fromisoformat(date)
            
            point = {
                "measurement": "daily_nutrition",
                "time": date.isoformat(),
                "fields": {
                    "calories": float(entry.get('calories', 0)),
                    "protein_g": float(entry.get('protein_g', 0)),
                    "carbs_g": float(entry.get('carbs_g', 0)),
                    "fat_g": float(entry.get('fat_g', 0)),
                    "sodium_mg": float(entry.get('sodium_mg', 0)),
                    "sugar_g": float(entry.get('sugar_g', 0)),
                    "fiber_g": float(entry.get('fiber_g', 0)),
                }
            }
            
            if entry.get('weight_lbs'):
                point['fields']['weight_lbs'] = float(entry['weight_lbs'])
            
            points.append(point)
        
        try:
            self.client.write_points(points)
            print(f"✓ Wrote {len(points)} nutrition entries to database")
            return True
        except Exception as e:
            print(f"✗ Error batch writing to InfluxDB: {e}")
            return False
    
    def query_date_range(self, start_date: datetime, end_date: datetime) -> List[Dict]:
        """
        Query nutrition data for a date range.
        
        Args:
            start_date: Start date
            end_date: End date
            
        Returns:
            List of nutrition data points
        """
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        # Format timestamps for InfluxDB (RFC3339 format with Z)
        start_str = start_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        end_str = end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
        
        query = f"""
        SELECT * FROM daily_nutrition 
        WHERE time >= '{start_str}' 
        AND time <= '{end_str}'
        ORDER BY time ASC
        """
        
        try:
            result = self.client.query(query)
            points = list(result.get_points())
            return points
        except Exception as e:
            print(f"Error querying InfluxDB: {e}")
            return []
    
    def get_latest_date(self) -> Optional[datetime]:
        """Get the most recent date with data in the database."""
        if not self.client:
            raise RuntimeError("Database not connected. Call connect() first.")
        
        query = "SELECT * FROM daily_nutrition ORDER BY time DESC LIMIT 1"
        
        try:
            result = self.client.query(query)
            points = list(result.get_points())
            if points:
                return datetime.fromisoformat(points[0]['time'].replace('Z', '+00:00'))
            return None
        except Exception as e:
            print(f"Error getting latest date: {e}")
            return None
    
    def close(self):
        """Close database connection."""
        if self.client:
            self.client.close()
