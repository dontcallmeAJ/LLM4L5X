# model_IntentionAnalyzer.py

import openai

client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="nokeyneeded"
)

MODEL_NAME = "phi4"

SYSTEM_MESSAGE = (
    "You are an AI agent designed to understand and classify a user's intent related to PLC programming tasks. "
    "Your primary goal is to map the user's request, regardless of its specific wording or grammatical structure, "
    "to one of a predefined set of PLC-related creation intentions.\n\n"
    "**Instructions for Classification:**\n"
    "1.  **Identify the Core Action:** Look for keywords or phrases that indicate the user wants to 'create', 'generate', 'build', 'make', 'write', 'produce', 'construct', 'design', 'setup', 'output', or 'develop' something.\n"
    "2.  **Identify the PLC Item:** Determine which specific PLC-related item (e.g., IL Code, Rung, Routine) the user wants to create.\n"
    "3.  **Strict Output Format:** Your response MUST strictly adhere to one of the following formats:\n"
    "    - `Intent: Create IL Code`\n"
    "    - `Intent: Create Rung`\n"
    "    - `Intent: Create Routine`\n"
    "    - `Intent: Create UDT`\n"
    "    - `Intent: Create AOI`\n"
    "    - `Intent: Create L5X Program`\n"
    "    - `Intent: Unknown` (Use this if the intention is unclear or does not match any listed item for creation)\n\n"
    "Do NOT include any additional text, explanations, or conversational elements in your response beyond the specified 'Intent: <Item>' format."
)

def get_intention_response(question: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": question}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error in intention analyzer: {e}")
        return ""
