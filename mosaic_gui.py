import json
import os
import math
import random
import numpy as np
import cv2
import pathlib
import tkinter as tk
from tkinter import filedialog

# Define the default values for the inputs
original_img = ""
imgs_path = ""
output_path = ""
output_size = 5000
tile_width = 60
tile_height = 60

def get_average_color(img):
    average_color = np.average(np.average(img, axis=0), axis=0)
    average_color = np.around(average_color, decimals=-1)
    average_color = tuple(int(i) for i in average_color)
    return average_color

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

def generate_image():
    global original_img, imgs_path, output_path, output_size, tile_width, tile_height

    # Get the input and output paths and directories
    original_img = input_path_var.get()
    imgs_path = input_dir_var.get()
    output_path = output_path_var.get()
    output_size = int(output_size_var.get())
    tile_width = int(tile_width_var.get())
    tile_height = int(tile_height_var.get())

    # Generate the image
    imgs_dir = pathlib.Path(imgs_path)
    images = [f"{imgs_dir}/{i}" for i in os.listdir(imgs_dir) if "png" in i or "jpg" in i or "jpeg" in i]

    data = {}
    for img_path in images:
        img = cv2.imread(img_path)
        average_color = get_average_color(img)
        if str(tuple(average_color)) in data:
            data[str(tuple(average_color))].append(str(img_path))
        else:
            data[str(tuple(average_color))] = [str(img_path)]
    with open("./cache.json", "w") as file:
        json.dump(data, file, indent=2, sort_keys=True)
    print("Caching done")

    with open("./cache.json", "r") as file:
        data = json.load(file)

    img = cv2.imread(original_img)
    img = cv2.resize(img, (output_size, output_size))
    img_height, img_width, _ = img.shape
    num_tiles_h, num_tiles_w = img_height // tile_height, img_width // tile_width
    img = img[:tile_height * num_tiles_h, :tile_width * num_tiles_w]

    tiles = []
    for y in range(0, img_height, tile_height):
        for x in range(0, img_width, tile_width):
            tiles.append((y, y + tile_height, x, x + tile_width))

    for tile in tiles:
        y0, y1, x0, x1 = tile
        try:
            average_color = get_average_color(img[y0:y1, x0:x1])
        except Exception:
            continue
        closest_color = get_closest_color(average_color, data.keys())

        i_path = random.choice(data[str(closest_color)])

        i_path = pathlib.Path(i_path)
        tile_img = cv2.imread(str(i_path))
        tile_img = cv2.resize(tile_img, (tile_width, tile_height))
        img[y0:y1, x0:x1] = tile_img

    cv2.imwrite(output_path, img)

    print("Image generated successfully")


root = tk.Tk()
root.title("Photomosaic Generator")
root.geometry("500x500")


input_path_label = tk.Label(root, text="Original Image Path")
input_path_var = tk.StringVar(value=original_img)
input_path_entry = tk.Entry(root, textvariable=input_path_var, width=50)
input_path_label.pack()
input_path_entry.pack()

input_dir_label = tk.Label(root, text="Directory with Tile Images")
input_dir_var = tk.StringVar(value=imgs_path)
input_dir_entry = tk.Entry(root, textvariable=input_dir_var, width=50)
input_dir_label.pack()
input_dir_entry.pack()

output_path_label = tk.Label(root, text="Output Image Path")
output_path_var = tk.StringVar(value=output_path)
output_path_entry = tk.Entry(root, textvariable=output_path_var, width=50)
output_path_label.pack()
output_path_entry.pack()


tile_width_label = tk.Label(root, text="Tile Width")
tile_width_var = tk.StringVar(value=str(tile_width))
tile_width_entry = tk.Entry(root, textvariable=tile_width_var, width=10)
tile_width_label.pack()
tile_width_entry.pack()

tile_height_label = tk.Label(root, text="Tile Height")
tile_height_var = tk.StringVar(value=str(tile_height))
tile_height_entry = tk.Entry(root, textvariable=tile_height_var, width=10)
tile_height_label.pack()
tile_height_entry.pack()

output_size_label = tk.Label(root, text="Output Width")
output_size_var = tk.StringVar(value=str(output_size))
output_size_entry = tk.Entry(root, textvariable=output_size_var, width=10)
output_size_label.pack()
output_size_entry.pack()

generate_button = tk.Button(root, text="Generate", command=generate_image, width=20, height=2)
generate_button.pack()


def select_input_path():
    path = filedialog.askopenfilename()
    input_path_var.set(path)

def select_input_dir():
    path = filedialog.askdirectory()
    input_dir_var.set(path)

def select_output_path():
    path = filedialog.asksaveasfilename(defaultextension=".jpg")
    output_path_var.set(path)

    select_input_path_button = tk.Button(root, text="Select Original Image", command=select_input_path, width=20)
    select_input_path_button.pack()

    select_input_dir_button = tk.Button(root, text="Select Tile Images Directory", command=select_input_dir, width=30)
    select_input_dir_button.pack()

    select_output_path_button = tk.Button(root, text="Select Output Path", command=select_output_path, width=20)
    select_output_path_button.pack()

root.mainloop()