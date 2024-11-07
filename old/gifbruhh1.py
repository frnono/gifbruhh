from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import os
import sys

class GifEditor:
    MAX_WIDTH = 800
    MAX_HEIGHT = 600
    CONFIG_FILE = os.path.join(os.getenv('APPDATA'), 'gifbruhh', 'config.txt')

    def __init__(self, root):
        self.root = root
        root.configure(bg='#2B2A33')

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)

        self.canvas = tk.Canvas(root, cursor="sb_v_double_arrow", background='#2B2A33', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_filename = ""
        self.png_filename = ""
        self.frames = []
        self.mask_img_original = None
        self.mask_img_resized = None
        self.current_frame = 0
        self.stretch_offset = 0
        self.flip_mode = tk.BooleanVar(value=False)
        self.add_mode = tk.BooleanVar(value=False)

        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.style.configure('TButton', background='#3C3B41', foreground='white')
        self.style.map('TButton', background=[('active', '#2F2E36')])
        self.style.configure('TCheckbutton', background='#2B2A33', foreground='white')
        self.style.configure('TFrame', background='#2B2A33')

        self.buttons_frame = ttk.Frame(root, style='TFrame')
        self.buttons_frame.pack(side=tk.BOTTOM, pady=10)

        self.load_image_button = ttk.Button(self.buttons_frame, text="Load Image", command=self.load_image, takefocus=0)
        self.load_image_button.pack(side=tk.LEFT, padx=5)

        self.load_png_button = ttk.Button(self.buttons_frame, text="Load PNG", command=self.load_png, takefocus=0)
        self.load_png_button.pack(side=tk.LEFT, padx=5)

        self.cutout_button = ttk.Button(self.buttons_frame, text="Apply", command=self.apply_action, state=tk.DISABLED, takefocus=0)
        self.cutout_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(self.buttons_frame, text="Save GIF", command=self.save_gif, state=tk.DISABLED, takefocus=0)
        self.save_button.pack(side=tk.LEFT, padx=5)

        self.action_checkbox = ttk.Checkbutton(self.buttons_frame, text="Add PNG", variable=self.add_mode, takefocus=0)
        self.action_checkbox.pack(side=tk.LEFT, padx=5)

        self.flip_checkbox = ttk.Checkbutton(self.buttons_frame, text="Flip PNG", variable=self.flip_mode, command=self.display_frame, takefocus=0)
        self.flip_checkbox.pack(side=tk.LEFT, padx=5)

        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        self.load_last_png()

    def load_last_png(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                self.png_filename = f.read().strip()
            if os.path.exists(self.png_filename):
                self.mask_img_original = Image.open(self.png_filename).convert("RGBA")
                self.reset_mask()
                self.display_frame()
                self.update_cutout_button()

    def load_image(self):
        self.image_filename = filedialog.askopenfilename(filetypes=[("Image Files", "*.gif *.png *.jpg *.jpeg")])
        if not self.image_filename:
            return
        im = Image.open(self.image_filename)
        if im.format != 'GIF':
            im = im.convert("RGBA")
            self.frames = [im]
        else:
            self.frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(im)]
        self.current_frame = 0
        self.display_frame()
        self.update_cutout_button()

    def load_png(self):
        self.png_filename = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
        if not self.png_filename:
            return
        with open(self.CONFIG_FILE, "w") as f:
            f.write(self.png_filename)
        self.mask_img_original = Image.open(self.png_filename).convert("RGBA")
        self.reset_mask()
        self.display_frame()
        self.update_cutout_button()

    def reset_mask(self):
        if self.mask_img_original:
            self.mask_img_resized = self.mask_img_original.copy()

    def display_frame(self):
        if not self.frames:
            return
        frame = self.frames[self.current_frame]

        gif_width = frame.width
        if self.mask_img_original:
            aspect_ratio = self.mask_img_original.height / self.mask_img_original.width
            new_height = int(gif_width * aspect_ratio) + self.stretch_offset
            self.mask_img_resized = self.mask_img_original.resize((gif_width, max(new_height, 1)), Image.LANCZOS)

            mask_to_use = self.mask_img_resized
            if self.flip_mode.get():
                mask_to_use = mask_to_use.transpose(Image.FLIP_LEFT_RIGHT)

            display_frame = frame.copy()
            display_frame.paste(mask_to_use, (0, 0), mask_to_use)
        else:
            display_frame = frame

        display_frame = self.resize_to_fit(display_frame)

        self.tk_img = ImageTk.PhotoImage(display_frame)
        self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_img)
        self.canvas.config(width=display_frame.width, height=display_frame.height)

    def add_png(self):
        if not self.mask_img_resized:
            return

        for i in range(len(self.frames)):
            frame = self.frames[i]
            gif_width = frame.width
            aspect_ratio = self.mask_img_resized.height / self.mask_img_resized.width
            new_height = int(gif_width * aspect_ratio)

            stretched_mask = self.mask_img_resized.resize((gif_width, max(new_height, 1)), Image.LANCZOS)
            if self.flip_mode.get():
                stretched_mask = stretched_mask.transpose(Image.FLIP_LEFT_RIGHT)

            frame.paste(stretched_mask, (0, 0), stretched_mask)
            self.frames[i] = frame

        self.display_frame()
        self.save_button.config(state=tk.NORMAL)

    def cutout_shape(self):
        if not self.mask_img_resized:
            return

        for i in range(len(self.frames)):
            frame = self.frames[i]
            gif_width = frame.width
            aspect_ratio = self.mask_img_resized.height / self.mask_img_resized.width
            new_height = int(gif_width * aspect_ratio)

            stretched_mask = self.mask_img_resized.resize((gif_width, max(new_height, 1)), Image.LANCZOS)
            if self.flip_mode.get():
                stretched_mask = stretched_mask.transpose(Image.FLIP_LEFT_RIGHT)

            alpha_mask = stretched_mask.split()[-1]
            frame.paste((0, 0, 0, 0), (0, 0), alpha_mask)
            self.frames[i] = frame

        self.display_frame()
        self.save_button.config(state=tk.NORMAL)

    def on_button_press(self, event):
        self.start_y = event.y_root

    def on_mouse_drag(self, event):
        if self.mask_img_original and self.mask_img_resized:
            delta_y = event.y_root - self.start_y
            self.stretch_offset += delta_y
            self.start_y = event.y_root

            new_height = max(int(self.mask_img_original.height + self.stretch_offset), 1)
            self.mask_img_resized = self.mask_img_original.resize((self.mask_img_original.width, new_height), Image.LANCZOS)
            self.display_frame()

    def resize_to_fit(self, image):
        width, height = image.size
        if width > self.MAX_WIDTH or height > self.MAX_HEIGHT:
            scaling_factor = min(self.MAX_WIDTH / width, self.MAX_HEIGHT / height)
            new_size = (int(width * scaling_factor), int(height * scaling_factor))
            return image.resize(new_size, Image.LANCZOS)
        return image

    def apply_action(self):
        if not self.mask_img_original:
            return

        if self.add_mode.get():
            self.add_png()
        else:
            self.cutout_shape()
    
    def update_cutout_button(self):
        if self.frames and self.mask_img_original:
            self.cutout_button.config(state=tk.NORMAL)

    def save_gif(self):
        if not self.frames:
            return
        output_filename = filedialog.asksaveasfilename(defaultextension=".gif", filetypes=[("GIF Files", "*.gif")])
        if not output_filename:
            return
        self.frames[0].save(output_filename, save_all=True, append_images=self.frames[1:], loop=0, disposal=2)
        messagebox.showinfo("Success", "GIF saved successfully :3")

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

if __name__ == "__main__":
    root = tk.Tk()
    root.title("gifbruhh")
    
    icon_path = resource_path("asriel.ico")

    if os.path.exists(icon_path):
        root.iconbitmap(icon_path)
    else:
        print("Icon file not found, using default window icon.")

    GifEditor(root)
    root.mainloop()