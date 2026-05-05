import math
import random
from PIL import Image, ImageDraw

from generate_circles import (
    BLUE,
    OTHER_COLORS,
    IMG_SIZE,
    RADIUS,
    TOTAL_CIRCLES_MIN,
    TOTAL_CIRCLES_MAX,
    sample_non_overlapping_centers,
    LAYOUT_RETRIES,
)


BROWN = (139, 69, 19)
MAX_SPECS_PER_BLUE = 5


def draw_brown_specs(draw, blue_centers, total_specs):
    if total_specs == 0 or not blue_centers:
        return 0

    active_count = random.randint(1, len(blue_centers))
    active_centers = random.sample(blue_centers, active_count)
    for _ in range(total_specs):
        cx, cy = random.choice(active_centers)
        sr = random.randint(1, 3)
        max_dist = max(0.0, RADIUS - sr - 2.0)
        dist = math.sqrt(random.random()) * max_dist
        theta = random.uniform(0.0, 2.0 * math.pi)
        sx = cx + dist * math.cos(theta)
        sy = cy + dist * math.sin(theta)
        draw.ellipse((sx - sr, sy - sr, sx + sr, sy + sr), fill=BROWN)
    return total_specs


def sample_specs_for_class(spec_class, max_specs):
    if max_specs <= 0 or spec_class == 0:
        return 0

    if spec_class == 1:
        lo = max(1, int(0.26 * max_specs))
        hi = max(lo, int(0.50 * max_specs))
    elif spec_class == 2:
        lo = max(1, int(0.51 * max_specs))
        hi = max(lo, int(0.75 * max_specs))
    else:
        lo = max(1, int(0.76 * max_specs))
        hi = max(lo, max_specs)
    return random.randint(lo, hi)


def generate_speck_sample():
    last_error = None
    for _ in range(LAYOUT_RETRIES):
        total_circles = random.randint(TOTAL_CIRCLES_MIN, TOTAL_CIRCLES_MAX)
        blue_count = random.randint(0, total_circles)
        speck_class = random.randint(0, 3)
        try:
            centers = sample_non_overlapping_centers(total_circles, RADIUS, IMG_SIZE, IMG_SIZE)
            break
        except ValueError as exc:
            last_error = exc
    else:
        raise ValueError(
            f"Failed to generate a valid non-overlapping speck layout after {LAYOUT_RETRIES} retries."
        ) from last_error
    is_blue = [True] * blue_count + [False] * (total_circles - blue_count)
    random.shuffle(is_blue)

    image = Image.new("RGB", (IMG_SIZE, IMG_SIZE), "white")
    draw = ImageDraw.Draw(image)
    blue_centers = []

    for (x, y), blue in zip(centers, is_blue):
        color = BLUE if blue else random.choice(OTHER_COLORS)
        draw.ellipse(
            (x - RADIUS, y - RADIUS, x + RADIUS, y + RADIUS),
            fill=color,
            outline=(40, 40, 40),
            width=1,
        )
        if blue:
            blue_centers.append((x, y))

    max_specs = blue_count * MAX_SPECS_PER_BLUE
    total_specs = sample_specs_for_class(speck_class, max_specs)
    if max_specs <= 0:
        speck_class = 0
    drawn_specs = draw_brown_specs(draw, blue_centers, total_specs)

    return image, blue_count, speck_class, drawn_specs
