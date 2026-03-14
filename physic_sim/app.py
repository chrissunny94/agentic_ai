import os
import re
import json
import subprocess
from flask import Flask, render_template, request, jsonify

# --- Model SDKs ---
import google.generativeai as genai
from openai import OpenAI
import anthropic

app = Flask(__name__)

# --- API key configuration ---
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))
openai_client    = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))
xai_client       = OpenAI(api_key=os.environ.get("XAI_API_KEY"), base_url="https://api.x.ai/v1")
anthropic_client = anthropic.Anthropic(api_key=os.environ.get("ANTHROPIC_API_KEY"))
# Ollama runs locally — no API key needed
ollama_client    = OpenAI(api_key="ollama", base_url="http://localhost:11434/v1")

# --- Model registry ---
MODELS = {
    "gemini":  "gemini-2.5-flash",
    "chatgpt": "gpt-4o",
    "grok":    "grok-3-fast",
    "claude":  "claude-sonnet-4-6",
    "ollama":  os.environ.get("OLLAMA_MODEL", "llama3.1"),  # override via env var
}

# --- Shared system prompt ---
SYSTEM_INSTRUCTION = (
    "You are an expert physics engine developer. Generate ONLY the code for main.cpp.\n"
    "Pre-existing API available via #include \"animation.hpp\" and \"plots.hpp\":\n"
    "  Animator anim; anim.record_frame(t, x, y);  // exactly 3 args: time, x, y\n"
    "  Plotter plot;  plot.add_data(\"Label\", x, y);\n\n"
    "At the end of main(), call anim.emit_json() and plot.emit_json().\n"
    "IMPORTANT CONSTRAINTS:\n"
    "  - Do NOT use nlohmann/json or any third-party libraries.\n"
    "  - Do NOT use std::filesystem.\n"
    "  - Only use standard headers: iostream, vector, cmath, string, iomanip, sstream.\n"
    "  - animation.hpp and plots.hpp handle all JSON output — do not re-implement it.\n"
    "  - Return ONLY raw C++ code inside a single ```cpp ... ``` block. No prose."
)


# ---------------------------------------------------------------------------
# LLM helpers
# ---------------------------------------------------------------------------

def call_llm(provider: str, messages: list[dict]) -> str:
    """
    Unified LLM call. messages = [{"role": "user"|"assistant", "content": "..."}]
    Returns the raw text response.
    """
    model = MODELS[provider]

    if provider == "gemini":
        # Gemini doesn't support a true system role in generate_content,
        # so we prepend the system instruction to the first user message.
        gemini_model = genai.GenerativeModel(model)
        # Build a single prompt from the message history
        prompt = "\n\n".join(
            f"{'User' if m['role'] == 'user' else 'Assistant'}: {m['content']}"
            for m in messages
        )
        response = gemini_model.generate_content(prompt)
        return response.text

    elif provider in ("chatgpt", "grok", "ollama"):
        client = openai_client if provider == "chatgpt" else \
                 xai_client    if provider == "grok"    else \
                 ollama_client
        openai_messages = [{"role": "system", "content": SYSTEM_INSTRUCTION}] + messages
        response = client.chat.completions.create(
            model=model,
            messages=openai_messages,
        )
        return response.choices[0].message.content

    elif provider == "claude":
        # Anthropic uses a separate system param
        response = anthropic_client.messages.create(
            model=model,
            max_tokens=8096,
            system=SYSTEM_INSTRUCTION,
            messages=messages,
        )
        return response.content[0].text

    else:
        raise ValueError(f"Unknown provider: {provider}")


def clean_llm_output(text: str) -> str:
    """Extract only the C++ code block — strip everything outside fences."""
    match = re.search(r'```(?:cpp|c\+\+)?\n([\s\S]*?)```', text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    # Fallback: drop lines that look like markdown prose
    lines = text.split('\n')
    code_lines = [
        l for l in lines
        if not re.match(r'^\s*(#{1,6}|\*{1,2}|>\s|[-*]\s|\d+\.)', l)
    ]
    return '\n'.join(code_lines).strip()


def parse_simulation_output(raw: str) -> dict:
    """Split stdout into text, animation frames, and plot data."""
    result = {"text": "", "animation": [], "plot": {}}

    anim_match = re.search(
        r'---ANIMATION_DATA---\n(\[.*?\])\n---END_ANIMATION---', raw, re.DOTALL
    )
    if anim_match:
        try:
            result["animation"] = json.loads(anim_match.group(1))
        except json.JSONDecodeError:
            pass

    plot_match = re.search(
        r'---PLOT_DATA---\n(\{.*?\})\n---END_PLOT---', raw, re.DOTALL
    )
    if plot_match:
        try:
            result["plot"] = json.loads(plot_match.group(1))
        except json.JSONDecodeError:
            pass

    text = re.sub(r'\n---ANIMATION_DATA---.*?---END_ANIMATION---', '', raw, flags=re.DOTALL)
    text = re.sub(r'\n---PLOT_DATA---.*?---END_PLOT---', '', text, flags=re.DOTALL)
    result["text"] = text.strip()

    return result


# ---------------------------------------------------------------------------
# Build helpers
# ---------------------------------------------------------------------------

def run_cmake_configure(build_dir="build"):
    result = subprocess.run(
        ["cmake", "-B", build_dir, "-S", "."],
        capture_output=True, text=True, timeout=30
    )
    if result.returncode != 0:
        return {"status": "error", "phase": "Configuration", "log": result.stderr}
    return None


def compile_and_run(cpp_code: str, src_dir="src", build_dir="build", skip_configure=False):
    os.makedirs(src_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)

    with open(os.path.join(src_dir, "main.cpp"), "w") as f:
        f.write(cpp_code)

    if not skip_configure:
        err = run_cmake_configure(build_dir)
        if err:
            return err

    build = subprocess.run(
        ["cmake", "--build", build_dir],
        capture_output=True, text=True, timeout=60
    )
    if build.returncode != 0:
        return {"status": "error", "phase": "Compilation", "log": build.stderr}

    exe = next(
        (os.path.join(build_dir, name) for name in ("sim", "sim.exe")
         if os.path.exists(os.path.join(build_dir, name))),
        None
    )
    if exe is None:
        return {"status": "error", "phase": "Runtime", "log": "Executable not found in build/"}

    run = subprocess.run([exe], capture_output=True, text=True, timeout=30)
    if run.returncode != 0:
        return {"status": "error", "phase": "Runtime", "log": run.stderr}

    return {"status": "success", "output": run.stdout}


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/models', methods=['GET'])
def list_models():
    """Returns the available model keys for the frontend selector."""
    return jsonify(list(MODELS.keys()))


@app.route('/ollama-models', methods=['GET'])
def list_ollama_models():
    """Returns locally available Ollama models by querying the Ollama API."""
    try:
        import urllib.request
        with urllib.request.urlopen("http://localhost:11434/api/tags", timeout=3) as r:
            data = json.loads(r.read())
        names = [m["name"] for m in data.get("models", [])]
        return jsonify({"available": names, "current": MODELS["ollama"]})
    except Exception as e:
        return jsonify({"available": [], "current": MODELS["ollama"], "error": str(e)})


@app.route('/generate', methods=['POST'])
def generate_code():
    data        = request.json
    user_prompt = data.get('prompt', '').strip()
    provider    = data.get('model', 'gemini').lower()

    if not user_prompt:
        return jsonify({'error': 'Empty prompt'}), 400
    if provider not in MODELS:
        return jsonify({'error': f'Unknown model: {provider}. Choose from {list(MODELS.keys())}'}), 400

    # Allow frontend to specify which local Ollama model to use
    if provider == "ollama":
        ollama_model = data.get('ollama_model')
        if ollama_model:
            MODELS["ollama"] = ollama_model

    try:
        # Initial generation — inject system instruction into first user message for Gemini
        first_msg = (
            f"{SYSTEM_INSTRUCTION}\n\nUser: {user_prompt}"
            if provider == "gemini"
            else user_prompt
        )
        messages = [{"role": "user", "content": first_msg}]

        raw      = call_llm(provider, messages)
        current_code = clean_llm_output(raw)
        messages.append({"role": "assistant", "content": current_code})

        for attempt in range(3):
            result = compile_and_run(current_code, skip_configure=(attempt > 0))

            if result["status"] == "success":
                parsed = parse_simulation_output(result["output"])
                return jsonify({
                    'code':     current_code,
                    'output':   parsed,
                    'attempts': attempt + 1,
                    'model':    provider,
                })

            # Build fix message and append to history
            fix_msg = (
                f"The code failed at the {result['phase']} phase.\n"
                f"Error:\n{result['log']}\n\n"
                f"Failing code:\n```cpp\n{current_code}\n```\n\n"
                f"Fix ONLY the error. Keep anim.record_frame(t, x, y) with exactly 3 args. "
                f"Keep anim.emit_json() and plot.emit_json(). "
                f"Return ONLY a single ```cpp ... ``` block."
            )
            messages.append({"role": "user",      "content": fix_msg})
            raw          = call_llm(provider, messages)
            current_code = clean_llm_output(raw)
            messages.append({"role": "assistant", "content": current_code})

        return jsonify({
            'error':    f'Failed after 3 attempts ({result["phase"]} phase)',
            'last_log': result["log"],
            'code':     current_code,
            'model':    provider,
        }), 500

    except subprocess.TimeoutExpired:
        return jsonify({'error': 'Build or run timed out (>60s)'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)
