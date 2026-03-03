import os
import subprocess
import re
import sys
import google.generativeai as genai

# Ensure your GEMINI_API_KEY is exported in your WSL terminal
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def clean_llm_output(text):
    """Strips markdown formatting to leave pure C++ code."""
    text = re.sub(r'^```(cpp|c\+\+)?\n', '', text, flags=re.MULTILINE)
    text = re.sub(r'```$', '', text, flags=re.MULTILINE)
    return text.strip()

def compile_and_run(cpp_code, src_dir="src", build_dir="build"):
    """WSL-friendly CMake build and execute step."""
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    with open(os.path.join(src_dir, "main.cpp"), "w") as f:
        f.write(cpp_code)

    # Step 1: WSL / Linux CMake Configure (defaults to Unix Makefiles)
    config_cmd = ["cmake", "-B", build_dir, "-S", "."]
    config_proc = subprocess.run(config_cmd, capture_output=True, text=True)
    if config_proc.returncode != 0:
        return {"status": "error", "phase": "CMake Configure", "log": config_proc.stderr or config_proc.stdout}

    # Step 2: CMake Build
    build_cmd = ["cmake", "--build", build_dir]
    build_proc = subprocess.run(build_cmd, capture_output=True, text=True)
    if build_proc.returncode != 0:
        return {"status": "error", "phase": "Compilation", "log": build_proc.stderr or build_proc.stdout}

    # Step 3: Execution (Linux binary is just 'sim')
    exe_path = os.path.join(build_dir, "sim")
    run_proc = subprocess.run([exe_path], capture_output=True, text=True)
    if run_proc.returncode != 0:
        return {"status": "error", "phase": "Execution", "log": run_proc.stderr or run_proc.stdout}

    return {"status": "success", "output": run_proc.stdout}

def run_agent(prompt):
    print(f"\n[Agent] Received Request: {prompt}\n")
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    # Updated prompt with strict #include requirements for GCC 13
    system_instruction = (
        "You are an expert in computational physics and high-performance C++. "
        "Generate valid, standalone C++ code for the requested simulation. "
        "The code MUST contain a main() function that prints the final results to stdout. "
        "CRITICAL: You MUST explicitly #include <iostream>, <iomanip>, <string>, <vector>, and <cmath> at the top of your file. "
        "You have access to two custom headers: #include \"animation.hpp\" and #include \"plots.hpp\". "
        "Return ONLY the raw C++ code. Do not include markdown blocks or explanations."
    )

    full_prompt = f"{system_instruction}\n\nUser Request: {prompt}"
    response = model.generate_content(full_prompt)
    current_code = clean_llm_output(response.text)

    max_retries = 3
    
    for attempt in range(max_retries):
        print(f"[Agent] Attempt {attempt + 1}/{max_retries} - Compiling and Running...")
        result = compile_and_run(current_code)
        
        if result["status"] == "success":
            print("\n[Success] Simulation Output:\n")
            print(result["output"])
            return
        
        print(f"[Failed] Error during {result['phase']}. Agent is analyzing the log to fix the code...")
        error_log = result["log"]
        
        # The Self-Correction Loop
        fix_prompt = (
            f"The following C++ code failed during {result['phase']} with this error:\n\n"
            f"{error_log}\n\n"
            f"Here is the broken code:\n{current_code}\n\n"
            f"Analyze the error, fix the C++ code, and provide ONLY the corrected raw C++ code."
        )
        response = model.generate_content(fix_prompt)
        current_code = clean_llm_output(response.text)
        
    print(f"\n[Fatal Error] Agent failed after {max_retries} attempts.")
    print(f"Last Log:\n{result['log']}")

if __name__ == '__main__':
    # You can pass the prompt directly via the command line
    if len(sys.argv) > 1:
        user_prompt = " ".join(sys.argv[1:])
    else:
        user_prompt = input("Enter physics simulation prompt: ")
    
    run_agent(user_prompt)
