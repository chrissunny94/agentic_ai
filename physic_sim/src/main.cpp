// include/animation.hpp
#include <string> // Assuming this is present for other methods
// ...
class Animator {
public:
    // Problematic line:
    void record_frame(double t, double x, double y);
    // ... other methods ...
    void emit_json(); // Assuming this is present
};