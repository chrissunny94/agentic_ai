#pragma once
#include <vector>
#include <string>

class Plotter {
public:
    void add_data(std::string label, double x, double y);
    void emit_json(); // Prints the data in JSON format at the end
private:
    struct Point { double x, y; };
    std::map<std::string, std::vector<Point>> data;
};