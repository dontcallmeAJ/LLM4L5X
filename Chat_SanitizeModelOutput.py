# Chat_SanitizeModelOutput.py

import re

def process_model_output(ModelOutput: str) -> str:
    """
    Cleans model output, formats it, and adds NOP() to standalone comparisons.
    """
    # Phase 1: Strip and normalize
    no_spaces = ModelOutput.replace(" ", "").replace("),", ")").replace(":", ",").replace("?", "")

    # Phase 2: Match all instructions
    instructions = re.findall(r"[A-Z]+\([^()]*\)", no_spaces)
    
    comparison_instr = {"EQ", "NE", "LE", "GE", "LT", "GT"}
    final_output = ""
    
    for i, instr in enumerate(instructions):
        instr_name = instr.split("(", 1)[0]
        
        # If comparison, check if it's alone
        if instr_name in comparison_instr:
            prev_is_comp = i > 0
            next_is_comp = i < len(instructions) - 1
            if not prev_is_comp and not next_is_comp:
                final_output += f"{instr}NOP()"
            else:
                final_output += instr
        else:
            final_output += instr

    return f"<![CDATA[{final_output};]]>"

def remove_duplicate_instructions(input_cdata: str) -> str:
    """
    Removes duplicate instructions from inside a CDATA block.
    """
    match = re.search(r'<!\[CDATA\[(.*?)\]\]>', input_cdata, re.DOTALL)
    if not match:
        return ""  # Invalid format
    inner_code = match.group(1)

    # Match all function-like instructions
    instructions = re.findall(r'\b\w+\([^()]*\)', inner_code)

    seen = set()
    unique = []
    for instr in instructions:
        if instr not in seen:
            seen.add(instr)
            unique.append(instr)

    cleaned_code = ''.join(unique)
    return f"<![CDATA[{cleaned_code};]]>"

def sanitize_model_output(raw_output: str) -> str:
    """
    Full pipeline: clean model output and remove duplicates.
    """
    cleaned = process_model_output(raw_output)
    deduped = remove_duplicate_instructions(cleaned)
    return deduped


