# LLM4L5X – V00 Package Notes

An application leveraging large language models to design and automate Allen-Bradley Studio 5000 PLC programs and related tasks.

---

## 📁 Project Structure

```
ICS_SLM_project/
├── static/
│   ├── script.js                    # JavaScript for basic UI interaction
│   └── style.css                    # CSS for styling the UI
├── templates/
│   ├── base.html                    # Base HTML layout (header, footer, etc.)
│   └── index.html                   # Main page content
├── uploads/                         # Directory to store uploaded documents
├── app.py                           # Flask server to route frontend/backend
│
│### 🔧 Backend Components
│
├── model_IntentionAnalyzer.py       # Core NLP agent; routes user input to appropriate processing
│   ├── Chat_ProcessSingleInput.py       # Orchestrates IL code generation from user input
│   │   ├── model_ILCodeGen.py           # Interacts with phi4-mini (HuggingFace or Ollama)
│   │   │   └── model_ILCodeGen_system_prompt.txt  # System prompt for IL code generation
│   │   ├── Chat_SanitizeModelOutput.py  # Cleans and formats raw model output
│   │   ├── Validator_ParseModelResponse.py
│   │   │   ├── Validator_ProcessParsedResponse.py
│   │   │   └── Validator_InstructionDetection.py
│   │   └── Validator_Reprompt.py       # Re-prompts model if validation fails
│   └── model_UDTGen.py                # Converts user instructions into UDT fields (Python dicts)
│       └── L5XGen_UDT.py
│
│### 📎 Attachment-Based Processing
│
├── Attach_L5XAnalyzer.py            # Analyzes uploaded L5X file and routes accordingly
│   └── L5XGen_UDT.py
├── Attach_ProcessExcel.py           # Processes uploaded Excel for routine generation
│
│### 🔁 Shared by Chat & Attachment Operations
│
├── L5XGen_Rung.py                   # Converts IL code to rung L5X file, invokes tag generation
├── L5XGen_Routine.py                # Converts IL code to routine L5X file, invokes tag generation
├── L5XGen_AOI.py*                   # Converts IL code to AOI L5X file, invokes tag generation
├── L5XGen_UDT.py                    # Converts IL code to UDT L5X file, invokes tag generation
├── L5XGen_Tag.py                    # Generates global tags for L5X
│
├── L5XOpt_UDT.py                    # Optimizes attached UDT L5X file (sorting, datatype ordering)
```
---
✅ Current Feature Support
- [x] Single NLP to Rung L5X generation / IL Code Generation
- [x] Batch NLP to Routine L5X generation
- [x] UDT generation and optimization
---
## 📌 ToDo
- [ ] Branching logic (Parallel Rungs)
- [ ] AOI creation from IL instructions
- [ ] Upload and analysis of Routine, UDT, and AOI (L5X format)
- [ ] Standard Block support using Retrieval-Augmented Generation (RAG)
- [ ] Standardization checks

---

## 📦 Tech Stack

- **Frontend**: HTML, CSS, JavaScript (Flask templating)
- **Backend**: Python, Flask, Transformers (LLM via HuggingFace/Ollama)
- **File Formats**: `.L5X`, `.xlsx`, `.txt`

---

## 📄 License

MIT License (or specify your preferred one)

---

## 🤝 Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you’d like to change.

---

*For questions or collaborations, feel free to contact the maintainer.*
