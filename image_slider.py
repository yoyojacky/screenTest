import pygame
import os

# 初始化Pygame
pygame.init()

# 设置屏幕分辨率
#screen_width = 1424
#screen_height = 680
#screen = pygame.display.set_mode((screen_width, screen_height))
# 设置屏幕为全屏模式
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# 获取屏幕分辨率
screen_width = screen.get_width()
screen_height = screen.get_height()

# 设置标题
pygame.display.set_caption("触摸图片滚动展示")

# 加载图片
image_folder = "images"  # 图片文件夹路径
images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith(('.png', '.jpg', '.jpeg'))]
current_image_index = 0

# 图片滚动速度
scroll_speed = 10

# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN:
            # 检测触摸位置，滚动图片
            if event.button == 1:  # 左键
                current_image_index = (current_image_index + 1) % len(images)
            elif event.button == 3:  # 右键
                current_image_index = (current_image_index - 1) % len(images)

    # 加载当前图片并调整大小
    try:
        image = pygame.image.load(images[current_image_index])
        image = pygame.transform.scale(image, (screen_width, screen_height))
    except Exception as e:
        print(f"Error loading image: {e}")
        running = False

    # 绘制图片
    screen.blit(image, (0, 0))

    # 更新屏幕
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(60)

# 退出Pygame
pygame.quit()
