from PIL import Image, ImageTk, ImageSequence
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import sys
from moviepy.editor import VideoFileClip

class GifEditor:
    MAX_WIDTH = 1280
    MAX_HEIGHT = 720
    CONFIG_FILE = os.path.join(os.getenv('APPDATA'), 'gifbruhh', 'config.txt')

    def __init__(self, root):
        self.root = root
        root.configure(bg='#2B2A33')

        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(self.CONFIG_FILE), exist_ok=True)

        self.load_config()

        self.canvas = tk.Canvas(root, cursor="sb_v_double_arrow", background='#2B2A33', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.image_filename = ""
        self.png_filename = ""
        self.frames = []
        self.original_frames = []  # Keep original frames for reference
        self.mask_img_original = None
        self.mask_img_resized = None
        self.current_frame = 0
        self.stretch_offset = 0
        self.flip_mode = tk.BooleanVar(value=False)
        self.add_mode = tk.BooleanVar(value=False)

        # Attributes for maintaining dimensions
        self.original_image_size = None
        self.current_width = None
        self.current_height = None

        # Initialize aspect ratio lock
        self.aspect_ratio_locked = tk.BooleanVar(value=True)

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

        self.load_png_button = ttk.Button(self.buttons_frame, text="Load Mask", command=self.load_png, takefocus=0)
        self.load_png_button.pack(side=tk.LEFT, padx=5)

        self.cutout_button = ttk.Button(self.buttons_frame, text="Apply", command=self.apply_action, state=tk.DISABLED, takefocus=0)
        self.cutout_button.pack(side=tk.LEFT, padx=5)

        self.save_button = ttk.Button(self.buttons_frame, text="Save GIF", command=self.save_gif, state=tk.DISABLED, takefocus=0)
        self.save_button.pack(side=tk.LEFT, padx=5)

        # Menu-related components
        self.menu_button = ttk.Button(self.buttons_frame, text="Options", command=self.show_menu, takefocus=0)
        self.menu_button.pack(side=tk.LEFT, padx=5)

        # Create a Menu
        self.options_menu = tk.Menu(root, tearoff=0)
        self.options_menu.add_checkbutton(label="Add PNG", variable=self.add_mode, command=self.add_png_toggle)
        self.options_menu.add_checkbutton(label="Flip PNG", variable=self.flip_mode, command=self.display_frame)
        self.options_menu.add_checkbutton(label="Lock Aspect Ratio", variable=self.aspect_ratio_locked)

        # Entry fields for width and height
        self.width_value = tk.StringVar()
        self.height_value = tk.StringVar()
        self.width_label = ttk.Label(self.buttons_frame, text="Width:", background='#2B2A33', foreground='white')
        self.width_label.pack(side=tk.LEFT, padx=5)
        self.width_entry = ttk.Entry(self.buttons_frame, textvariable=self.width_value, width=5)
        self.width_entry.pack(side=tk.LEFT, padx=5)
        self.width_entry.bind("<Return>", self.update_dimensions)

        self.height_label = ttk.Label(self.buttons_frame, text="Height:", background='#2B2A33', foreground='white')
        self.height_label.pack(side=tk.LEFT, padx=5)
        self.height_entry = ttk.Entry(self.buttons_frame, textvariable=self.height_value, width=5)
        self.height_entry.pack(side=tk.LEFT, padx=5)
        self.height_entry.bind("<Return>", self.update_dimensions)

        # Bind for vertical scaling of PNG with left-click
        self.canvas.bind("<ButtonPress-1>", self.on_button_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)

        # Bind for scaling of PNG while maintaining aspect ratio with right-click
        self.canvas.bind("<ButtonPress-3>", self.on_button_press_right)
        self.canvas.bind("<B3-Motion>", self.on_mouse_drag_right)

        self.load_last_png()

    def load_config(self):
        """Load configuration from config file."""
        self.last_save_directory = os.path.expanduser("~")  # Default to home directory
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("SAVE_DIR="):
                        self.last_save_directory = line.strip().split("=")[1]
                    elif line.startswith("PNG_FILE="):
                        self.png_filename = line.strip().split("=")[1]

    def save_config(self):
        """Save configuration to config file."""
        with open(self.CONFIG_FILE, "w") as f:
            f.write(f"SAVE_DIR={self.last_save_directory}\n")
            if self.png_filename:
                f.write(f"PNG_FILE={self.png_filename}\n")

    def load_last_png(self):
        if os.path.exists(self.CONFIG_FILE):
            with open(self.CONFIG_FILE, "r") as f:
                self.png_filename = f.read().strip()
            if os.path.exists(self.png_filename):
                try:
                    self.mask_img_original = Image.open(self.png_filename).convert("RGBA")
                    self.reset_mask()
                    self.display_frame()
                    self.update_cutout_button()
                except Exception as e:
                    print(f"Failed to load the last PNG: {e}")

    def load_image(self):
        self.image_filename = filedialog.askopenfilename(
            filetypes=[("Image/Video Files", "*.gif *.png *.jpg *.jpeg *.mp4 *.mov *.m4v *.mkv")])
        if not self.image_filename:
            return

        # Set the window title with the image file name
        file_name = os.path.basename(self.image_filename)
        self.root.title(f"gifbruhh - {file_name}")

        file_ext = os.path.splitext(self.image_filename)[1].lower()

        if file_ext in ['.gif', '.png', '.jpg', '.jpeg']:
            im = Image.open(self.image_filename)
            if im.format != 'GIF':
                im = im.convert("RGBA")
                self.frames = [im]
                self.original_frames = [im.copy()]
            else:
                self.frames = [frame.copy().convert("RGBA") for frame in ImageSequence.Iterator(im)]
                self.original_frames = [frame.copy() for frame in self.frames]
        elif file_ext in ['.mp4', '.mov', '.m4v', '.mkv']:
            try:
                clip = VideoFileClip(self.image_filename)
                target_fps = 5
                fps_clip = clip.set_fps(target_fps)
                scale_factor = 0.5
                resized_clip = fps_clip.resize(scale_factor)
                self.frames = [Image.fromarray(frame.astype('uint8'), 'RGB').convert("RGBA") for frame in resized_clip.iter_frames(fps=target_fps)]
                self.original_frames = [frame.copy() for frame in self.frames]
                clip.close()
            except FileNotFoundError:
                messagebox.showerror("FFmpeg Missing", "FFmpeg is required to process video files. Please install FFmpeg and ensure it's in your PATH.")
                return
            except Exception as e:
                messagebox.showerror("Error", f"An error occurred while processing the video: {str(e)}")
                return

        self.current_frame = 0
        self.original_image_size = self.frames[0].size
        self.current_width, self.current_height = self.original_image_size
        self.width_value.set(str(self.current_width))
        self.height_value.set(str(self.current_height))

        # Resize the mask initially to match the frame
        if self.mask_img_original:
            self.mask_img_resized = self.mask_img_original.resize(self.frames[0].size, Image.LANCZOS)

        self.display_frame()
        self.update_cutout_button()
        self.save_button.config(state=tk.NORMAL)

    def load_png(self):
        self.png_filename = filedialog.askopenfilename(filetypes=[("PNG Files", "*.png")])
        if not self.png_filename:
            return
        
        # Write the PNG filename to config
        if not os.path.exists(os.path.dirname(self.CONFIG_FILE)):
            os.makedirs(os.path.dirname(self.CONFIG_FILE))
        with open(self.CONFIG_FILE, "w") as f:
            f.write(self.png_filename)
        
        self.mask_img_original = Image.open(self.png_filename).convert("RGBA")
        self.reset_mask()
        self.display_frame()
        self.update_cutout_button()

    def reset_mask(self):
        if self.mask_img_original and self.frames:
            self.mask_img_resized = self.mask_img_original.resize(self.frames[self.current_frame].size, Image.LANCZOS)

    def update_dimensions(self, event=None):
        try:
            new_width = int(self.width_entry.get())
            new_height = int(self.height_entry.get())

            self.frames = [
                orig_frame.resize((new_width, new_height), Image.LANCZOS) for orig_frame in self.original_frames
            ]
            self.current_width, self.current_height = new_width, new_height
            # Adjust mask size as needed
            self.reset_mask()
            self.display_frame()
        except ValueError:
            messagebox.showerror("Invalid Input", "Please enter valid numeric values for width and height.")

    def add_png_toggle(self):
        """Toggle adding PNG by calling add_png without state checking."""
        if self.add_mode.get():
            self.add_png()

    def show_menu(self):
        # Position the menu where the button is
        x = self.menu_button.winfo_rootx()
        y = self.menu_button.winfo_rooty() + self.menu_button.winfo_height()
        self.options_menu.post(x, y)

    def display_frame(self):
        if not self.frames:
            return

        frame = self.frames[self.current_frame]

        if self.mask_img_resized:
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
        self.start_y = event.y

    def on_mouse_drag(self, event):
        if self.mask_img_original and self.mask_img_resized:
            delta_y = event.y - self.start_y
            new_width = self.mask_img_resized.width
            new_height = max(self.mask_img_resized.height + delta_y, 1)

            self.mask_img_resized = self.mask_img_original.resize((new_width, new_height), Image.LANCZOS)
            self.start_y = event.y
            self.display_frame()

    def on_button_press_right(self, event):
        self.start_x = event.x
        self.start_y = event.y
        self.initial_frame_width, self.initial_frame_height = self.frames[self.current_frame].size
        
        # Capture initial mask dimensions for maintaining stretch ratio
        if self.mask_img_resized:
            self.initial_mask_width, self.initial_mask_height = self.mask_img_resized.size
        else:
            self.initial_mask_width, self.initial_mask_height = self.initial_frame_width, self.initial_frame_height

    def on_mouse_drag_right(self, event):
        if self.frames and self.mask_img_original:
            delta_x = event.x - self.start_x
            delta_y = event.y - self.start_y

            if self.aspect_ratio_locked.get():
                # Compute the scaling factor
                delta = max(delta_x, delta_y, key=abs)
                scaling_factor = 1 + (delta / float(self.initial_frame_width))
                new_frame_width = int(self.initial_frame_width * scaling_factor)
                new_frame_height = int(self.initial_frame_height * scaling_factor)
            else:
                new_frame_width = max(int(self.initial_frame_width + delta_x), 1)
                new_frame_height = max(int(self.initial_frame_height + delta_y), 1)

            # Resize the frame
            self.frames[self.current_frame] = self.original_frames[self.current_frame].resize(
                (new_frame_width, new_frame_height), Image.LANCZOS)

            if self.mask_img_resized:
                # Calculate the stretch ratio based on initial mask resize
                width_ratio = new_frame_width / self.initial_frame_width
                height_ratio = new_frame_height / self.initial_frame_height
                
                # Adjust mask dimensions based on the initial stretching
                new_mask_width = int(self.initial_mask_width * width_ratio)
                new_mask_height = int(self.initial_mask_height * height_ratio)

                self.mask_img_resized = self.mask_img_original.resize(
                    (new_mask_width, new_mask_height), Image.LANCZOS)

            self.width_value.set(str(new_frame_width))
            self.height_value.set(str(new_frame_height))

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
        else:
            self.cutout_button.config(state=tk.DISABLED)

    def save_gif(self):
        if not self.frames:
            return
        output_name = filedialog.asksaveasfilename(initialdir=self.last_save_directory, defaultextension=".gif", filetypes=[("GIF Files", "*.gif")])
        if not output_name:
            return
        # Update last save directory
        self.last_save_directory = os.path.dirname(output_name)
        self.save_config()

        self.frames[0].save(output_name, save_all=True, append_images=self.frames[1:], loop=0, disposal=2)
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