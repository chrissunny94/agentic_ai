import os
import subprocess
import re
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Use the latest stable model
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# def clean_llm_output(text):
#     """Removes markdown code blocks if the LLM includes them."""
#     text = re.sub(r'^```(cpp|c\+\+)?\n', '', text, flags=re.MULTILINE)
#     text = re.sub(r'```$', '', text, flags=re.MULTILINE)
#     return text.strip()


def clean_llm_output(text):
    """Extract only the C++ code — strip everything outside fences."""
    # Try to find a fenced code block first
    match = re.search(r'```(?:cpp|c\+\+)?\n([\s\S]*?)```', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Fallback: if no fences, strip lines that look like markdown prose
    lines = text.split('\n')
    code_lines = [
        l for l in lines
        if not re.match(r'^(\s*(#{1,6}|\*{1,2}|>\s|[-*]\s|\d+\.))', l)
    ]
    return '\n'.join(code_lines).strip()

def compile_and_run(cpp_code, src_dir="src", build_dir="build"):
    """Writes dynamic code and builds the full project."""
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    
    # Write only the dynamic part
    main_file_path = os.path.join(src_dir, "main.cpp")
    with open(main_file_path, "w") as f:
        f.write(cpp_code)

    # 1. Configure (Linking your static animation.cpp and plots.cpp)
    config_cmd = ["cmake", "-B", build_dir, "-S", "."]
    config_process = subprocess.run(config_cmd, capture_output=True, text=True)
    
    if config_process.returncode != 0:
        return {"status": "error", "phase": "Configuration", "log": config_process.stderr}

    # 2. Build
    build_cmd = ["cmake", "--build", build_dir]
    build_process = subprocess.run(build_cmd, capture_output=True, text=True)

    if build_process.returncode != 0:
        return {"status": "error", "phase": "Compilation", "log": build_process.stderr}

    # 3. Execute (Assuming Linux/WSL based on your 'ls' output)
    exe_path = os.path.join(build_dir, "sim")
    if not os.path.exists(exe_path):
        exe_path = os.path.join(build_dir, "sim.exe") # Windows fallback

    run_process = subprocess.run([exe_path], capture_output=True, text=True)

    if run_process.returncode != 0:
        return {"status": "error", "phase": "Runtime", "log": run_process.stderr}

    return {"status": "success", "output": run_process.stdout}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_code():
    data = request.json
    user_prompt = data.get('prompt', '')

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_instruction = (
            "You are an expert physics engine developer. Generate ONLY the code for main.cpp.\n"
            "Pre-existing API available via #include \"animation.hpp\" and \"plots.hpp\":\n"
            "1. Animator anim; anim.record_frame(t, x, y);\n"
            "2. Plotter plot; plot.add_data(\"Label\", x, y);\n\n"
            "At the end of main(), you MUST call anim.emit_json() and plot.emit_json() "
            "to send data to the frontend. Print descriptive text normally to stdout.\n"
            "Return ONLY raw C++ code."
        )

        response = model.generate_content(f"{system_instruction}\n\nUser: {user_prompt}")
        current_code = clean_llm_output(response.text)

        for attempt in range(3):
            result = compile_and_run(current_code)
            
            if result["status"] == "success":
                return jsonify({'code': current_code, 'output': result["output"], 'attempts': attempt + 1})
            
            # Error feedback loop
            fix_prompt = f"Error in {result['phase']}:\n{result['log']}\n\nFix this code:\n{current_code}"
            response = model.generate_content(fix_prompt)
            current_code = clean_llm_output(response.text)
            
        return jsonify({'error': 'Failed after 3 attempts', 'last_log': result["log"], 'code': current_code}), 500

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)