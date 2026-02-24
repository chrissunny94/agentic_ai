#include <iostream> // Required for input/output operations (std::cout)
#include <cmath>    // Required for mathematical functions (not strictly used in this basic version, but good practice for physics simulations)

// No custom headers "animation.hpp" or "plots.hpp" are included
// as plotting or animation were not explicitly requested by the user.

int main() {
    // 1. Simulation Parameters
    const double mass = 1.0;            // Mass of the object (kg)
    const double spring_constant = 10.0; // Spring constant (N/m)
    const double damping_coefficient = 0.5; // Damping coefficient (Ns/m). Set to 0.0 for an undamped system.

    // 2. Initial Conditions
    double position = 1.0;              // Initial displacement from equilibrium (m)
    double velocity = 0.0;              // Initial velocity (m/s)

    // 3. Time Parameters
    const double dt = 0.001;            // Time step (s)
    const double total_time = 10.0;     // Total simulation time (s)
    
    // Calculate the number of simulation steps
    const int num_steps = static_cast<int>(total_time / dt);

    double current_time = 0.0;          // Current simulation time

    // Print initial conditions for context
    std::cout << "----------------------------------------\n";
    std::cout << "Spring-Mass-Damper Simulation\n";
    std::cout << "Initial Conditions:\n";
    std::cout << "  Mass:              " << mass << " kg\n";
    std::cout << "  Spring Constant:   " << spring_constant << " N/m\n";
    std::cout << "  Damping Coeff:     " << damping_coefficient << " Ns/m\n";
    std::cout << "  Initial Position:  " << position << " m\n";
    std::cout << "  Initial Velocity:  " << velocity << " m/s\n";
    std::cout << "  Time Step (dt):    " << dt << " s\n";
    std::cout << "  Total Time:        " << total_time << " s\n";
    std::cout << "----------------------------------------\n";
    std::cout << "\nStarting simulation...\n\n";

    // 4. Simulation Loop
    // Iteratively update position and velocity over time
    for (int i = 0; i < num_steps; ++i) {
        // Calculate forces acting on the mass
        double spring_force = -spring_constant * position;
        double damping_force = -damping_coefficient * velocity;
        double net_force = spring_force + damping_force;

        // Calculate acceleration using Newton's second law (F = ma => a = F/m)
        double acceleration = net_force / mass;

        // 5. Update State using Explicit Euler Integration
        // We use the current position and velocity to calculate the state at the next time step.
        double next_position = position + velocity * dt;
        double next_velocity = velocity + acceleration * dt;

        // Update the state variables for the next iteration
        position = next_position;
        velocity = next_velocity;

        // Advance the simulation time
        current_time += dt;
    }

    // Print the final results of the simulation to stdout
    std::cout << "Simulation finished after " << num_steps << " steps.\n";
    std::cout << "----------------------------------------\n";
    std::cout << "Final Results:\n";
    std::cout << "  Final Time:     " << current_time << " s\n";
    std::cout << "  Final Position: " << position << " m\n";
    std::cout << "  Final Velocity: " << velocity << " m/s\n";
    std::cout << "----------------------------------------\n";

    return 0; // Indicate successful execution
}