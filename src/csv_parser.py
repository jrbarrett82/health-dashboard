"""Parser for Lose It! CSV data files."""
import io
import csv
from datetime import datetime
from typing import List, Dict
from dateutil import parser as date_parser


class LoseItCSVParser:
    """Parses Lose It! CSV exports and aggregates nutrition data by day."""
    
    def parse_csv(self, csv_data: bytes) -> List[Dict]:
        """
        Parse CSV data from Lose It! export.
        
        Args:
            csv_data: Raw CSV file content as bytes
            
        Returns:
            List of daily aggregated nutrition data
        """
        # Decode CSV data
        csv_text = csv_data.decode('utf-8')
        csv_file = io.StringIO(csv_text)
        
        reader = csv.DictReader(csv_file)
        
        # Aggregate by day
        days = {}
        
        for row in reader:
            if not row.get('Date'):
                continue
            
            date_str = row['Date']
            
            # Parse date
            try:
                date_obj = date_parser.parse(date_str).date()
                date_key = date_obj.isoformat()
            except Exception as e:
                print(f"Warning: Could not parse date '{date_str}': {e}")
                continue
            
            # Initialize day entry if needed
            if date_key not in days:
                days[date_key] = {
                    'date': date_key,
                    'calories': 0,
                    'protein_g': 0,
                    'carbs_g': 0,
                    'fat_g': 0,
                    'sodium_mg': 0,
                    'sugar_g': 0,
                    'fiber_g': 0,
                    'weight_lbs': None,
                }
            
            # Add food/nutrition data
            if row.get('Calories'):
                try:
                    days[date_key]['calories'] += self._parse_number(row.get('Calories', 0))
                    days[date_key]['protein_g'] += self._parse_number(
                        row.get('Protein (g)') or row.get('Protein(g)', 0)
                    )
                    days[date_key]['carbs_g'] += self._parse_number(
                        row.get('Carbohydrates (g)') or row.get('Carbohydrates(g)', 0)
                    )
                    days[date_key]['fat_g'] += self._parse_number(
                        row.get('Fat (g)') or row.get('Fat(g)', 0)
                    )
                    days[date_key]['sodium_mg'] += self._parse_number(
                        row.get('Sodium (mg)') or row.get('Sodium(mg)', 0)
                    )
                    days[date_key]['sugar_g'] += self._parse_number(
                        row.get('Sugars (g)') or row.get('Sugars(g)', 0)
                    )
                    days[date_key]['fiber_g'] += self._parse_number(
                        row.get('Fiber (g)') or row.get('Fiber(g)', 0)
                    )
                except Exception as e:
                    print(f"Warning: Error parsing nutrition data for {date_key}: {e}")
            
            # Add weight data (overwrites if multiple entries)
            if row.get('Weight'):
                try:
                    days[date_key]['weight_lbs'] = self._parse_number(row['Weight'])
                except Exception as e:
                    print(f"Warning: Error parsing weight for {date_key}: {e}")
        
        # Convert to list and sort by date
        result = sorted(days.values(), key=lambda x: x['date'])
        
        print(f"✓ Parsed {len(result)} days of nutrition data")
        return result
    
    def _parse_number(self, value) -> float:
        """Safely parse a numeric value."""
        if value is None or value == '':
            return 0.0
        
        try:
            # Remove commas and parse
            if isinstance(value, str):
                value = value.replace(',', '')
            return float(value)
        except (ValueError, TypeError):
            return 0.0
    
    def parse_multiple_csvs(self, csv_files: List[bytes]) -> List[Dict]:
        """
        Parse multiple CSV files and combine data.
        
        Args:
            csv_files: List of CSV file contents as bytes
            
        Returns:
            Combined and deduplicated daily nutrition data
        """
        all_data = {}
        
        for csv_data in csv_files:
            parsed = self.parse_csv(csv_data)
            
            # Merge data by date (later data overwrites earlier)
            for entry in parsed:
                date_key = entry['date']
                if date_key in all_data:
                    # Merge: sum nutrition values, keep latest weight
                    all_data[date_key]['calories'] += entry['calories']
                    all_data[date_key]['protein_g'] += entry['protein_g']
                    all_data[date_key]['carbs_g'] += entry['carbs_g']
                    all_data[date_key]['fat_g'] += entry['fat_g']
                    all_data[date_key]['sodium_mg'] += entry['sodium_mg']
                    all_data[date_key]['sugar_g'] += entry['sugar_g']
                    all_data[date_key]['fiber_g'] += entry['fiber_g']
                    if entry['weight_lbs']:
                        all_data[date_key]['weight_lbs'] = entry['weight_lbs']
                else:
                    all_data[date_key] = entry
        
        # Convert to sorted list
        result = sorted(all_data.values(), key=lambda x: x['date'])
        
        print(f"✓ Combined into {len(result)} unique days")
        return result
