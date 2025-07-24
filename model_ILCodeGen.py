# Model_ILCodeGen.py

import openai

client = openai.OpenAI(
    base_url="http://localhost:11434/v1",
    api_key="nokeyneeded"
)

MODEL_NAME = "phi4-mini"

with open("model_ILCodeGen_system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_MESSAGE = f.read().strip()

def get_model_response(user_question: str) -> str:
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": SYSTEM_MESSAGE},
                {"role": "user", "content": user_question}
            ],
            temperature=0.2,
            max_tokens=1000
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"Error generating IL code: {e}")
        return "An error occurred while generating IL code."
