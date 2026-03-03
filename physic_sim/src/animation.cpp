#include "animation.hpp"
#include <iostream>

void Animator::record_frame(double t, double x, double y) {
    frames.push_back({t, x, y});
}

void Animator::emit_json() {
    std::cout << "\n---ANIMATION_DATA---\n[";
    for (size_t i = 0; i < frames.size(); ++i) {
        std::cout << "{\"t\":" << frames[i].time << ",\"x\":" << frames[i].x << ",\"y\":" << frames[i].y << "}" 
                  << (i == frames.size()-1 ? "" : ",");
    }
    std::cout << "]\n---END_ANIMATION---" << std::endl;
}