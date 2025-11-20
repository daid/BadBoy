cmake_minimum_required(VERSION 3.10)
project(SweepEmu)

find_package(SDL2 REQUIRED)
if(NOT DEFINED SDL2_LIBRARIES)
    set(SDL2_LIBRARIES SDL2::SDL2)
endif()

file(GLOB_RECURSE SOURCES src/*.cpp src/*.h)
set(BINJGB_DIR ${CMAKE_CURRENT_SOURCE_DIR}/../../binjgb/)
set(BINJGB_SRC
    ${BINJGB_DIR}/src/emulator.c
    ${BINJGB_DIR}/src/emulator.h
    ${BINJGB_DIR}/src/common.c
    ${BINJGB_DIR}/src/common.h
)
add_executable(${CMAKE_PROJECT_NAME} ${SOURCES} ${BINJGB_SRC})
target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC ${BINJGB_DIR}/src)

target_compile_options(${CMAKE_PROJECT_NAME} PUBLIC -Wall)
target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC ${SDL2_LIBRARIES})
target_include_directories(${CMAKE_PROJECT_NAME} PUBLIC ${SDL2_INCLUDE_DIRS})
if(WIN32)
    target_link_libraries(${CMAKE_PROJECT_NAME} PUBLIC -mconsole)
endif()