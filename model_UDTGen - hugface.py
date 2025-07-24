# model_UDTGen.py

import json
import re
from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

# Load local phi-4-mini model
model_path = r"D:\LLM\phi4mini\models--microsoft--Phi-4-mini-instruct\snapshots\model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)
pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

MODEL_NAME = "phi4-mini"

# System prompt used to instruct the model
SYSTEM_MESSAGE = (
    "You are a PLC automation assistant that extracts UDT field definitions from user instructions. "
    "Return ONLY a JSON array of objects with keys: name, type, description.\n\n"
    "Supported types: BOOL, SINT, INT, DINT, REAL, STRING, TIMER, COUNTER (case-insensitive).\n"
    "You also support arrays in the format TYPE[N], for example: BOOL[64], DINT[3].\n"
    "BOOL arrays are allowed only in sizes that are multiples of 32 (e.g., BOOL[32], BOOL[64], etc).\n\n"
    "Input Format:\n"
    "- Each field must be written as either:\n"
    "  1. name, type, description\n"
    "  2. name, type (in which case, the description should be set to the same value as the name)\n"
    "- Multiple fields must be separated using semicolons (;).\n"
    "- Each field must contain either 2 or 3 comma-separated values. Ignore fields with fewer than 2 or more than 3 values.\n"
    "- Do NOT split a single field into multiple entries. Treat everything between two semicolons as one field.\n\n"
    "Description Rules:\n"
    "- If 3 values are present, the third value MUST be used exactly as the description.\n"
    "- If only 2 values are present, set the description equal to the name.\n"
    "- NEVER use the name as the description if a third value is present.\n"
    "- The description should NEVER be blank. If missing, use the name instead.\n\n"
    "Example Input:\n"
    "bit1, BOOL, start bit; counter, DINT; msg, STRING, display message\n\n"
    "Expected Output:\n"
    "[\n"
    "  {\"name\": \"bit1\", \"type\": \"BOOL\", \"description\": \"start bit\"},\n"
    "  {\"name\": \"counter\", \"type\": \"DINT\", \"description\": \"counter\"},\n"
    "  {\"name\": \"msg\", \"type\": \"STRING\", \"description\": \"display message\"}\n"
    "]\n\n"
    "Return ONLY the JSON array. Do not include any explanation, formatting, or text outside the array.\n"
    "Make sure you do NOT replace any description with the name if the description is given.\n"
    "Return all valid fields and do not omit any.\n"
)

def chunk_fields(input_text: str, chunk_size: int = 20):
    """Split UDT fields into chunks of N fields for safer generation."""
    fields = input_text.strip().split(";")
    for i in range(0, len(fields), chunk_size):
        yield ";".join(fields[i:i + chunk_size])

def extract_udt_tags(user_input: str) -> list:
    """Extract UDT tag definitions as structured JSON."""
    all_tags = []
    
    try:
        for chunk in chunk_fields(user_input):
            full_prompt = f"{SYSTEM_MESSAGE}\nUser Input:\n{chunk.strip()}\n"

            result = pipe(
                full_prompt,
                max_new_tokens=512,
                temperature=0.2,
                do_sample=False,
                return_full_text=False
            )

            content = result[0]['generated_text'].strip()
            print(f"\n[model_UDTGen Raw Model Output]\n{content}\n")

            json_match = re.search(r'\[.*?\]', content, re.DOTALL)
            if json_match:
                json_string = json_match.group(0)
                print(f"[Extracted JSON String]\n{json_string}\n")
            else:
                print("[No JSON array found, falling back to full content]")
                json_string = content

            try:
                tags = json.loads(json_string)
                if isinstance(tags, list):
                    all_tags.extend(tags)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error: {e}")
                print(f"⚠️ Raw response: {json_string}")

        return all_tags

    except Exception as e:
        print(f"❌ Error during UDT extraction: {e}")
        return []
