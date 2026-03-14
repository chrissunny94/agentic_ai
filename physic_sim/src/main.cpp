#include "animation.hpp"
#include "plots.hpp"

int main() {
    double k = 4.0; // Spring constant (in N/m)
    double m = 2.0; // Mass of the object attached to spring (in kg)
    double x0 = 10.0; // Initial displacement (in meters)
    double v0 = 5.0; // Initial velocity (in m/s)

    Animator anim;
    Plotter plot;

    double dt = 0.01;
    double t = 0;

    while (t < 10) {
        double x = (x0 - k * v0 / m) * pow(m / (k * cos(M_PI * sqrt(k / m))), cos(t));
        double v = v0 + (-k * v0 / m) * dt / cos(M_PI * sqrt(k / m));

        anim.record_frame(t, x, 0);

        plot.add_data("displacement", t, x);
        plot.add_data("velocity", t, v);

        t += dt;
    }

    cout << "Simulation successful." << endl;

    anim.emit_json();
    plot.emit_json();

    return 0;
}