import pygame
import math
import psutil

# 初始化Pygame
pygame.init()

# 设置屏幕为全屏模式
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)

# 获取屏幕分辨率
screen_width = screen.get_width()
screen_height = screen.get_height()

# 设置标题
pygame.display.set_caption("多个圆形仪表盘展示")

# 定义仪表盘参数
dashboard_diameter = 200  # 仪表盘直径
dashboard_radius = dashboard_diameter // 2  # 仪表盘半径
dashboard_color = (0, 255, 255)  # 青色
needle_color = (255, 165, 0)  # 橙色
needle_width = 5
needle_length = dashboard_radius * 0.8
min_value = 0
max_value = 100
spacing = 80  # 仪表盘之间的间距

# 计算仪表盘中心位置
num_dashboards = 4  # 仪表盘数量
total_width = (dashboard_diameter + spacing) * num_dashboards - spacing
start_x = (screen_width - total_width) // 2
dashboard_centers = []
for i in range(num_dashboards):
    x = start_x + i * (dashboard_diameter + spacing) + dashboard_radius
    y = screen_height // 2
    dashboard_centers.append((x, y))

# 获取系统信息的函数
def get_cpu_temperature():
    with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
        temp = int(f.read()) / 1000.0
    return temp

def get_network_speed():
    net_io = psutil.net_io_counters()
    return net_io.bytes_sent / 1024 / 1024, net_io.bytes_recv / 1024 / 1024

def get_disk_usage():
    disk = psutil.disk_usage('/')
    return disk.percent

def get_memory_usage():
    memory = psutil.virtual_memory()
    return memory.percent

# 主循环
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

    # 获取系统数据
    cpu_temp = get_cpu_temperature()
    net_sent, net_recv = get_network_speed()
    disk_usage = get_disk_usage()
    memory_usage = get_memory_usage()

    # 绘制背景
    screen.fill((0, 0, 0))

    # 绘制每个仪表盘
    values = [cpu_temp, net_sent, net_recv, memory_usage]
    labels = ["CPU Temp (°C)", "Net Sent (MB)", "Net Recv (MB)", "Memory Usage (%)"]
    for i, center in enumerate(dashboard_centers):
        # 更新仪表盘值
        current_value = values[i]

        # 计算指针角度
        angle = (current_value - min_value) / (max_value - min_value) * 270 - 135  # 从-135到135度
        needle_end_x = center[0] + needle_length * math.cos(math.radians(angle))
        needle_end_y = center[1] + needle_length * math.sin(math.radians(angle))

        # 绘制仪表盘
        pygame.draw.circle(screen, dashboard_color, center, dashboard_radius, 2)
        pygame.draw.line(screen, needle_color, center, (int(needle_end_x), int(needle_end_y)), needle_width)

        # 绘制刻度
        for j in range(0, 360, 6):  # 每6度一个刻度
            tick_angle = j
            tick_end_x = center[0] + dashboard_radius * math.cos(math.radians(tick_angle))
            tick_end_y = center[1] + dashboard_radius * math.sin(math.radians(tick_angle))
            pygame.draw.line(screen, dashboard_color, (int(tick_end_x), int(tick_end_y)), 
                             (int(tick_end_x), int(tick_end_y)), 2)

        # 绘制当前值
        font = pygame.font.Font(None, 36)
        text = font.render(f"{labels[i]}: {current_value:.2f}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(center[0], center[1] + dashboard_radius + 30))
        screen.blit(text, text_rect)

    # 更新屏幕
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(60)

# 退出Pygame
pygame.quit()
