# L5XOpt_UDT.py

import logging
import xml.etree.ElementTree as ET # New import for XML parsing
import re
from L5XGen_UDT import generate_udt_l5x_from_tags, SUPPORTED_TYPES # Import SUPPORTED_TYPES too

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def extract_udt_definition(l5x_content: str) -> dict:
    """
    Extracts the name and members of a UDT from L5X content.
    It processes the provided XML for DataType elements and their Members.
    Returns a dictionary like:
    {
        "name": "Motor_OnOFF",
        "members": [
            {"name": "OnCMD", "type": "BIT", "bit_number": 0, "description": "OnCMD", "dimension": 0, "external_access": "Read/Write", "hidden": False},
            {"name": "RunFB", "type": "BIT", "bit_number": 1, "description": "RunFB", "dimension": 0, "external_access": "Read/Write", "hidden": False},
            # ... and so on
        ]
    }
    Returns an empty dict if UDT not found, or a dict with an 'error' key if parsing fails.
    This function now resides in L5XOpt_UDT.py.
    """
    try:
        root = ET.fromstring(l5x_content)
        # Look for the DataType element that is the *target* of the export
        data_type_element = root.find(".//DataType[@Use='Target']")

        if data_type_element is None:
            logging.warning("No DataType element with Use='Target' found in L5X for UDT extraction.")
            return {"error": "No target DataType element found."}

        udt_name = data_type_element.get('Name')
        if not udt_name:
            logging.warning("DataType element found but no 'Name' attribute for UDT.")
            return {"error": "UDT name not found in L5X."}

        members = []

        # Iterate through all <Member> elements directly under the <Members> tag
        for member_element in data_type_element.findall("./Members/Member"):
            member_name = member_element.get('Name')
            data_type = member_element.get('DataType')
            dimension = member_element.get('Dimension', '0') # Default to 0 if not present
            bit_number = member_element.get('BitNumber') # Can be None for non-bit members
            external_access = member_element.get('ExternalAccess', 'Read/Write')
            hidden = member_element.get('Hidden', 'false').lower() == 'true' # Convert string to bool

            # Extract description (handle CDATA if present)
            description_element = member_element.find('.//Description')
            description = ''
            if description_element is not None and description_element.text:
                # Remove CDATA markers if present (though ET.fromstring usually handles this)
                description = description_element.text.strip().replace('<![CDATA[', '').replace(']]>', '')

            # Exclude the hidden "ZZZZZZZZZZOnCMD" type members which are internal to Rockwell
            # and just map to the bit-level access.
            if member_name and not member_name.startswith('ZZZZZZZZZZ'):
                member_info = {
                    "name": member_name,
                    "type": data_type,
                    "dimension": int(dimension),
                    "description": description,
                    "external_access": external_access,
                    "hidden": hidden
                }
                if bit_number is not None:
                    try:
                        member_info["bit_number"] = int(bit_number)
                    except ValueError:
                        logging.warning(f"Invalid bit_number for member {member_name}: {bit_number}")
                        member_info["bit_number"] = None
                
                members.append(member_info)
        
        logging.info(f"Extracted UDT '{udt_name}' with {len(members)} relevant members.")
        return {"name": udt_name, "members": members}

    except ET.ParseError as e:
        logging.error(f"XML Parse Error in extract_udt_definition: {e}")
        return {"error": f"Invalid L5X format for UDT extraction: {e}"}
    except Exception as e:
        logging.error(f"Error in extract_udt_definition: {e}", exc_info=True)
        return {"error": f"Failed to extract UDT definition due to an unexpected error: {e}"}


def optimize_and_regenerate_udt(udt_definition: dict) -> dict:
    """
    Optimizes and regenerates an L5X UDT based on an extracted UDT definition.
    This function acts as an adapter, taking the UDT structure extracted by
    extract_udt_definition (now in this module) and formatting it for
    L5XGen_UDT.py's generation, ensuring that the sorting and bit-packing
    functionalities are applied.

    Args:
        udt_definition (dict): A dictionary containing the UDT's name and
                                a list of its members, as extracted by
                                extract_udt_definition (this module).
                                Expected format:
                                {
                                    "name": "MyUDT",
                                    "members": [
                                        {"name": "OnCMD", "type": "BIT", "bit_number": 0, "description": "OnCMD", "dimension": 0, "external_access": "Read/Write", "hidden": False},
                                        {"name": "CounterVal", "type": "DINT", "dimension": 0, "description": "Current Count", "external_access": "Read/Write", "hidden": False},
                                        # ... (extracted members with their attributes)
                                    ]
                                }

    Returns:
        dict: The result from generate_udt_l5x_from_tags, including:
              - "success": bool
              - "udt_text": str (the generated L5X XML)
              - "download_name": str
              - "message": str
              - "error": str (if success is False)
    """
    if not isinstance(udt_definition, dict) or not udt_definition.get("name") or not isinstance(udt_definition.get("members"), list):
        logging.error("Invalid udt_definition provided to optimize_and_regenerate_udt.")
        return {"success": False, "error": "Invalid UDT definition format for optimization."}

    udt_name = udt_definition["name"]
    extracted_members = udt_definition["members"]

    formatted_tags = []
    for member in extracted_members:
        member_name = member.get("name", "")
        if not member_name: # Skip members without a valid name
            continue

        # Handle 'BIT' type explicitly as L5XGen_UDT expects 'BOOL' for its logic
        raw_type = member.get("type", "DINT").upper()
        if raw_type == "BIT":
            base_type = "BOOL"
        else:
            base_type = raw_type

        # Check if the base type is one that L5XGen_UDT.py supports
        if base_type not in SUPPORTED_TYPES:
            logging.warning(f"Skipping unsupported member type: '{base_type}' for member '{member_name}'")
            continue

        dimension = member.get("dimension", 0)

        # Reconstruct the type string with dimension for L5XGen_UDT.py
        if dimension > 0:
            formatted_type_string = f"{base_type}[{dimension}]"
        else:
            formatted_type_string = base_type
        
        # Pass through all relevant attributes to the generation function
        formatted_tags.append({
            "name": member_name,
            "type": formatted_type_string,
            "description": member.get("description", member_name),
            "external_access": member.get("external_access", "Read/Write"), # Use extracted or default
            "hidden": member.get("hidden", False) # Use extracted or default
        })
    
    if not formatted_tags:
        logging.warning(f"No valid members found for UDT '{udt_name}' after filtering.")
        return {"success": False, "error": "No valid members to optimize for the UDT."}

    data_for_generation = {
        "udt_name": udt_name,
        "tags": formatted_tags
    }

    logging.info(f"Attempting to regenerate UDT '{udt_name}' with {len(formatted_tags)} members via L5XGen_UDT.")
    result = generate_udt_l5x_from_tags(data_for_generation)
    
    return result
