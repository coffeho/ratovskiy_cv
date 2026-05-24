"""
Шарик по нарисованной дороге — Pymunk + Pygame + OpenCV
SPACE — запуск/сброс | P — пауза | D — дебаг | Q/ESC — выход
"""

import math
import sys
import time

import cv2
import numpy as np
import pygame
import pymunk

# ── Настройки ──────────────────────────────────────────────
W, H = 640, 480
FPS = 60
RADIUS = 14
GRAVITY = 900
STEPS = 8
TRAIL_MAX = 50
DETECT_EVERY = 6  # кадров между пересчётом дороги
BLUR_KERNEL = 9  # размытие по Гауссу перед детекцией (нечётное: 3,5,7,9,11...)
SEG_EPSILON = 6  # точность аппроксимации кривых: меньше = больше отрезков, точнее


# ── Физический мир ─────────────────────────────────────────
space = pymunk.Space()
space.gravity = (0, GRAVITY)  # Y вниз совпадает с Pygame
space.damping = 0.995

# Невидимый пол + боковые стенки
for a, b in [
    ((-100, H + 50), (W + 100, H + 50)),
    ((-5, -100), (-5, H + 100)),
    ((W + 5, -100), (W + 5, H + 100)),
]:
    s = pymunk.Segment(space.static_body, a, b, 3)
    s.friction, s.elasticity = 0.4, 0.2
    space.add(s)

road_shapes = []


def set_road(segments):
    global road_shapes
    for sh in road_shapes:
        space.remove(sh)
    road_shapes = []
    for (x1, y1), (x2, y2) in segments:
        s = pymunk.Segment(space.static_body, (x1, y1), (x2, y2), 3)
        s.friction, s.elasticity = 0.85, 0.25
        space.add(s)
        road_shapes.append(s)


ball_body, ball_shape = None, None


def spawn_ball(x, y):
    global ball_body, ball_shape
    if ball_body:
        space.remove(ball_shape, ball_body)
    body = pymunk.Body(1, pymunk.moment_for_circle(1, 0, RADIUS))
    body.position = (x, y)
    sh = pymunk.Circle(body, RADIUS)
    sh.friction, sh.elasticity = 0.75, 0.4
    space.add(body, sh)
    ball_body, ball_shape = body, sh


# ── Детекция дороги ────────────────────────────────────────
def detect_segments(frame):
    # Размытие по Гауссу подавляет шум и склеивает разрывы линий
    k_size = BLUR_KERNEL if BLUR_KERNEL % 2 == 1 else BLUR_KERNEL + 1
    gray = cv2.GaussianBlur(
        cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), (k_size, k_size), 0
    )
    mask = cv2.adaptiveThreshold(
        gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 21, 8
    )
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    for lo, hi in [
        ([0, 0, 0], [180, 255, 90]),
        ([0, 100, 50], [10, 255, 255]),
        ([170, 100, 50], [180, 255, 255]),
        ([100, 100, 50], [130, 255, 255]),
        ([35, 100, 50], [85, 255, 255]),
    ]:
        mask |= cv2.inRange(hsv, np.array(lo), np.array(hi))
    k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
    mask = cv2.morphologyEx(
        cv2.morphologyEx(mask, cv2.MORPH_CLOSE, k, iterations=2),
        cv2.MORPH_OPEN,
        k,
        iterations=1,
    )
    mask = cv2.dilate(mask, cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11)))

    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    clean = np.zeros_like(mask)
    segs = []
    for c in cnts:
        if cv2.contourArea(c) < 400:
            continue
        cv2.drawContours(clean, [c], -1, 255, -1)
        # approxPolyDP разбивает кривой контур на короткие отрезки —
        # просветов нет, кривые описываются точно
        approx = cv2.approxPolyDP(c, SEG_EPSILON, closed=False)
        pts = approx[:, 0]  # shape (N, 2)
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            dx = abs(x2 - x1)
            # пропускаем почти-вертикальные отрезки
            if dx > 0 and math.degrees(math.atan(abs(y2 - y1) / dx)) < 72:
                segs.append(((int(x1), int(y1)), (int(x2), int(y2))))
    return clean, segs


def start_pos(mask):
    cx = W // 2
    for y in range(H):
        if mask[y, cx] > 128:
            return cx, max(RADIUS + 4, y - 50)
    ys, xs = np.where(mask > 128)
    if len(ys):
        i = np.argmin(ys)
        return int(xs[i]), max(RADIUS + 4, int(ys[i]) - 50)
    return W // 2, RADIUS + 10


# ── Демо-кадр (нет камеры) ────────────────────────────────
def demo_frame():
    img = np.full((H, W, 3), (20, 20, 35), dtype=np.uint8)
    for p1, p2 in [
        ((W // 5, H // 5), (2 * W // 5, H // 4)),
        ((2 * W // 5 + 20, H // 3), (3 * W // 5, H // 3 - 30)),
        ((W // 8, H // 2), (W // 2, H // 2 + 20)),
        ((W // 2 + 20, 2 * H // 3), (7 * W // 8, 2 * H // 3 - 40)),
        ((W // 6, 3 * H // 4), (W // 2 - 20, 3 * H // 4 + 10)),
    ]:
        cv2.line(img, p1, p2, (180, 180, 180), 12)
    return img


# ── Главный цикл ───────────────────────────────────────────
def main():
    cap = cv2.VideoCapture(1)
    if cap.isOpened():
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, W)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, H)
    else:
        cap = None

    pygame.init()
    screen = pygame.display.set_mode((W, H))
    pygame.display.set_caption("Шарик по дороге")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("monospace", 14, bold=True)
    font_b = pygame.font.SysFont("monospace", 30, bold=True)

    frame = demo_frame() if cap is None else None
    road_mask, segments = np.zeros((H, W), dtype=np.uint8), []
    trail = []
    state = "WAITING"  # WAITING | FALLING | LOST
    paused = False
    debug = False
    fnum = 0
    lost_at = 0
    sx, sy = W // 2, RADIUS + 10

    def rebuild(frm):
        nonlocal road_mask, segments, sx, sy
        road_mask, segments = detect_segments(frm)
        sx, sy = start_pos(road_mask)
        set_road(segments)

    def reset(drop=False):
        nonlocal state, trail
        rebuild(frame)
        spawn_ball(sx, sy)
        trail = []
        state = "FALLING" if drop else "WAITING"

    ret, raw = cap.read() if cap else (False, None)
    frame = cv2.flip(cv2.resize(raw, (W, H)), 1) if ret else demo_frame()
    reset()

    while True:
        dt = min(clock.tick(FPS) / 1000, 0.05)
        fnum += 1

        for e in pygame.event.get():
            if e.type == pygame.QUIT or (
                e.type == pygame.KEYDOWN and e.key in (pygame.K_q, pygame.K_ESCAPE)
            ):
                if cap:
                    cap.release()
                pygame.quit()
                sys.exit()
            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_SPACE:
                    reset(drop=True)
                elif e.key == pygame.K_r:
                    reset(drop=False)
                elif e.key == pygame.K_p:
                    paused = not paused
                elif e.key == pygame.K_d:
                    debug = not debug

        # Кадр с камеры
        if cap:
            ret, raw = cap.read()
            if ret:
                frame = cv2.flip(cv2.resize(raw, (W, H)), 1)

        if fnum % DETECT_EVERY == 0:
            rebuild(frame)

        # Физика
        if not paused and state == "FALLING":
            for _ in range(STEPS):
                space.step(dt / STEPS)
            bx, by = ball_body.position
            trail.append((int(bx), int(by)))
            if len(trail) > TRAIL_MAX:
                trail.pop(0)
            if by > H * 1.1 or bx < -60 or bx > W + 60:
                state, lost_at = "LOST", time.time()
        elif state == "LOST" and time.time() - lost_at > 1.5:
            reset()

        # ── Рисуем ────────────────────────────────────────
        # Фон
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        pygame.surfarray.blit_array(screen, np.transpose(rgb, (1, 0, 2)))

        # Подсветка дороги
        overlay = pygame.Surface((W, H), pygame.SRCALPHA)
        ys, xs = np.where(road_mask > 128)
        if len(ys):
            for x, y in zip(xs[::4], ys[::4]):  # каждый 4-й пиксель — быстрее
                overlay.set_at((x, y), (50, 200, 80, 80))
        screen.blit(overlay, (0, 0))

        # Дебаг
        if debug:
            for (x1, y1), (x2, y2) in segments:
                pygame.draw.line(screen, (0, 230, 80), (x1, y1), (x2, y2), 3)

        # След
        for i in range(1, len(trail)):
            t = i / len(trail)
            pygame.draw.line(
                screen,
                (int(100 + 155 * t), int(50 + 150 * t), int(220 - 60 * t)),
                trail[i - 1],
                trail[i],
                max(1, int(t * 3)),
            )

        # Шарик
        if ball_body:
            bx, by = int(ball_body.position.x), int(ball_body.position.y)
            pygame.draw.circle(screen, (0, 0, 0, 70), (bx + 2, by + 4), RADIUS)  # тень
            pygame.draw.circle(screen, (30, 110, 255), (bx, by), RADIUS)
            ang = ball_body.angle
            pygame.draw.line(
                screen,
                (10, 50, 160),
                (bx, by),
                (
                    bx + int(math.cos(ang) * (RADIUS - 3)),
                    by + int(math.sin(ang) * (RADIUS - 3)),
                ),
                2,
            )
            pygame.draw.circle(screen, (10, 50, 160), (bx, by), RADIUS, 2)
            pygame.draw.circle(
                screen,
                (180, 220, 255),
                (bx - RADIUS // 3, by - RADIUS // 3),
                max(2, RADIUS // 4),
            )

        # Пульсирующий маркер старта
        if state == "WAITING":
            pulse = RADIUS + 8 + int(6 * math.sin(time.time() * 5))
            pygame.draw.circle(screen, (255, 210, 40), (sx, sy), RADIUS, 2)
            pygame.draw.circle(screen, (255, 210, 40), (sx, sy), pulse, 1)

        # HUD
        hud = [
            f"FPS {clock.get_fps():.0f}",
            "SPACE — запуск",
            "R — сброс",
            "P — пауза",
            "D — дебаг",
        ]
        for i, t in enumerate(hud):
            screen.blit(font.render(t, True, (255, 255, 255)), (10, 10 + i * 20))

        if state == "WAITING":
            screen.blit(
                font_b.render("Нажмите SPACE", True, (255, 210, 40)),
                (W // 2 - 130, H - 55),
            )
        if state == "LOST":
            screen.blit(
                font_b.render("Возврат...", True, (255, 60, 60)), (W // 2 - 100, H // 2)
            )
        if paused:
            screen.blit(
                font_b.render("ПАУЗА", True, (0, 230, 230)), (W // 2 - 60, H // 2)
            )

        pygame.display.flip()


if __name__ == "__main__":
    main()
