# PhysSim — project memory

## Available headers (never invent others)

### animation.hpp
- Class: `Animator`
- `void record_frame(double t, double x, double y)` — EXACTLY 3 args: time, x position, y position
- `void emit_json()` — prints frames to stdout wrapped in `---ANIMATION_DATA---` / `---END_ANIMATION---`
- Do NOT call with 4 or 5 args. Do NOT redefine this class.

### plots.hpp
- Class: `Plotter`
- `void add_data(std::string label, double x, double y)` — one point at a time
- `void emit_json()` — prints data to stdout wrapped in `---PLOT_DATA---` / `---END_PLOT---`
- Do NOT redefine this class or re-implement emit_json.

## Required at the end of every main()
```cpp
anim.emit_json();
plot.emit_json();
```

## Allowed standard headers only
- iostream
- vector
- cmath
- string
- iomanip
- sstream

## Strictly forbidden
- nlohmann/json — NOT installed, will cause compile error
- std::filesystem — NOT available
- Any third-party or non-standard library
- Redefining Animator, Plotter, AnimationFrame, Point, or any struct from the headers

## Output format
- Return ONLY a single ```cpp ... ``` fenced code block
- No explanation, no markdown prose, no headers outside the code block
