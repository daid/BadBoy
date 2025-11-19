cmake_minimum_required(VERSION 3.10)
project(BadBoy)

find_package(SDL2 REQUIRED)
if(NOT DEFINED SDL2_LIBRARIES)
    set(SDL2_LIBRARIES SDL2::SDL2)
endif()

file(GLOB_RECURSE SOURCES src/*.cpp src/*.h)
add_executable(${CMAKE_PROJECT_NAME} ${SOURCES})

target_compile_options(${CMAKE_PROJECT_NAME} PUBLIC -Wall)
target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC ${SDL2_LIBRARIES})
target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC ${SDL2_INCLUDE_DIRS})
if(WIN32)
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC -mconsole)
endif()
