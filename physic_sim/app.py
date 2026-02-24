import os
import subprocess
import re
from flask import Flask, render_template, request, jsonify
import google.generativeai as genai

app = Flask(__name__)

# Configure the LLM API
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def clean_llm_output(text):
    """Removes markdown code blocks if the LLM includes them."""
    text = re.sub(r'^```(cpp|c\+\+)?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    return text.strip()

def compile_and_run(cpp_code, src_dir="src", build_dir="build"):
    """Writes the code, builds via CMake, and runs the executable."""
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    
    # The agent's generated code is always written to main.cpp
    main_file_path = os.path.join(src_dir, "main.cpp")
    with open(main_file_path, "w") as f:
        f.write(cpp_code)

    # Step 1: CMake Configure (Using MinGW as per your terminal)
    config_cmd = ["cmake", "-G", "MinGW Makefiles", "-B", build_dir, "-S", "."]
    config_process = subprocess.run(config_cmd, capture_output=True, text=True)
    
    if config_process.returncode != 0:
        return {"status": "error", "phase": "CMake Configuration", "log": config_process.stderr or config_process.stdout}

    # Step 2: CMake Build
    build_cmd = ["cmake", "--build", build_dir]
    build_process = subprocess.run(build_cmd, capture_output=True, text=True)

    if build_process.returncode != 0:
        return {"status": "error", "phase": "Compilation", "log": build_process.stderr or build_process.stdout}

    # Step 3: Execute the Simulation
    exe_path = os.path.join(build_dir, "sim.exe") 
    if not os.path.exists(exe_path):
        exe_path = os.path.join(build_dir, "Debug", "sim.exe") # Fallback

    run_process = subprocess.run([exe_path], capture_output=True, text=True)

    if run_process.returncode != 0:
        return {"status": "error", "phase": "Execution (Runtime Error)", "log": run_process.stderr or run_process.stdout}

    return {"status": "success", "output": run_process.stdout}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate', methods=['POST'])
def generate_code():
    data = request.json
    user_prompt = data.get('prompt', '')

    if not user_prompt:
        return jsonify({'error': 'Prompt is required'}), 400

    try:
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        system_instruction = (
            "You are an expert in computational physics and high-performance C++. "
            "Generate valid, standalone C++ code for the requested simulation. "
            "The code MUST contain a main() function that prints the final results to stdout. "
            "You have access to two custom headers: #include \"animation.hpp\" and #include \"plots.hpp\". "
            "Use these headers if the user requests plotting or animation. "
            "Return ONLY the raw C++ code. Do not include markdown blocks or explanations."
        )

        # Initial Generation
        full_prompt = f"{system_instruction}\n\nUser Request: {user_prompt}"
        response = model.generate_content(full_prompt)
        current_code = clean_llm_output(response.text)

        max_retries = 3
        
        # The Agentic Feedback Loop
        for attempt in range(max_retries):
            print(f"Agent Attempt {attempt + 1}/{max_retries}...")
            
            result = compile_and_run(current_code)
            
            if result["status"] == "success":
                return jsonify({
                    'code': current_code, 
                    'output': result["output"], 
                    'attempts': attempt + 1
                })
            
            print(f"Error during {result['phase']}. Agent is analyzing the log...")
            
            # If it failed, feed the stderr back to the LLM to fix it
            error_log = result["log"]
            fix_prompt = (
                f"The following C++ code failed during {result['phase']} with this error:\n\n"
                f"{error_log}\n\n"
                f"Here is the broken code:\n{current_code}\n\n"
                f"Analyze the error, fix the C++ code, and provide ONLY the corrected raw C++ code."
            )
            
            response = model.generate_content(fix_prompt)
            current_code = clean_llm_output(response.text)
            
        return jsonify({
            'error': f'Agent failed to compile/run after {max_retries} attempts.', 
            'last_log': result.get("log", "Unknown error"), 
            'code': current_code
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)