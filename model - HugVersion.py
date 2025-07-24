from transformers import AutoTokenizer, AutoModelForCausalLM, pipeline

model_path = r"E:\LLM\phi4mini\models--microsoft--Phi-4-mini-instruct\snapshots\model"
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModelForCausalLM.from_pretrained(model_path)

pipe = pipeline("text-generation", model=model, tokenizer=tokenizer)

SYSTEM_MESSAGE = ""

with open("system_prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_MESSAGE = f.read().strip()


def get_model_response(question: str) -> str:
    try:
        # Define chat-style messages
        messages = [
            {"role": "system", "content": SYSTEM_MESSAGE},
            {"role": "user", "content": question}
        ]

        # Apply chat template
        prompt = tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)

        # Generate output
        output = pipe(prompt, max_new_tokens=1000, do_sample=False, return_full_text=False)

        return output[0]['generated_text'].strip()

    except Exception as e:
        print(f"❌ Error generating response: {e}")
        return ""
