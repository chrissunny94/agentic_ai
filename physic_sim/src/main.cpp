#include "animation.hpp"
#include "plots.hpp"

int main() {
    double k = 0.1; // spring constant
    double m = 1.0; // mass of the object attached to the spring
    int num_steps = 100;

    std::vector<double> x(num_steps), v(num_steps);
    x[0] = 2.0;
    v[0] = 3.0;

    for (int i = 1; i < num_steps; ++i) {
        v[i] = v[i-1] - k * (x[i-1] - 5.0) / m;
        x[i] = x[i-1] + v[i-1];
    }

    double t[num_steps];
    for(int i = 0; i < num_steps; ++i)
        t[i] = static_cast<double>(i) * 10.0; // assuming t[i+1] - t[i] = 10

    Animator anim;
    for (int i = 0; i < num_steps; ++i)
        anim.record_frame(t[i], x[i]);

    Plotter plot;
    for (int i = 0; i < num_steps-1; ++i) {
        std::stringstream ss;
        ss << "t[" << i << "]";
        plot.add_data(ss.str(), t[i+1] - t[i]);
    }

    int num_points = num_steps;

    Plotter position_plot;
    for (int i = 0; i < num_points-1; ++i) {
        std::stringstream ss1, ss2;
        ss1 << "t[" << i << "]";
        ss2 << "x";
        position_plot.add_data(ss1.str() + " - " + ss2.str(), x[i+1]);
    }

    int frames_per_second = 25;

    double frame_duration = 1000.0 / frames_per_second;
    for (int i = 0; i < num_points-1; ++i) {
        std::stringstream ssmm, ssmmm;
        ssmm << "t[" << i << "]";
        ssmmm << (x[i+1] - x[i]) / frame_duration;
        position_plot.add_data(ssmm.str() + " mm/s", ssmmm.str());
    }

    anim.emit_json();
    plot.emit_json();
    return 0;
}