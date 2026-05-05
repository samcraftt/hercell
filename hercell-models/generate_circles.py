import math
import random
from PIL import Image, ImageDraw


BLUE = (30, 144, 255)
OTHER_COLORS = [
    (220, 20, 60),   # crimson
    (60, 179, 113),  # medium sea green
    (255, 165, 0),   # orange
    (148, 0, 211),   # dark violet
]

IMG_SIZE = 128
RADIUS = 10
TOTAL_CIRCLES_MIN = 6
TOTAL_CIRCLES_MAX = 14
LAYOUT_RETRIES = 40


def sample_non_overlapping_centers(n, radius, width, height, max_attempts=20000):
    centers = []
    min_dist = 2 * radius
    for _ in range(n):
        placed = False
        for _ in range(max_attempts):
            x = random.uniform(radius, width - radius)
            y = random.uniform(radius, height - radius)
            if all(math.hypot(x - cx, y - cy) >= min_dist for cx, cy in centers):
                centers.append((x, y))
                placed = True
                break
        if not placed:
            raise ValueError("Could not place circles without overlap.")
    return centers


def generate_circle_sample():
    last_error = None
    for _ in range(LAYOUT_RETRIES):
        total_circles = random.randint(TOTAL_CIRCLES_MIN, TOTAL_CIRCLES_MAX)
        blue_count = random.randint(0, total_circles)
        try:
            centers = sample_non_overlapping_centers(total_circles, RADIUS, IMG_SIZE, IMG_SIZE)
            break
        except ValueError as exc:
            last_error = exc
    else:
        raise ValueError(
            f"Failed to generate a valid non-overlapping circle layout after {LAYOUT_RETRIES} retries."
        ) from last_error

    is_blue = [True] * blue_count + [False] * (total_circles - blue_count)
    random.shuffle(is_blue)

    image = Image.new("RGB", (IMG_SIZE, IMG_SIZE), "white")
    draw = ImageDraw.Draw(image)
    for (x, y), blue in zip(centers, is_blue):
        color = BLUE if blue else random.choice(OTHER_COLORS)
        draw.ellipse(
            (x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS),
            fill=color,
            outline=(40, 40, 40),
            width=1,
        )

    return image, blue_count
