import pygame
import sys
import random
import math

pygame.init()

# ---------- Дэлгэц ба үндсэн тохиргоо ----------
WIDTH, HEIGHT = 720, 480
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Day-Night Pixel Landscape with Moon & Stars")

clock = pygame.time.Clock()

# ---------- Өнгө палитр ----------
MOUNTAIN_LIGHT = (210, 190, 160)
MOUNTAIN_DARK = (70, 100, 150)
GRASS = (100, 150, 80)
TREE = (40, 90, 50)
GROUND = (90, 60, 40)
ROCK = (60, 70, 80)
CLOUD = (240, 245, 250)
SUN_COLOR = (255, 230, 150)
MOON_COLOR = (230, 230, 255)

# ---------- Үүлс ----------
clouds = [
    [100, 70, 100, 30],
    [250, 50, 120, 40],
    [450, 80, 150, 35],
    [580, 60, 90, 30]
]
cloud_speed = 0.3

# ---------- Sparkle (газрын гялтганах effect) ----------
sparkles = [(random.randint(0, WIDTH), random.randint(350, 420)) for _ in range(25)]

# ---------- Одод ----------
stars = [(random.randint(0, WIDTH), random.randint(0, 250)) for _ in range(70)]

# ---------- Өдрийн мөчлөг ----------
time_angle = 0  # 0–2π мөчлөг

def lerp_color(c1, c2, t):
    return (
        int(c1[0] + (c2[0] - c1[0]) * t),
        int(c1[1] + (c2[1] - c1[1]) * t),
        int(c1[2] + (c2[2] - c1[2]) * t),
    )

def get_sky_color(t):
    """Тэнгэрийн өнгө (үүр → өдөр → орой → шөнө)"""
    if t < 0.25:
        return lerp_color((30, 40, 90), (138, 197, 255), t * 4)
    elif t < 0.5:
        return lerp_color((138, 197, 255), (255, 150, 80), (t - 0.25) * 4)
    elif t < 0.75:
        return lerp_color((255, 150, 80), (10, 15, 40), (t - 0.5) * 4)
    else:
        return lerp_color((10, 15, 40), (30, 40, 90), (t - 0.75) * 4)

def draw_scene(sky_color, sun_y, moon_y, t):
    # Тэнгэрийн өнгө
    screen.fill(sky_color)

    # Нар (өдрийн үед л)
    if t < 0.55:
        pygame.draw.circle(screen, SUN_COLOR, (600, int(sun_y)), 40)

    # Сар (шөнийн үед л)
    if t > 0.45:
        moon_x = 120
        pygame.draw.circle(screen, MOON_COLOR, (moon_x, int(moon_y)), 35)
        # Сарны гэрэлт сүүдэр (crescent effect)
        pygame.draw.circle(screen, sky_color, (moon_x - 10, int(moon_y)), 28)

    # Одод (шөнө гарах)
    if t > 0.55:
        for (x, y) in stars:
            brightness = random.randint(150, 255)
            pygame.draw.circle(screen, (brightness, brightness, 255), (x, y), 1)

    # Үүлс
    for c in clouds:
        pygame.draw.ellipse(screen, CLOUD, c)

    # Уул
    pygame.draw.polygon(screen, MOUNTAIN_DARK, [(0, 300), (250, 150), (450, 170), (700, 320), (WIDTH, HEIGHT), (0, HEIGHT)])
    pygame.draw.polygon(screen, MOUNTAIN_LIGHT, [(150, 200), (360, 100), (520, 180), (700, 300), (WIDTH, HEIGHT), (0, HEIGHT)])

    # Газар
    pygame.draw.rect(screen, GRASS, (0, 320, WIDTH, 100))
    pygame.draw.rect(screen, GROUND, (0, 400, WIDTH, 80))

    
            # Мод (иш голд байрласан)
    tree_positions = [80, 160, 280, 400, 560, 640]
    for x in tree_positions:
        # Навчны доод суурь 40px өргөн → ишийг төвд 8px өргөнөөр зурах
        trunk_width = 8
        trunk_height = 30
        tree_base_y = 360
        tree_top_y = tree_base_y - trunk_height
        trunk_x = x + 20 - trunk_width // 2  # ишийг навчны голд төвлөрүүлэх

        # Иш
        pygame.draw.rect(screen, (70, 40, 20), (trunk_x, tree_base_y, trunk_width, trunk_height))

        # Навчны 2 давхар гурвалжин
        pygame.draw.polygon(screen, TREE, [(x, tree_base_y), (x + 20, tree_base_y - 30), (x + 40, tree_base_y)])
        pygame.draw.polygon(screen, TREE, [(x, tree_base_y - 15), (x + 20, tree_base_y - 45), (x + 40, tree_base_y - 15)])



    # Газрын гялтганах effect
    brightness = int(255 * (1 - abs(math.sin(time_angle))))
    for (x, y) in sparkles:
        pygame.draw.circle(screen, (brightness, brightness, brightness), (x, y), 1)

def move_clouds():
    for c in clouds:
        c[0] += cloud_speed
        if c[0] > WIDTH:
            c[0] = -c[2]

# ---------- Үндсэн loop ----------
while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

    move_clouds()

    # Өдрийн мөчлөг 0–2π
    time_angle += 0.002
    if time_angle > 2 * math.pi:
        time_angle = 0

    # 0–1 хооронд хувиргах
    t = (math.sin(time_angle) + 1) / 2

    # Тэнгэр, нар, сарны хөдөлгөөн
    sky_color = get_sky_color(t)
    sun_y = 300 - math.sin(time_angle) * 250
    moon_y = 300 + math.sin(time_angle) * 250

    draw_scene(sky_color, sun_y, moon_y, t)

    pygame.display.flip()
    clock.tick(60)


