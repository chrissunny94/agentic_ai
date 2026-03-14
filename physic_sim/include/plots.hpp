#pragma once
#include <string>
#include <vector>
#include <map>        // ADD THIS

struct Point { double x; double y; };   // ADD THIS

class Plotter {
public:
    void add_data(std::string label, double x, double y);
    void emit_json();
private:
    std::map<std::string, std::vector<Point>> data;
};