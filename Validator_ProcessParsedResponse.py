# Validator_ProcessParsedResponse.py

import re
from Validator_InstructionDetection import detect_instruction

def process_instruction_pairs(instruction_pairs, question):
    ops = []
    all_matches = []
    instruction_lines = []
    model_keywords_list = []
    inferred_operations = []
    detected_instrs = []
    operand_counts = []
    found_keywords_list = []
    num = 0

    for line_text, output_operation, keyword_str, inferred_operation in instruction_pairs:
        found_keywords, detected_instr, operand_count = detect_instruction(line_text)
        num += 1

        print(f"Line{num}:------------------------------------>>>")
        print(f"|^-^| Validator - Found Keywords: {found_keywords}")
        print(f"|^-^| Validator - Instruction: {detected_instr}({operand_count})" if detected_instr else "|^-^| Validator - Instruction: None")

        match = "No"
        match_instr = re.match(r"(\w+)\(([^()]*)\)", output_operation)
        if match_instr:
            model_instr = match_instr.group(1)
            operands = [op.strip() for op in match_instr.group(2).split(",") if op.strip()]
            model_operand_count = len(operands)

            if detected_instr and model_instr.upper() == detected_instr.upper() and model_operand_count == operand_count:
                match = "Yes"

        print(f"|^-^| Validator - Match: {match}\n")

        ops.append(output_operation)
        all_matches.append(match)
        instruction_lines.append(output_operation)
        model_keywords_list.append(keyword_str)
        inferred_operations.append(inferred_operation)
        detected_instrs.append(detected_instr)
        operand_counts.append(operand_count)
        found_keywords_list.append(found_keywords)

    return {
        "ops": ops,
        "matches": all_matches,
        "instruction_lines": instruction_lines,
        "model_keywords_list": model_keywords_list,
        "inferred_operations": inferred_operations,
        "detected_instrs": detected_instrs,
        "operand_counts": operand_counts,
        "found_keywords_list": found_keywords_list
    }
