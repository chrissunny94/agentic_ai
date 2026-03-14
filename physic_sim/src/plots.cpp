#include "plots.hpp"   // ADD THIS (was missing — caused 'data' not in scope)
#include <iostream>
#include <map>

void Plotter::add_data(std::string label, double x, double y) {
    data[label].push_back({x, y});
}

void Plotter::emit_json() {
    std::cout << "\n---PLOT_DATA---\n{";
    bool first = true;
    for (auto const& [label, points] : data) {
        if (!first) std::cout << ",";
        first = false;
        std::cout << "\"" << label << "\": [";
        for (size_t i = 0; i < points.size(); ++i) {
            std::cout << "[" << points[i].x << "," << points[i].y << "]"
                      << (i == points.size()-1 ? "" : ",");
        }
        std::cout << "]";
    }
    std::cout << "}\n---END_PLOT---" << std::endl;
}