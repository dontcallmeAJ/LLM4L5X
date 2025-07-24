# Validator_ParseModelResponse.py

import re

def parse_model_output(raw_output: str):
    lines = raw_output.splitlines()
    instructions = []

    current_line_num = None
    line_text_accum = []
    output_instr = None
    keyword_str = None
    operation_str = None

    line_pattern = re.compile(r"^line\s*\w*\s*:", re.IGNORECASE)
    output_pattern = re.compile(r"^output operation\s*:", re.IGNORECASE)
    found_pattern = re.compile(r"^found keyword\s*:", re.IGNORECASE)
    inferred_pattern = re.compile(r"^inferred operation\s*:", re.IGNORECASE)

    def save_instruction():
        if current_line_num and line_text_accum and output_instr and keyword_str and operation_str:
            line_text = " ".join(line_text_accum).strip()
            instructions.append((line_text, output_instr, keyword_str, operation_str))

    for line in lines:
        line = line.strip()

        if line_pattern.match(line):
            # Save the previous instruction before starting new one
            save_instruction()
            current_line_num = line.split(":", 1)[0].strip()
            line_text_accum = []

            # Capture any text on same line after colon, if present
            parts = line.split(":", 1)
            if len(parts) > 1 and parts[1].strip():
                line_text_accum.append(parts[1].strip())

        elif output_pattern.match(line):
            output_instr = line.split(":", 1)[1].strip()

        elif found_pattern.match(line):
            keyword_str = line.split(":", 1)[1].strip()

        elif inferred_pattern.match(line):
            operation_str = line.split(":", 1)[1].strip()

        else:
            # If it is a non-empty line and we are inside a current Line block,
            # append it as part of instruction text (handles new line values)
            if current_line_num and line:
                line_text_accum.append(line)

    # Save the last instruction collected
    save_instruction()

    return instructions
