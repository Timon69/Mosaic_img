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


original_img = ""
imgs_path = ""
output_path = ""
output_img_size = (10000, 10000)
fragment_size = [100, 100]
cache = False
cache_path = f'/home/timon/PycharmProjects/My_moduls/Mosaic_img/caches/{imgs_path.split("/")[-1]}_cache.json'


def get_average_color(img):
    return tuple(np.mean(img, axis=(0, 1)).astype(int))


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

    img = cv2.imread(original_img)
    img = cv2.resize(img, output_img_size)
    img_height, img_width, _ = img.shape
    tile_height, tile_width = fragment_size
    num_tiles_h, num_tiles_w = img_height // tile_height, img_width // tile_width
    img = img[:tile_height * num_tiles_h, :tile_width * num_tiles_w]

    tiles = []
    for y in range(0, img_height, tile_height):
        for x in range(0, img_width, tile_width):
            tiles.append((y, y + tile_height, x, x + tile_width))

    with multiprocessing.Pool() as pool:
        results = list(tqdm(pool.imap_unordered(process_tile, tiles), total=len(tiles), desc="Сalculations"))

    for result in tqdm(results, desc="Building photo"):
        if result is not None:
            y0, y1, x0, x1, i = result
            img[y0:y1, x0:x1] = i

    start = time.time()
    cv2.imwrite(output_path, img)
    print(f"Saving took {time.time()-start} seconds")
