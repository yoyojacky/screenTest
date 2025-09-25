#!/usr/bin/env python3
"""
Pi 5 GPU 硬解(OpenGL 2.1) + NV12→RGB 渲染 720p MP4
菜单 3 排按钮，点击播放，播完返回菜单，不跳出窗口
"""
import os, sys, threading, queue, subprocess, ctypes
import pygame
import numpy as np
from OpenGL.GL import *
from OpenGL.GL import shaders
from OpenGL.arrays import vbo

# ------------------ 1. 基础配置 ------------------
WIDTH, HEIGHT = 1280, 720
FPS = 30
ROWS = 3
VIDEOS_DIR = "videos"

def scan_videos(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.mp4')]
    files.sort()
    return [os.path.join(folder, f) for f in files]

video_paths = scan_videos(VIDEOS_DIR)
if not video_paths:
    sys.exit(f'在 {VIDEOS_DIR} 目录下没找到任何 mp4 文件')

# ------------------ 2. pygame + OpenGL 2.1 初始化 ------------
pygame.init()
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MAJOR_VERSION, 2)
pygame.display.gl_set_attribute(pygame.GL_CONTEXT_MINOR_VERSION, 1)
pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.OPENGL | pygame.DOUBLEBUF | pygame.FULLSCREEN)
pygame.mouse.set_visible(True)
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 32, bold=True)

# ------------------ 3. OpenGL 2.1 资源 ------------------
# 3.1 全屏三角形
vertices = np.array([
    -1.0, -1.0, 0.0, 0.0, 1.0,
     3.0, -1.0, 0.0, 2.0, 1.0,
    -1.0,  3.0, 0.0, 0.0, -1.0], dtype=np.float32)

vbo_id = glGenBuffers(1)
glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
glBufferData(GL_ARRAY_BUFFER, vertices.nbytes, vertices, GL_STATIC_DRAW)

# 3.2 着色器 (OpenGL 2.1 GLSL 110)
VS = """
#version 110
attribute vec3 pos;
attribute vec2 uv;
varying vec2 vUv;
void main(){
    gl_Position = vec4(pos, 1.0);
    vUv = uv;
}
"""
FS_NV12 = """
#version 110
uniform sampler2D texY;
uniform sampler2D texUV;
varying vec2 vUv;
const mat3 YUV2RGB = mat3(
    1.164,  1.164,  1.164,
    0.0,   -0.392,  2.017,
    1.596, -0.813,  0.0
);
void main(){
    float y  = texture2D(texY,  vUv).r - 0.0625;
    vec2  uv = texture2D(texUV, vUv).rg - vec2(0.5);
    vec3 rgb = YUV2RGB * vec3(y, uv);
    gl_FragColor = vec4(rgb, 1.0);
}
"""
program = shaders.compileProgram(
    shaders.compileShader(VS, GL_VERTEX_SHADER),
    shaders.compileShader(FS_NV12, GL_FRAGMENT_SHADER)
)
glUseProgram(program)

# 3.3 Uniform & texture
texY_loc  = glGetUniformLocation(program, "texY")
texUV_loc = glGetUniformLocation(program, "texUV")
glUniform1i(texY_loc, 0)
glUniform1i(texUV_loc, 1)

# 3.4 VAO (OpenGL 2.1 手动绑定)
vao = glGenVertexArrays(1) if glGenVertexArrays else None
glBindVertexArray(vao) if vao else None
glBindBuffer(GL_ARRAY_BUFFER, vbo_id)
glEnableVertexAttribArray(0)
glVertexAttribPointer(0, 3, GL_FLOAT, False, 5 * 4, ctypes.c_void_p(0))
glEnableVertexAttribArray(1)
glVertexAttribPointer(1, 2, GL_FLOAT, False, 5 * 4, ctypes.c_void_p(3 * 4))

# 3.5 纹理
texY  = glGenTextures(1)
texUV = glGenTextures(1)
for t in (texY, texUV):
    glBindTexture(GL_TEXTURE_2D, t)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)

# ------------------ 4. 解码线程 ------------------
class VideoPlayer:
    def __init__(self, path):
        self.path = path
        self.q = queue.Queue(maxsize=3)
        self.running = False

    def _decode(self):
        cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-hwaccel", "drm",
            "-c:v", "h264_v4l2m2m",
            "-i", self.path,
            "-f", "rawvideo",
            "-pix_fmt", "nv12",
            "-s", f"{WIDTH}x{HEIGHT}",
            "-r", str(FPS),
            "-"
        ]
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)
        frame_size = int(WIDTH * HEIGHT * 1.5)
        while self.running:
            buf = pipe.stdout.read(frame_size)
            if not buf:
                break
            try:
                self.q.put(buf, timeout=1)
            except queue.Full:
                pass
        pipe.kill()

    def play(self):
        self.running = True
        threading.Thread(target=self._decode, daemon=True).start()
        glClearColor(0, 0, 0, 1)
        while True:
            for e in pygame.event.get():
                if e.type in (pygame.QUIT, pygame.KEYDOWN,
                              pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    self.running = False
                    return
            try:
                nv12 = self.q.get_nowait()
                self._render(nv12)
            except queue.Empty:
                pass
            pygame.display.flip()
            clock.tick(FPS)

    def _render(self, nv12):
        y_plane = nv12[:WIDTH * HEIGHT]
        uv_plane = nv12[WIDTH * HEIGHT:]
        # Y texture
        glActiveTexture(GL_TEXTURE0)
        glBindTexture(GL_TEXTURE_2D, texY)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE, WIDTH, HEIGHT, 0,
                     GL_LUMINANCE, GL_UNSIGNED_BYTE, y_plane)
        # UV texture
        glActiveTexture(GL_TEXTURE1)
        glBindTexture(GL_TEXTURE_2D, texUV)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_LUMINANCE_ALPHA, WIDTH // 2, HEIGHT // 2, 0,
                     GL_LUMINANCE_ALPHA, GL_UNSIGNED_BYTE, uv_plane)
        glDrawArrays(GL_TRIANGLES, 0, 3)

# ------------------ 5. 菜单 ------------------
def draw_ui():
    screen = pygame.display.get_surface()
    screen.fill((30, 30, 30))
    for rect, path in buttons:
        pygame.draw.rect(screen, (0, 150, 255), rect, border_radius=12)
        txt = font.render(os.path.basename(path), True, (255, 255, 255))
        screen.blit(txt, txt.get_rect(center=rect.center))
    pygame.display.flip()

# 计算按钮
BUTTONS = len(video_paths)
COLS = (BUTTONS + ROWS - 1) // ROWS
margin = 20
uw, uh = WIDTH - 2 * margin, HEIGHT - 2 * margin
btn_w = uw // COLS - 10
btn_h = uh // ROWS - 10
buttons = []
for idx, path in enumerate(video_paths):
    row, col = divmod(idx, COLS)
    left = margin + col * (btn_w + 10)
    top  = margin + row * (btn_h + 10)
    buttons.append((pygame.Rect(left, top, btn_w, btn_h), path))

running = True
while running:
    draw_ui()
    for e in pygame.event.get():
        if e.type == pygame.QUIT or (e.type == pygame.KEYDOWN and e.key == pygame.K_ESCAPE):
            running = False
        elif e.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            pos = (int(e.x * WIDTH), int(e.y * HEIGHT)) if e.type == pygame.FINGERDOWN else e.pos
            for rect, path in buttons:
                if rect.collidepoint(pos):
                    VideoPlayer(path).play()
                    break
    clock.tick(FPS)

pygame.quit()
