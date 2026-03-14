#include <cmath> // fix: #include cmath -> include it from the allowed standard headers list

#define PI 3.14159265359
#define G 9.81

struct Point {
    double x, y;
};

class Animator;
class Plotter;

double simulateSpring(double k) {
    std::vector<Point> massPos;
    double totalEnergy = 0;
    
    for (int i = 1; i <= 100; ++i) {
        Point pos;
        pos.x = sin((PI / 5) * i);
        pos.y = 2.0 * sin((PI / 3) * i);
        
        massPos.push_back(pos);
        totalEnergy += (massPos[i - 1].x * massPos[i].x + massPos[i - 1].y * massPos[i].y) *
                        exp(-(i * (log2(k)))) -
                       pow(exp((1.0 / i)), k);
    }
    
    return totalEnergy;
}

int main() {
    double maxEnergy = simulateSpring(3);
    
    Animator anim; // fix: forward declare the class
    for (int i = 1; i <= 100; ++i) {
        Point pos;
        pos.x = sin((PI / 5) * i);
        pos.y = 2.0 * sin((PI / 3) * i);
        
        anim.record_frame(i, pos.x, pos.y);
    }
    
    anim.emit_json();
    
    Plotter plot; // fix: forward declare the class
    for (int i = 1; i <= 100; ++i) {
        Point pt;
        pt.x = pow(exp((1.0 / i)), 3);
        pt.y = sin((PI / 5) * i);
        
        plot.add_data("position", pt.x, pt.y);
    }
    
    plot.emit_json();
    
    return 0;
}