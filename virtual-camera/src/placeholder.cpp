#include <cstdint>
#include <vector>
static std::vector<uint8_t> pixels;
bool initialize_placeholder() { pixels.assign(1280*720*3/2,128); std::fill(pixels.begin(),pixels.begin()+1280*720,16); return true; }
const uint8_t *get_placeholder_ptr() { return pixels.data(); }
const bool get_placeholder_size(int *x,int *y) { *x=1280; *y=720; return true; }
