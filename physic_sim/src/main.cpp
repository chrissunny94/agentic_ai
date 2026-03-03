The compilation errors you're encountering are straightforward and can be resolved by addressing two main issues: a missing header and incorrect scope for member function definitions.

Here's the breakdown of the errors and the corrected code for `plots.hpp`, `plots.cpp`, and the supplementary `animation.hpp` for completeness.

---

### Analysis of Errors:

1.  **`error: ‘map’ in namespace ‘std’ does not name a template type` in `plots.hpp`**
    *   **Cause:** This error, along with the very helpful note `‘std::map’ is defined in header ‘<map>’; did you forget to ‘#include <map>’`, indicates that you're using `std::map` without including its definition.
    *   **Fix:** Add `#include <map>` to `plots.hpp`.

2.  **`error: ‘data’ was not declared in this scope` in `plots.cpp`**
    *   **Cause:** When defining a member function (like `add_data` or `emit_json`) outside its class declaration, you need to use the scope resolution operator (`Plotter::`) to specify which class the function belongs to. Without it, the compiler treats `add_data` and `emit_json` as standalone functions, and `data` (which is a member of `Plotter`) is out of their scope.
    *   **Fix:** Change `void add_data(...)` to `void Plotter::add_data(...)` and `void emit_json(...)` to `void Plotter::emit_json(...)` in `plots.cpp`.

Additionally, the `Point` struct needs to be defined for `std::vector<Point>` to be valid, and `nlohmann/json.hpp` is required for the JSON serialization.

---

### Corrected Code:

**1. Corrected `include/plots.hpp`**

#ifndef PLOTS_HPP
#define PLOTS_HPP

#include <vector>
#include <string>
#include <map> // FIX: Added missing include for std::map

// Define a Point struct as implied by `push_back({x, y})` in plots.cpp
struct Point {
    double x;
    double y;
};

class Plotter {
public:
    std::map<std::string, std::vector<Point>> data;

    // Method declarations
    void add_data(std::string label, double x, double y);
    void emit_json();
};

#endif // PLOTS_HPP

**2. Corrected `src/plots.cpp`**

#include "plots.hpp"
#include <iostream>
#include <fstream> // For file output (e.g., plot_data.json)
#include <nlohmann/json.hpp> // Assuming you're using nlohmann/json for JSON serialization

// FIX: Add Plotter:: scope resolution to define member function
void Plotter::add_data(std::string label, double x, double y) {
    // Access the 'data' member of the current Plotter instance
    // 'this->' is optional here; 'data' alone would also correctly refer to the member.
    data[label].push_back({x, y});
}

// FIX: Add Plotter:: scope resolution to define member function
void Plotter::emit_json() {
    nlohmann::json j_data;

    // Loop through the 'data' member of the current Plotter instance
    // 'this->' is optional here; 'data' alone would also correctly refer to the member.
    for (auto const& [label, points] : data) {
        nlohmann::json point_array = nlohmann::json::array();
        for (const auto& p : points) {
            point_array.push_back({{"x", p.x}, {"y", p.y}});
        }
        j_data[label] = point_array;
    }

    std::cout << "Plotter data JSON:\n" << j_data.dump(2) << std::endl;

    // Optional: Write to a file
    std::ofstream ofs("plot_data.json");
    if (ofs.is_open()) {
        ofs << j_data.dump(2);
        ofs.close();
        std::cout << "Plotter data written to plot_data.json" << std::endl;
    } else {
        std::cerr << "Error: Could not open plot_data.json for writing." << std::endl;
    }
}

**3. Minimal `include/animation.hpp` (for `main.cpp` to compile)**

This file was correctly inferred in your problem description.

#ifndef ANIMATION_HPP
#define ANIMATION_HPP

#include <vector>
#include <string>
#include <fstream>
#include <iostream>
#include <nlohmann/json.hpp> // Assuming nlohmann/json is also used by Animator

struct Frame {
    double time;
    double x_pos;
    double y_pos;
};

class Animator {
public:
    std::vector<Frame> frames;

    void record_frame(double t, double x, double y) {
        frames.push_back({t, x, y});
    }

    void emit_json() {
        nlohmann::json j_frames = nlohmann::json::array();
        for (const auto& frame : frames) {
            j_frames.push_back({
                {"time", frame.time},
                {"x", frame.x_pos},
                {"y", frame.y_pos}
            });
        }

        std::cout << "Animator data JSON:\n" << j_frames.dump(2) << std::endl;

        std::ofstream ofs("animation_data.json");
        if (ofs.is_open()) {
            ofs << j_frames.dump(2);
            ofs.close();
            std::cout << "Animator data written to animation_data.json" << std::endl;
        } else {
            std::cerr << "Error: Could not open animation_data.json for writing." << std::endl;
        }
    }
};

#endif // ANIMATION_HPP

**4. `src/main.cpp` (No changes needed)**

#include <iostream>
#include <vector>
#include <cmath>
#include "animation.hpp"
#include "plots.hpp"

int main() {
    std::cout << "Starting spring simulation..." << std::endl;

    // Simulation parameters
    const double mass = 1.0;
    const double spring_constant = 10.0;
    const double damping_coefficient = 0.5;
    const double initial_position = 1.0;
    const double initial_velocity = 0.0;

    const double time_step = 0.01;
    const double total_time = 20.0;

    // Initialize current state
    double t = 0.0;
    double x = initial_position;
    double v = initial_velocity;

    // Create instances of Animator and Plotter
    Animator anim;
    Plotter plot;

    // Descriptive text for the simulation
    std::cout << "Simulating a mass-spring-damper system." << std::endl;
    std::cout << "Mass: " << mass << " kg" << std::endl;
    std::cout << "Spring Constant: " << spring_constant << " N/m" << std::endl;
    std::cout << "Damping Coefficient: " << damping_coefficient << " Ns/m" << std::endl;
    std::cout << "Initial Position: " << initial_position << " m" << std::endl;
    std::cout << "Initial Velocity: " << initial_velocity << " m/s" << std::endl;
    std::cout << "Time Step: " << time_step << " s" << std::endl;
    std::cout << "Total Simulation Time: " << total_time << " s" << std::endl;

    // Main simulation loop (using Euler integration for simplicity)
    while (t <= total_time) {
        // Record current state for animation (assume 1D horizontal motion, y=0)
        anim.record_frame(t, x, 0.0); // t, x_position, y_position

        // Record current state for plotting
        plot.add_data("Position", t, x);

        // Calculate net force
        double spring_force = -spring_constant * x;
        double damping_force = -damping_coefficient * v;
        double net_force = spring_force + damping_force;

        // Calculate acceleration
        double acceleration = net_force / mass;

        // Update velocity and position using Euler integration
        v += acceleration * time_step;
        x += v * time_step;

        // Advance time
        t += time_step;
    }

    std::cout << "Simulation finished. Emitting data..." << std::endl;

    // Emit collected data to the frontend
    anim.emit_json();
    plot.emit_json();

    std::cout << "Data emitted successfully." << std::endl;

    return 0;
}

---

To compile this, ensure you have the `nlohmann/json` header-only library available in your include path. If you downloaded `json.hpp`, place it where your compiler can find it (e.g., in an `include` directory, or next to your source files for a simple project). Your `CMakeLists.txt` or Makefile should then compile `src/plots.cpp` and `src/main.cpp`.