# Attach_L5Xanalyzer.py

import xml.etree.ElementTree as ET
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def analyze_l5x_type(file_content: str) -> str:
    """
    Analyzes the L5X content to determine if it's a DataType (UDT), Program, Routine, etc.
    """
    try:
        root = ET.fromstring(file_content)
        target_type = root.get('TargetType')
        if target_type:
            # For UDTs exported as DataTypes, TargetType will be 'DataType'
            return target_type 
        
        # Fallback for other types if TargetType is not always present or specific enough
        if root.find(".//Routine") is not None:
            return "Routine"
        if root.find(".//Program") is not None:
            return "Program"
        # If it's a DataType but not explicitly marked as TargetType, still call it UDT
        if root.find(".//DataType") is not None: 
            return "UDT" 
        
        return "Unknown L5X Type"
    except ET.ParseError as e:
        logging.error(f"XML Parse Error in analyze_l5x_type: {e}")
        return "Invalid L5X (Parse Error)"
    except Exception as e:
        logging.error(f"Error in analyze_l5x_type: {e}")
        return "Analysis Error"

