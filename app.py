from flask import Flask, render_template, request, jsonify, send_file, Response
from werkzeug.utils import secure_filename
import os, sys, time, logging, re
from io import BytesIO

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from model_IntentionAnalyzer import get_intention_response
from model_UDTGen import extract_udt_tags
from Chat_ProcessSingleInput import process_question
from L5XGen_Rung import GenerateRung
from Attach_L5Xanalyzer import analyze_l5x_type
from L5XOpt_UDT import optimize_and_regenerate_udt, extract_udt_definition
from L5XGen_UDT import generate_udt_l5x_from_tags
from Attach_ProcessExcel import process_excel_file

app = Flask(__name__)
app.config.update({
    'UPLOAD_FOLDER': 'uploads',
    'MAX_CONTENT_LENGTH': 16 * 1024 * 1024
})
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
known_udts = {}

ALLOWED_EXTENSIONS = {'txt', 'pdf', 'doc', 'docx', 'xlsx', 'l5x'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def create_response(text, is_code=False, duration=None, download=None, requires_confirmation=False, confirmation_data=None):
    return {'response': {
        'text': text, 'is_code': is_code, 'duration': duration,
        'download': download, 'requires_confirmation': requires_confirmation,
        'confirmation_data': confirmation_data
    }}

def error_response(msg, status=400):
    return jsonify(create_response(msg)), status

def handle_udt_generation(user_input):
    tags = extract_udt_tags(user_input)
    if not tags.get("tags"):
        return {"success": False, "error": "Could not extract UDT definitions. Specify fields like 'a BOOL called start'."}
    udt_name = tags.get("udt_name", "GeneratedUDT")
    app.logger.info(f"Generating UDT named: {udt_name}")
    res = generate_udt_l5x_from_tags(tags)
    if res.get("success"):
        return {
            "success": True,
            "udt_l5x": res["udt_text"],
            "file_name": res["download_name"],
            "message": f"UDT '{udt_name}' generation completed - download will begin shortly."
        }
    return {"success": False, "error": f"Failed to generate UDT L5X: {res.get('error', 'Unknown error')}"}

def process_code_generation_intention(user_input, intention_type):
    result = process_question(user_input)
    output = result.get("final_output", f"Failed to generate {intention_type}.")
    download = None
    if output.startswith("<?xml"):
        download = {'file_content': output,
                    'file_name': f"generated_rung_{int(time.time())}.L5X",
                    'content_type': 'application/xml'}
    return output, bool(output), download

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('favicon.ico')

@app.route('/chat', methods=['POST'])
def chat():
    start = time.time()
    data = request.get_json() or {}
    user_msg = data.get('message', '').strip()
    if not user_msg:
        return error_response('No message received.', 400)
    app.logger.info(f"[Chat] User: {user_msg}")
    intention_raw = get_intention_response(user_msg)
    app.logger.info(f"[Chat] Intention Raw: {intention_raw}")
    intention_match = re.search(r"Intent:\s*(.+)", intention_raw)
    intention = intention_match.group(1).strip("`") if intention_match else "Unknown"

    response_text, is_code, download_info = "", False, None
    requires_confirmation, confirmation_data = False, None

    if intention in ["Create IL Code", "Create Rung"]:
        response_text, is_code, download_info = process_code_generation_intention(user_msg, intention)
    elif intention == "Create UDT":
        udt_result = handle_udt_generation(user_msg)
        if udt_result["success"]:
            response_text = udt_result["message"]
            download_info = {
                'file_content': udt_result["udt_l5x"],
                'file_name': udt_result["file_name"],
                'content_type': 'application/xml'
            }
        else:
            response_text = udt_result["error"]
    else:
        fallback = {
            "Create Routine": "What’s the Routine name, type (Ladder/ST/FBD), and function?",
            "Create AOI": "Provide AOI name, function, and parameters with types.",
            "Create L5X Program": "Provide program name, description, and initial routines.",
            "Unknown": "I'm not sure what you mean. Could you clarify your intention? For example, do you want to create a Rung, Routine, AOI, UDT, or Program?"
        }
        response_text = fallback.get(intention, f"Intention '{intention}' detected. Please clarify.")

    return jsonify(create_response(response_text, is_code, time.time() - start, download_info, requires_confirmation, confirmation_data))

@app.route('/confirm_intention', methods=['POST'])
def confirm_intention():
    start = time.time()
    data = request.get_json() or {}
    intention = data.get('intention', '').strip().rstrip("`")
    original_question = data.get('original_question', '').strip()
    if not intention:
        return error_response('No intention confirmed.', 400)

    response_text, is_code, download_info = "", False, None
    if intention in ["Create IL Code", "Create Rung"]:
        response_text, is_code, download_info = process_code_generation_intention(original_question, intention)
    elif intention == "Create UDT":
        udt_result = handle_udt_generation(original_question)
        if udt_result["success"]:
            response_text = udt_result["message"]
            download_info = {
                'file_content': udt_result["udt_l5x"],
                'file_name': udt_result["file_name"],
                'content_type': 'application/xml'
            }
        else:
            response_text = udt_result["error"]
    else:
        response_text = f"Intention '{intention}' confirmed. Please clarify further."

    return jsonify(create_response(response_text, is_code, time.time() - start, download_info))

from flask import send_file

@app.route('/attach', methods=['POST'])
def attach_file():
    start = time.time()
    file = request.files.get('file')
    message = request.form.get('message', '').strip()
    if not file or not allowed_file(file.filename):
        return error_response("Invalid or no file uploaded.", 400)

    filename = secure_filename(file.filename)
    ext = filename.rsplit('.', 1)[1].lower()

    if ext == 'xlsx':
        try:
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)

            mode = request.form.get('mode', 'routine').lower()
            log_path = os.path.join(app.config['UPLOAD_FOLDER'], f"Log_{filename}")
            output_path = os.path.join(app.config['UPLOAD_FOLDER'], f"Output_{filename.rsplit('.', 1)[0]}.L5X")

            success = process_excel_file(filepath, mode=mode, log_file_path=log_path, output_l5x_path=output_path)

            if success and os.path.exists(output_path):
                return send_file(
                    output_path,
                    as_attachment=True,
                    download_name=os.path.basename(output_path),
                    mimetype='application/xml'  
                )
            else:
                return jsonify({
                    "success": False,
                    "message": f"Failed to process Excel file '{filename}'. Check logs for details."
                }), 500

        except Exception as e:
            app.logger.exception("Error while processing Excel file.")
            return jsonify({
                "success": False,
                "message": f"Internal error while processing Excel: {str(e)}"
            }), 500

    elif ext == 'l5x':
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            l5x_content = f.read()

        l5x_type = analyze_l5x_type(l5x_content)
        if l5x_type.lower() in {"datatype", "udt"}:
            udt = extract_udt_definition(l5x_content)
            app.logger.info(f"Extracted UDT: {udt}")
            if udt and "name" in udt:
                udt_name = udt["name"]
                known_udts[udt_name] = udt
                response_text = f"Detected UDT '{udt_name}'. Please confirm next steps."
                requires_confirmation = True
                confirmation_data = {
                    'type': 'udt_attachment',
                    'udt_name': udt_name,
                    'udt_definition': udt,
                    'original_filename': filename,
                    'options': [{'label': 'Optimize', 'action': 'optimize'}, {'label': 'Manual Command', 'action': 'manual_command'}]
                }
                return jsonify(create_response(response_text, False, time.time() - start, None, requires_confirmation, confirmation_data))
            else:
                return jsonify(create_response("L5X UDT detected, but extraction failed.", False, time.time() - start))
        else:
            return jsonify(create_response(f"L5X file '{filename}' type '{l5x_type}' not currently supported.", False, time.time() - start))

    else:
        response_text = f"Received file '{filename}' with message: '{message}'"
        return jsonify(create_response(response_text, False, time.time() - start))

@app.route('/process_udt_attachment', methods=['POST'])
def process_udt_attachment():
    try:
        data = request.get_json() or {}
        action = data.get('action')
        udt_def = data.get('udt_definition')
        udt_name = udt_def.get('name', 'UnknownUDT') if udt_def else 'UnknownUDT'

        if not action or not udt_def:
            return error_response('Invalid UDT action or definition provided.')

        if action == 'optimize':
            res = optimize_and_regenerate_udt(udt_def)
            if res.get("success"):
                return jsonify(create_response(
                    f"UDT '{udt_name}' optimized. Download will begin shortly.",
                    download={
                        'file_content': res["udt_text"],
                        'file_name': res.get("download_name", f"{udt_name}_optimized.L5X"),
                        'content_type': 'application/xml'
                    }
                ))
            return jsonify(create_response(f"Failed to optimize UDT '{udt_name}': {res.get('error', 'Unknown error')}"))
        if action == 'manual_command':
            return jsonify(create_response(f"You chose manual command for UDT '{udt_name}'. What would you like to do next?"))
        return error_response('Unsupported UDT action.', 400)
    except Exception as e:
        app.logger.exception("Error in /process_udt_attachment")
        return jsonify(create_response(f'Error processing UDT attachment action: {e}.')), 500

@app.route('/generate_rung_from_saved_code', methods=['POST'])
def generate_rung_from_saved_code():
    try:
        data = request.get_json() or {}
        raw_il_code = data.get('code_content')
        original_filename = data.get('filename', f"generated_rung_{int(time.time())}.L5X")

        if not raw_il_code:
            return jsonify({'success': False, 'error': 'No code content provided to generate rung.'}), 400

        rung_generation_result = GenerateRung(raw_il_code)

        if rung_generation_result["success"]:
            l5x_content_to_download = rung_generation_result["rung_text"]
            filename = original_filename 
            if not filename.lower().endswith('.l5x'):
                filename += '.L5X'

            buffer = BytesIO()
            buffer.write(l5x_content_to_download.encode('utf-8'))
            buffer.seek(0)

            return send_file(
                buffer,
                as_attachment=True,
                download_name=filename,
                mimetype='application/xml'
            )
        else:
            return jsonify({'success': False, 'error': rung_generation_result.get('error', 'Failed to generate rung L5X.')}), 500

    except Exception as e:
        app.logger.exception("Error in /generate_rung_from_saved_code")
        return jsonify({'success': False, 'error': f'Internal server error during rung regeneration: {e}'}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5003)
