#include <windows.h>
#include <stdint.h>
#include <new>
#include "shared-memory-queue.h"
struct Publisher { video_queue_t *q; uint32_t width, height; };
extern "C" void *dlc_create(uint32_t width,uint32_t height,uint32_t fps) {
    if (!width || !height || (width%2) || (height%2) || width>3840 || height>2160 || !fps || fps>120) return nullptr;
    auto *p=new(std::nothrow) Publisher{};
    if (!p) return nullptr;
    p->q=video_queue_create(width,height,10000000ULL/fps);
    if (!p->q) { delete p; return nullptr; }
    p->width=width; p->height=height; return p;
}
extern "C" int dlc_write(void *handle,uint8_t *nv12,uint32_t bytes,uint64_t timestamp) {
    auto *p=static_cast<Publisher *>(handle);
    if (!p || !nv12 || bytes!=p->width*p->height*3/2) return 0;
    uint8_t *planes[2]={nv12,nv12+p->width*p->height};
    uint32_t stride[2]={p->width,p->width};
    video_queue_write(p->q,planes,stride,timestamp); return 1;
}
extern "C" void dlc_close(void *handle) {
    auto *p=static_cast<Publisher *>(handle);
    if(p) { video_queue_close(p->q); delete p; }
}
