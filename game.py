import os 
import pygame 
import subprocess


WIDTH, HEIGHT = 1280, 720
FPS = 30
ROWS = 3 
VIDEOS_DIR = "videos"
PLAYER = "vlc"

def scan_videos(folder):
    files = [f for f in os.listdir(folder) if f.lower().endswith('.mp4')]
    files.sort()
    return [os.path.join(folder, f) for f in files]

video_paths = scan_videos(VIDEOS_DIR)
if not video_paths:
    raise RuntimeError(f"在{VIDEO_DIR} 目录下没有找到任何mp4文件")

os.environ["SDL_VIDEO_CENTERED"] = "1"
pygame.init()
pygame.mouse.set_visible(True)
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Pi5 视频小游戏")
clock = pygame.time.Clock()

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

font = pygame.font.SysFont('arial', 28, bold=True)

def draw_ui():
    screen.fill((30,30,30))
    for rect, path in buttons:
        pygame.draw.rect(screen, (0, 150, 255), rect, border_radius=12)
        txt = os.path.basename(path)
        surf = font.render(txt, True, (255,255,255))
        screen.blit(surf, surf.get_rect(center=rect.center))
    pygame.display.flip()


def play_video(path):
    cmd = [
            "vlc",
            "--fullscreen",
            "--play-and-exit",
            "--no-video-title-show",
            "--mouse-hide-timeout", "0", path
            ]
    subprocess.run(cmd, check=False)

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
                    play_video(path)
                    break 
    clock.tick(FPS)
pygame.quit()

