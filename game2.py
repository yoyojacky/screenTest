#!/usr/bin/env python3
"""
Raspberry Pi 5 触摸屏 3 排按钮小游戏
1280×720 分辨率，3 排按钮，点击按钮播放 MP4
使用 FFmpeg 把 MP4 逐帧解码到 pygame Surface，不跳出窗口
"""
import os
import sys
import subprocess
import threading
import queue
import pygame
import numpy as np

# ------------------ 1. 基础配置 ------------------
WIDTH, HEIGHT = 1280, 720
FPS = 30
ROWS = 3
VIDEOS_DIR = "videos"

# ------------------ 2. 扫描视频 ------------------
def scan_videos(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.mp4')]
    files.sort()
    return [os.path.join(folder, f) for f in files]

video_paths = scan_videos(VIDEOS_DIR)
if not video_paths:
    sys.exit(f'在 {VIDEOS_DIR} 目录下没找到任何 mp4 文件')

# ------------------ 3. pygame 初始化 ------------
pygame.init()
pygame.mouse.set_visible(True)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pi 视频按钮小游戏")
clock = pygame.time.Clock()
font = pygame.font.SysFont('arial', 28, bold=True)

# ------------------ 4. 按钮布局 ------------------
BUTTONS = len(video_paths)
COLS = (BUTTONS + ROWS - 1) // ROWS
margin = 20
usable_w = WIDTH - 2 * margin
usable_h = HEIGHT - 2 * margin
btn_w = usable_w // COLS - 10
btn_h = usable_h // ROWS - 10

buttons = []
for idx, path in enumerate(video_paths):
    row = idx // COLS
    col = idx % COLS
    left = margin + col * (btn_w + 10)
    top = margin + row * (btn_h + 10)
    rect = pygame.Rect(left, top, btn_w, btn_h)
    buttons.append((rect, path))

# ------------------ 5. 视频播放逻辑 ------------------
class VideoPlayer:
    """
    用 FFmpeg 解码，线程读取帧，主线程 blit 到 pygame
    """
    def __init__(self, filepath, target_surface):
        self.path = filepath
        self.surface = target_surface
        self.q = queue.Queue(maxsize=3)   # 缓冲 3 帧，防止卡顿
        self.running = False
        self.thread = None

    def _reader(self):
        """
        FFmpeg 子进程：输出原始 RGB24 数据
        """
        cmd = [
            "ffmpeg",
            "-loglevel", "error",
            "-hwaccel", "drm",
            "-c:v", "h254_v4l2m2m",
            "-f", "rawvideo",
            "-pix_fmt", "NV12",
            "-s", f"{WIDTH}x{HEIGHT}", 
            "-r", str(FPS),
            "-"                      # 输出到 stdout
        ]
        pipe = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, bufsize=10**8)

        w, h = WIDTH, HEIGHT
        frame_size = w * h * 3

        while self.running:
            raw = pipe.stdout.read(frame_size)
            if not raw:
                break
            frame = np.frombuffer(raw, dtype=np.uint8).reshape((h, w, 3))
            frame = np.swapaxes(frame, 0, 1)  # (w,h,3) -> 方便 pygame
            try:
                self.q.put(frame, timeout=1)
            except queue.Full:
                pass   # 主线程来不及消费，丢弃
        pipe.kill()

    def play(self):
        """阻塞播放，直到视频结束或用户退出"""
        self.running = True
        self.thread = threading.Thread(target=self._reader, daemon=True)
        self.thread.start()

        black = pygame.Surface((WIDTH, HEIGHT))
        black.fill((0, 0, 0))

        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.stop()
                    return
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.stop()
                    return
                elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
                    self.stop()
                    return

            try:
                frame = self.q.get_nowait()
                img = pygame.surfarray.make_surface(frame)
                screen.blit(img, (0, 0))
            except queue.Empty:
                screen.blit(black, (0, 0))  # 防止花屏
            pygame.display.flip()
            clock.tick(FPS)

        self.stop()

    def stop(self):
        self.running = False
        if self.thread and self.thread.is_alive():
            self.thread.join(timeout=0.5)

# ------------------ 6. 主菜单循环 ------------------
def draw_ui():
    screen.fill((30, 30, 30))
    for rect, path in buttons:
        pygame.draw.rect(screen, (0, 150, 255), rect, border_radius=12)
        txt = os.path.basename(path)
        surf = font.render(txt, True, (255, 255, 255))
        screen.blit(surf, surf.get_rect(center=rect.center))
    pygame.display.flip()

running = True
while running:
    draw_ui()
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
        elif event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            pos = (int(event.x * WIDTH), int(event.y * HEIGHT)) \
                  if event.type == pygame.FINGERDOWN else event.pos
            for rect, path in buttons:
                if rect.collidepoint(pos):
                    player = VideoPlayer(path, screen)
                    player.play()          # 阻塞到播完或用户退出
                    break
    clock.tick(FPS)

pygame.quit()
