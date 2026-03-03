#pragma once
#include <vector>

struct State {
    double time;
    double x, y; // Position for animation
};

class Animator {
public:
    void record_frame(double t, double x, double y);
    void emit_json();
private:
    std::vector<State> frames;
};