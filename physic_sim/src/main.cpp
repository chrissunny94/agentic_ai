#include "iostream"
#include "vector"
#include "cmath"
#include "string"
#include "iomanip"

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
        pos.x = math.sin((PI / 5) * i);
        pos.y = 2.0 * sin((PI / 3) * i);
        
        massPos.push_back(pos);
        totalEnergy += (massPos[i - 1].x * massPos[i].x + massPos[i - 1].y * massPos[i].y) *
                        math.exp(-(i * (math.log2(k)))) -
                       pow(math.exp((1.0 / i)), k);
    }
    
    return totalEnergy;
}

int main() {
    double maxEnergy = simulateSpring(3);
    
    Animator anim;
    for (int i = 1; i <= 100; ++i) {
        Point pos;
        pos.x = sin((PI / 5) * i);
        pos.y = 2.0 * sin((PI / 3) * i);
        
        anim.record_frame(i, pos.x, pos.y);
    }
    
    anim.emit_json();
    
    Plotter plot;
    for (int i = 1; i <= 100; ++i) {
        Point pt;
        pt.x = pow(math.exp((1.0 / i)), 3);
        pt.y = sin((PI / 5) * i);
        
        plot.add_data("position", pt.x, pt.y);
    }
    
    plot.emit_json();
    
    return 0;
}