import torch
from tqdm import tqdm
from torch import nn
from torch import optim
from torch.utils import data
from collections import deque
from torch.utils.tensorboard import SummaryWriter
from datetime import datetime

def train(model, train_dataset, test_dataset, epochs):
    timestamp = datetime.today().strftime("%Y%m%d_%H%M%S")
    train_writer = SummaryWriter(f"runs/{timestamp}/train")
    test_writer = SummaryWriter(f"runs/{timestamp}/test")
    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters())
    dl_train = data.DataLoader(train_dataset, batch_size=8, shuffle=True, num_workers=2)
    dl_test = data.DataLoader(test_dataset, batch_size=8, shuffle=True, num_workers=2)
    
    accuracy_deque = deque(maxlen=len(dl_train))
    
    for epoch in range(epochs):
        pbar = tqdm(range(len(dl_train)), desc=f"Epoch {epoch+1}/{epochs}", position=0, leave=True, ncols=100)

        model.train(True)
        for i, (x, y) in enumerate(dl_train):
            optimizer.zero_grad()
            pred = model(x)
            loss = criterion(pred, y)
            loss.backward()
            optimizer.step()
            accuracy = (y == pred.max(1)[1]).float().mean().item()
            accuracy_deque.append(accuracy)
            train_writer.add_scalar("Accuracy", sum(accuracy_deque) / len(accuracy_deque), epoch * len(dl_train) + i)
            pbar.set_postfix({"accuracy": f"{sum(accuracy_deque) / len(accuracy_deque) * 100:.2f}%"})
            pbar.update()

        running_accuracy = 0.0
        model.eval()
        pbar = tqdm(range(len(dl_test)), desc="Test", position=0, leave=True, ncols=100)
        with torch.no_grad():
            for i, (x, y) in enumerate(dl_test):
                pred = model(x)
                accuracy = (y == pred.max(1)[1]).float().mean()
                running_accuracy += accuracy.item()
                pbar.set_postfix({"accuracy": f"{running_accuracy / (i + 1) * 100:.2f}%"})
                pbar.update()
            test_writer.add_scalar("Accuracy", running_accuracy / len(dl_test), (epoch + 1) * len(dl_train))

# ===================================================================
from matplotlib import pyplot as plt
import seaborn as sns
from PIL import Image
import numpy as np

def mnist_visualize(path_to_image, model, transform):
    fig, ax = plt.subplots(1, 3, figsize=(14, 10), width_ratios=(5, 1, 1))

    image = Image.open(path_to_image)
    
    sns.heatmap(
        np.asarray(image), 
        cbar=False, linewidth=.5, cmap="gray",
        xticklabels=False, yticklabels=False,
        ax=ax[0]
    ).title.set_text("Input layer")
    
    x = transform(image)
    x = model[0](x)
    x = model[1](x)
    
    sns.heatmap(
        np.rot90(x.detach().numpy(), k=3), 
        cbar=False, linewidth=.5, cmap="coolwarm", center=0.0,
        annot=True, fmt=".1f", square=True, 
        xticklabels=False, yticklabels=False,
        ax=ax[1]
    ).title.set_text("Hidden layer")
    
    x = model[2](x)
    x = model[3](x)
    x = model[4](x)
    
    sns.heatmap(
        np.rot90(x.detach().numpy(), k=3), 
        cbar=False, linewidth=.5, cmap="coolwarm", center=0.0,
        annot=True, fmt=".1f", square=True, 
        xticklabels=False,
        ax=ax[2]
    ).title.set_text("Output layer")
    
    plt.show()

# ===================================================================
from matplotlib import pyplot as plt
import seaborn as sns
from PIL import Image
import numpy as np
import torch

def visualize(path_to_image, model, transform, classes):
    fig, ax = plt.subplots(1, 2, figsize=(10, 3.5), width_ratios=(10, 2))

    image = Image.open(path_to_image)
    ax[0].imshow(image)
    
    pred = model(torch.unsqueeze(transform(image), 0))
    
    sns.heatmap(
        np.rot90(pred.detach().numpy(), k=3), 
        cbar=False, linewidth=.5, cmap="coolwarm", center=0.0,
        annot=True, fmt=".1f", square=True, 
        xticklabels=False, yticklabels=classes,
        ax=ax[1]
    )
    
    plt.show()

# ===================================================================
from concurrent.futures import ThreadPoolExecutor
from tqdm import tqdm
import urllib.request
import pathlib
import math
import json
import re
import os

class DatasetDownloader:
    def __init__(self, ds_path, threads=5):
        self.pbar = None
        self.image_num = 0
        self.path = ds_path
        self.threads = threads
        self.url_queue = []

    def gen_image_num(self, n=1):
        start = self.image_num
        self.image_num += n
        return range(start, self.image_num)
    
    def dl_jobs(self, queries, hundreds=1, test_split=0.2):
        self.pbar = tqdm(range(len(queries) * hundreds), desc="Retrieving URLs", position=0, leave=True, ncols=100)
        for query in queries:
            vqd = self.get_vqd(query)
            for hundred in range(hundreds):
                data = {"q": query, "vqd": vqd, "s": hundreds * 100}
                data = urllib.parse.urlencode(data).encode('utf-8')
                response = urllib.request.urlopen("https://duckduckgo.com/i.js", data=data)
                response = json.loads(response.read().decode("utf-8"))
                image_urls = list(map((lambda d: d["thumbnail"]), response["results"]))
                self.url_queue += list(zip(map(os.path.join, 
                        [self.path] * len(image_urls), 
                        ["test"] * math.ceil(test_split * len(image_urls)) + ["train"] * math.floor((1 - test_split) * len(image_urls)), 
                        [query] * len(image_urls), 
                        map(lambda i: f"{i:06d}.jpg", self.gen_image_num(len(image_urls))),
                    ), 
                    image_urls, 
                ))
                self.pbar.update()
                
        self.pbar = tqdm(range(len(self.url_queue)), desc="Downloading images", position=0, leave=True, ncols=100)
        pool = ThreadPoolExecutor()
        for thread_num in range(1, self.threads + 1):
            pool.submit(self.dl_thread, thread_num)
        pool.shutdown(wait=True)
        
    @classmethod
    def get_vqd(cls, query):
        data = urllib.parse.urlencode({"q": query}).encode('utf-8')
        response = urllib.request.urlopen("https://duckduckgo.com/", data=data)
        response = response.read().decode("utf-8")
        vqd = re.search(r"vqd=([\d-]+)\&", response).group(1)
        return vqd

    def dl_thread(self, thread_num):
        while self.url_queue:
            path, url = self.url_queue.pop()
            pathlib.Path(os.path.split(path)[0]).mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(url, path)
            self.pbar.update()

# ===================================================================
from tkinter import filedialog, Tk
import os

def open_file(initialdir=os.getcwd()):
    root = Tk()
    root.call('wm', 'attributes', '.', '-topmost', '1')
    root.withdraw()
    filenames = filedialog.askopenfilename(initialdir=initialdir)
    return filenames

def save_file(initialdir=os.getcwd()):
    root = Tk()
    root.call('wm', 'attributes', '.', '-topmost', '1')
    root.withdraw()
    filenames = filedialog.asksaveasfilename(initialdir=initialdir)
    return filenames

# ===================================================================
import tkinter as tk
import math
import random
from PIL import Image, ImageDraw

class MnistApp:
    def __init__(self, model, transform):
        self.root = tk.Tk()
        self.root.geometry("500x350")
        self.root.resizable(0, 0)

        self.model, self.transform = model, transform
        self.mouse_pressed = False
        self.image = Image.new("L", (280, 280), 0)
        self.imdraw = ImageDraw.Draw(self.image)
        
        self.canvas = tk.Canvas(self.root, height=280, width=280, bg="black")
        self.canvas.place(relx=0.3, rely=0.43, anchor=tk.CENTER)
        self.canvas.bind('<ButtonPress-1>', self.mouse_down)
        self.canvas.bind('<ButtonRelease-1>', self.mouse_up)
                    
        button = tk.Button(self.root, text="ERASE", command=self.erase)
        button.place(relx=0.3, rely=0.9, anchor=tk.CENTER)

        self.label = tk.Label(self.root, text="Start drawing \nfor predictions", font=("Arial", 18))
        self.label.place(relx=0.8, rely=0.5, anchor=tk.CENTER)

    @classmethod
    def random_point(cls, x, y, r):
        a = random_angle = 2 * math.pi * random.random()
        r = random_radius = r * random.random() ** 5
        random_x = r * math.cos(a) + x
        random_y = r * math.sin(a) + y
        return random_x, random_y

    def draw(self, event):
        if self.mouse_pressed:
            x = self.root.winfo_pointerx() - event.x_root + event.x
            y = self.root.winfo_pointery() - event.y_root + event.y
            
            rx, ry = self.random_point(x, y, 5)
            event.widget.create_line(rx, ry, rx+10, ry+10, width=10, fill='white')
            self.imdraw.line(((rx, ry), (rx+10, ry+10)), width=10, fill=255)
            self.predict()
            self.after_id = self.root.after(1, self.draw, event)

    def erase(self):
        self.canvas.delete("all")
        self.image = Image.new("L", (280, 280), 0)
        self.imdraw = ImageDraw.Draw(self.image)

    def mouse_down(self, event):
        self.mouse_pressed = True
        self.draw(event)

    def mouse_up(self, event):
        self.mouse_pressed = False

    def predict(self):
        pred = self.model(self.transform(self.image.resize((28, 28)))).detach().numpy()[0]
        show_str = ""
        for val, pred_val in enumerate(pred):
            show_str += f"{val}: {pred_val*100:.1f}% \n"
        self.label.config(text=show_str)