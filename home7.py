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
inner_radius = dashboard_radius + 20  # 内圈半径，距离外圈20像素
tick_length = 15  # 刻度线长度
label_offset = 30  # 标签偏移量，控制标签距离刻度线的距离
dashboard_color = (0, 255, 255)  # 青色
needle_color = (255, 165, 0)  # 橙色
needle_width = 3
needle_length = dashboard_radius * 0.7
spacing = 90  # 仪表盘之间的间距

# 仪表盘配置
dashboards = [
    {"name": "CPU Temp (°C)", "min_value": 30, "max_value": 90},
    {"name": "Net Sent (MB)", "min_value": 0, "max_value": 1024},
    {"name": "Net Recv (MB)", "min_value": 0, "max_value": 1024},
    {"name": "Memory Usage (%)", "min_value": 0, "max_value": 100},
    {"name": "CPU Usage (%)", "min_value": 0, "max_value": 100}
]

# 计算仪表盘中心位置
num_dashboards = len(dashboards)  # 仪表盘数量
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

def get_cpu_usage():
    return psutil.cpu_percent()

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
    cpu_usage = get_cpu_usage()

    # 绘制背景
    screen.fill((0, 0, 0))

    # 绘制每个仪表盘
    for i, center in enumerate(dashboard_centers):
        dashboard = dashboards[i]
        # 更新仪表盘值
        if dashboard["name"] == "CPU Temp (°C)":
            current_value = cpu_temp
        elif dashboard["name"] == "Net Sent (MB)":
            current_value = net_sent
        elif dashboard["name"] == "Net Recv (MB)":
            current_value = net_recv
        elif dashboard["name"] == "Memory Usage (%)":
            current_value = memory_usage
        elif dashboard["name"] == "CPU Usage (%)":
            current_value = cpu_usage

        # 计算指针角度
        angle = (current_value - dashboard["min_value"]) / (dashboard["max_value"] - dashboard["min_value"]) * 270 -135
        needle_end_x = center[0] + needle_length * math.cos(math.radians(angle))
        needle_end_y = center[1] + needle_length * math.sin(math.radians(angle))

        # 绘制仪表盘外圈
        pygame.draw.circle(screen, dashboard_color, center, dashboard_radius, 2)

        # 绘制仪表盘内圈刻度
        for j in range(0, 360, 30):  # 每30度一个刻度
            tick_angle = math.radians(j + 135)  # 从135度开始
            tick_end_x = center[0] + inner_radius * math.cos(tick_angle)
            tick_end_y = center[1] + inner_radius * math.sin(tick_angle)
            tick_start_x = center[0] + (inner_radius - tick_length) * math.cos(tick_angle)
            tick_start_y = center[1] + (inner_radius - tick_length) * math.sin(tick_angle)
            pygame.draw.line(screen, dashboard_color, (int(tick_start_x), int(tick_start_y)), (int(tick_end_x), int(tick_end_y)), 2)

            # 绘制刻度标签
            if j % 30 == 0:  # 每30度绘制一个标签
                label = str(int((j // 30) * (dashboard["max_value"] // 10)))
                font = pygame.font.Font(None, 18)
                text = font.render(label, True, (255, 255, 255))
                text_rect = text.get_rect(center=(int(tick_end_x), int(tick_end_y)))
                # 旋转标签以匹配刻度方向
                text_surface = pygame.transform.rotate(text, -(j + 135))
                text_rect.center = (int(tick_end_x), int(tick_end_y))
                screen.blit(text_surface, text_rect)

        # 绘制指针
        pygame.draw.line(screen, needle_color, center, (int(needle_end_x), int(needle_end_y)), needle_width)

        # 绘制当前值
        font = pygame.font.Font(None, 24)
        text = font.render(f"{dashboard['name']}: {current_value:.2f}", True, (255, 255, 255))
        text_rect = text.get_rect(center=(center[0], center[1] + dashboard_radius // 2 + 80))
        screen.blit(text, text_rect)

    # 更新屏幕
    pygame.display.flip()

    # 控制帧率
    pygame.time.Clock().tick(60)

# 退出Pygame
pygame.quit()
