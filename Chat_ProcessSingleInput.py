# Chat_ProcessSingleInput.py
import time
import re
import traceback

from model_ILCodeGen import get_model_response

from Validator_ParseModelResponse import parse_model_output
from Validator_ProcessParsedResponse import process_instruction_pairs
from Validator_Reprompt import generate_reprompt

from Chat_SanitizeModelOutput import sanitize_model_output

def process_question(question: str):
    """
    Handles single question processing end-to-end.
    Returns a dictionary of the results.
    """
    print(f"Processing -------------------------------------------------------------------------------------")
    print(f"Question: {question}")
    result_data = {
        "question": question,
        "model_output": None,
        "parsed_instructions": [],
        "validated_instructions": [],
        "final_output": None,
        "reprompted": False,
        "error": None,
        "time_taken": None
    }

    try:
        start_time = time.time()

        raw_output = get_model_response(question) 
        print(f"\n[Model output]\n{raw_output}\n")
        result_data["model_output"] = raw_output

        instruction_pairs = parse_model_output(raw_output)

        if not instruction_pairs:
            print("No instructions parsed.")
            print(f"Raw_Output: {raw_output}")
        else:
            result = process_instruction_pairs(instruction_pairs, question)
            result_data["validated_instructions"] = result

            allow_reprompt = False # Keep this as per your original code

            if allow_reprompt:
                if "No" in result["matches"]:
                    reprompt_text = generate_reprompt(
                        question=question,
                        model_outputs=result["instruction_lines"],
                        detected_instrs=result["detected_instrs"],
                        operand_counts=result["operand_counts"],
                        matches=result["matches"],
                        found_keywords_list=result["found_keywords_list"],
                        model_keywords_list=result["model_keywords_list"]
                    )
                    print("[Reprompting & Re-Processing]--->>>>>>>>>>>>>>>>>>---------------|")
                    print(reprompt_text)
                    raw_output = get_model_response(reprompt_text) # Re-invokes model_ILCodeGen
                    print(f"[New Model Output]\n{raw_output}\n")
                    result_data["reprompted"] = True
                    instruction_pairs = parse_model_output(raw_output)
                    if instruction_pairs:
                        result = process_instruction_pairs(instruction_pairs, question)
                        result_data["validated_instructions"] = result

        combined_output = ' '.join(result["ops"]).strip() if result and result["ops"] else raw_output.strip()
        print(f"Combined Output: {combined_output}")
        result_data["final_output"] = sanitize_model_output(combined_output)
        print("Final Output:", result_data["final_output"], flush=True)

        result_data["time_taken"] = round(time.time() - start_time, 2)
    except Exception as e:
        print(f"(/°Д°)/ Error in single question processing: {e}")
        traceback.print_exc()
        result_data["error"] = str(e)
        result_data["final_output"] = "Error"

    return result_data
