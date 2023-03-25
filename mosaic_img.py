import json
import math
import random
import cv2
import time
from tqdm import tqdm
import numpy as np
import multiprocessing
import pathlib
import os
from functools import wraps


def memoize(func):
    cache = {}

    @wraps(func)
    def wrapper(*args, **kwargs):
        key = str(args) + str(kwargs)

        if key not in cache:
            cache[key] = func(*args, **kwargs)

        return cache[key]
    return wrapper


safe_save = False
# path to main img
original_img = ""
# path to dir with fragments
imgs_path = ""
# path for output img
output_path = "./results" if safe_save else "./result.jpg"
# [width, height]
output_img_size = (10000, 10000)
fragment_size = [100, 100]
# make cache or not. set False if you already have cache else True
cache = False
# path to dir for file with cache
cache_path = f'./caches/{imgs_path.split("/")[-1]}_cache.json'
# overlaying the final result on the initial img
merge = True
# transparency of main img
alpha = 0.6
# transparency of fragments img
betta = 0.3
# runs faster but uses a lot of RAM
use_ram = False


if use_ram:
    @memoize
    def get_average_color(img):
        return tuple(np.mean(img, axis=(0, 1)).astype(int))
else:
    def get_average_color(img):
        return tuple(np.mean(img, axis=(0, 1)).astype(int))


if use_ram:
    @memoize
    def get_closest_color(color, colors):
        cr, cg, cb = color

        min_difference = float("inf")
        closest_color = None
        for c in colors:
            r, g, b = eval(c)
            difference = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
            if difference < min_difference:
                min_difference = difference
                closest_color = eval(c)

        return closest_color
else:
    def get_closest_color(color, colors):
        cr, cg, cb = color

        min_difference = float("inf")
        closest_color = None
        for c in colors:
            r, g, b = eval(c)
            difference = math.sqrt((r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2)
            if difference < min_difference:
                min_difference = difference
                closest_color = eval(c)

        return closest_color


if use_ram:
    @memoize
    def process_tile(tile):
        y0, y1, x0, x1 = tile
        try:
            average_color = get_average_color(img[y0:y1, x0:x1])
        except Exception:
            return None
        closest_color = get_closest_color(average_color, data.keys())

        i_path = random.choice(data[str(closest_color)])
        i = cv2.imread(i_path)
        i = cv2.resize(i, (tile_width, tile_height))
        return (y0, y1, x0, x1, i)
else:
    def process_tile(tile):
        y0, y1, x0, x1 = tile
        try:
            average_color = get_average_color(img[y0:y1, x0:x1])
        except Exception:
            return None
        closest_color = get_closest_color(average_color, data.keys())

        i_path = random.choice(data[str(closest_color)])
        i = cv2.imread(i_path)
        i = cv2.resize(i, (tile_width, tile_height))
        return (y0, y1, x0, x1, i)


if use_ram:
    @memoize
    def make_cache(img_path):
        img = cv2.imread(img_path)
        average_color = get_average_color(img)
        if str(tuple(average_color)) in data:
            data[str(tuple(average_color))].append(str(img_path))
        else:
            data[str(tuple(average_color))] = [str(img_path)]
            with open(cache_path, "w") as file:
                json.dump(data, file, indent=2, sort_keys=True)
else:
    def make_cache(img_path):
        img = cv2.imread(img_path)
        average_color = get_average_color(img)
        if str(tuple(average_color)) in data:
            data[str(tuple(average_color))].append(str(img_path))
        else:
            data[str(tuple(average_color))] = [str(img_path)]
            with open(cache_path, "w") as file:
                json.dump(data, file, indent=2, sort_keys=True)


if __name__ == '__main__':
    data = {}
    
    if cache:
        imgs_dir = pathlib.Path(imgs_path)
        images = [f"{imgs_dir}/{i}" for i in os.listdir(imgs_dir) if "png" in i or "jpg" in i or "jpeg" in i]

        with multiprocessing.Pool() as pool:
            a = list(tqdm(pool.imap_unordered(make_cache, images), total=len(images), desc="Caching"))

    with open(cache_path, "r") as file:
        data = json.load(file)

    start = time.time()
    img = cv2.imread(original_img)
    img = cv2.resize(img, output_img_size)
    if merge:
        cv2.imwrite("./orig.png", img)
    img_height, img_width, _ = img.shape
    tile_width, tile_height = fragment_size
    num_tiles_h, num_tiles_w = img_height // tile_height, img_width // tile_width
    img = img[:tile_height * num_tiles_h, :tile_width * num_tiles_w]

    tiles = []
    for y in range(0, img_height, tile_height):
        for x in range(0, img_width, tile_width):
            tiles.append((y, y + tile_height, x, x + tile_width))
    print(f"Preparations took {time.time() - start} seconds")

    with multiprocessing.Pool() as pool:
        results = list(tqdm(pool.imap_unordered(process_tile, tiles), total=len(tiles), desc="Сalculations"))

    for result in tqdm(results, desc="Building photo"):
        if result is not None:
            y0, y1, x0, x1, i = result
            img[y0:y1, x0:x1] = i

    if safe_save and not merge:
        start = time.time()
        for i in range(10000):
            path = f"{output_path}/{i}.jpg"
            if not os.path.exists(path):
                cv2.imwrite(path, img)
                break
        print(f"Saving took {time.time()-start} seconds")
    elif not safe_save and not merge:
        start = time.time()
        cv2.imwrite(output_path, img)
        print(f"Saving took {time.time()-start} seconds")

    if merge:
        start = time.time()
        orig = cv2.imread("./orig.png")
        changed = img

        # Apply alpha blending
        result = cv2.addWeighted(orig, 1 - alpha, changed, 1 - betta, 0)
        if safe_save:
            for i in range(10000):
                path = f"{output_path}/{i}.jpg"
                if not os.path.exists(path):
                    cv2.imwrite(path, result)
                    break
        else:
            cv2.imwrite(output_path, result)
        os.remove("./orig.png")
        print(f"Merging took {time.time() - start} seconds")
