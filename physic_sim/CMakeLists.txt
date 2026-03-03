cmake_minimum_required(VERSION 3.10)
project(PhysicSim)

set(CMAKE_CXX_STANDARD 17)

# 1. Define the "Standard" library (Static parts)
add_library(phys_utils STATIC 
    src/animation.cpp 
    src/plots.cpp
)
target_include_directories(phys_utils PUBLIC include)

# 2. Define the LLM-generated executable
# This will only re-link main.cpp when it changes
add_executable(sim src/main.cpp)
target_link_libraries(sim phys_utils)