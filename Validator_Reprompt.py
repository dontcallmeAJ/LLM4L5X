# Validator_Reprompt.py

def generate_reprompt(question, model_outputs, detected_instrs, operand_counts, matches, found_keywords_list, model_keywords_list):
    """
    Generate a reprompt message when one or more model outputs don't match the expected instruction.

    Parameters:
        question (str): Original input question.
        model_outputs (List[str]): List of model-generated operations, one per line.
        detected_instrs (List[str]): List of detected instructions, one per line.
        operand_counts (List[int]): Operand count for each detected instruction.
        matches (List[str]): List indicating if each line matched ("Yes" or "No").
        found_keywords_list (List[List[str]]): Detected keywords per line.
        model_keywords_list (List[str]): Model-inferred keywords per line.

    Returns:
        str: The generated reprompt message.
    """
    mismatch_sections = []

    for i, match in enumerate(matches):
        if match == "No":
            model_output = model_outputs[i]
            detected_instr = detected_instrs[i]
            operand_count = operand_counts[i]
            found_keywords = found_keywords_list[i]
            model_keywords = model_keywords_list[i]

            # Extract model instruction and operand count
            import re
            model_instr_match = re.match(r"(\w+)\((.*?)\)", model_output)
            if model_instr_match:
                model_instr = model_instr_match.group(1)
                model_operands = [op.strip() for op in model_instr_match.group(2).split(",") if op.strip()]
                model_operand_count = len(model_operands)
            else:
                model_instr = "Unknown"
                model_operand_count = 0

            mismatch_sections.append(
                f"Line {i+1}:\n"
                f"Your response: {model_output}\n"
                #f"→ Detected keywords: {', '.join(found_keywords) if found_keywords else 'None'}\n"
                #f"→ Expected instruction: {detected_instr} ({operand_count} operand{'s' if operand_count != 1 else ''})\n"
                #f"→ Your instruction: {model_instr} ({model_operand_count} operand{'s' if model_operand_count != 1 else ''}) "
                #f"with keywords: {model_keywords}\n"
                f"→ ✅ The correct instruction should be: {detected_instr} with {operand_count} operand{'s' if operand_count != 1 else ''}.\n"
            )

    if not mismatch_sections:
        return "All lines matched the expected instructions. No reprompt needed."

    reprompt_text = (
        f"Let's correct your previous response.\n\n"
        f"The original question was:\n\n\"{question}\"\n\n"
        f"Issues were found in the following line(s):\n\n" +
        "\n".join(mismatch_sections) +
        "\nPlease revise only the incorrect lines. Lines that were correct may stay unchanged."
    )

    return reprompt_text
