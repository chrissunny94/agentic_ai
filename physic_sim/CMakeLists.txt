cmake_minimum_required(VERSION 3.15)
project(AgenticPhysicsSim VERSION 1.0)

# Set C++ standard
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED True)

# Expose the include directory to the agent
include_directories(include)

# Gather all static source files
set(STATIC_SOURCES 
    src/animation.cpp 
    src/plots.cpp
)

# Compile the agent's generated main.cpp alongside your static tools
add_executable(sim 
    src/main.cpp 
    ${STATIC_SOURCES}
)