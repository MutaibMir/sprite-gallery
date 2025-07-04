import os, json, base64
from io import BytesIO
from PIL import Image as PILImage

from kivy.app import App
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.core.image import Image as CoreImage
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.filechooser import FileChooserIconView
from kivy.uix.popup import Popup
from kivy.uix.widget import Widget

# === CONFIG ===
CACHE_FILE = ".viewsprite.json"
SPRITES_PER_PAGE = 8
SPRITES_PER_ROW = 2
CELL_SIZE = 512
ZOOM_SIZE = 1024

def load_cached():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def load_cached():
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                return json.load(f)
        except:
            pass
    return {}

def save_cached(data):
    with open(CACHE_FILE, "w") as f:
        json.dump(data, f)
        
cached = load_cached()
class CollectionList(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.path = cached.get("json_path") or "/sdcard/"
        self.layout = BoxLayout(orientation='vertical')

        # Top bar with buttons
        topbar = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
        self.change_btn = Button(text="Change Folder", size_hint_y=None, height=60)
        self.reload_btn = Button(text="Reload", size_hint_y=None, height=60)
        self.change_btn.bind(on_press=self.select_folder)
        self.reload_btn.bind(on_press=self.load_collections)
        topbar.add_widget(self.change_btn)
        topbar.add_widget(self.reload_btn)

        # Scrollable grid of collections
        self.scroll = ScrollView()
        self.grid = GridLayout(cols=1, spacing=10, size_hint_y=None, padding=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        self.layout.add_widget(topbar)
        self.layout.add_widget(self.scroll)
        self.add_widget(self.layout)

        if self.path and os.path.isdir(self.path):
            self.load_collections()

    def select_folder(self, *_):
        from kivy.uix.filechooser import FileChooserListView

        self.selected_path = None  # Track selection

        box = BoxLayout(orientation='vertical')
        chooser = FileChooserListView(path="/sdcard/", dirselect=True, size_hint=(1, 0.9))
        confirm = Button(text="Use This Folder", size_hint=(1, 0.1))

        def on_selection(_, selection):
            if selection:
                self.selected_path = selection[0]

        def on_confirm(_):
            if self.selected_path and os.path.isdir(self.selected_path):
                self.path = self.selected_path
                cached["json_path"] = self.path
                save_cached(cached)
                popup.dismiss()
                self.load_collections()
            else:
                print("No valid folder selected")

        chooser.bind(selection=on_selection)
        confirm.bind(on_press=on_confirm)

        box.add_widget(chooser)
        box.add_widget(confirm)

        popup = Popup(title="Select JSON Folder", content=box, size_hint=(0.9, 0.9))
        popup.open()

    def load_collections(self, *_):
        self.grid.clear_widgets()
        if not self.path or not os.path.isdir(self.path):
            return
        files = [f for f in os.listdir(self.path) if f.endswith(".json")]
        for f in files:
            try:
                with open(os.path.join(self.path, f), "r") as fp:
                    data = json.load(fp)
                if "_textures" not in data:
                    continue
                name = data.get("Name", f)
                btn = Button(
                    text=f"{name}", bold=True, font_size=22,
                    size_hint_y=None, height=120
                )
                btn.bind(on_press=lambda _, d=data: self.open(d))
                self.grid.add_widget(btn)
            except Exception as e:
                print("Load error:", e)

    def open(self, data):
        viewer = self.manager.get_screen("viewer")
        viewer.load(data)
        self.manager.current = "viewer"
class SpriteTile(ButtonBehavior, BoxLayout):
    def __init__(self, raw, on_press_callback, index, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.size_hint = (None, None)
        self.size = (CELL_SIZE, CELL_SIZE)
        self.index = index
        self.on_press_callback = on_press_callback

        try:
            pil_img = PILImage.open(BytesIO(raw))
            w, h = pil_img.size
            scale = min(CELL_SIZE / w, CELL_SIZE / h)
            new_size = (int(w * scale), int(h * scale))
            resized = pil_img.resize(new_size, PILImage.NEAREST)
            buf = BytesIO()
            resized.save(buf, format='PNG')
            buf.seek(0)
            tex = CoreImage(buf, ext='png').texture
            self.img = Image(texture=tex, size_hint=(None, None), size=tex.size)
            wrapper = BoxLayout(size_hint=(None, None), size=(CELL_SIZE, CELL_SIZE))
            wrapper.add_widget(Widget())
            wrapper.add_widget(self.img)
            wrapper.add_widget(Widget())
            self.add_widget(Widget())
            self.add_widget(wrapper)
            self.add_widget(Widget())
        except Exception as e:
            print("Tile error:", e)

    def on_press(self):
        self.on_press_callback(self.index)

class SpriteViewer(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collection = None
        self.page = 0
        self.sort_mode = "A"
        self.sorted_indices = []

        self.layout = BoxLayout(orientation='vertical')
        top = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
        self.back = Button(text="Back", size_hint_y=None, height=60)
        self.sort = Button(text="Sort: By Alphabet", size_hint_y=None, height=60)
        self.back.bind(on_press=lambda *_: setattr(self.manager, "current", "list"))
        self.sort.bind(on_press=self.change_sort)
        top.add_widget(self.back)
        top.add_widget(self.sort)

        self.scroll = ScrollView()
        self.grid = GridLayout(cols=SPRITES_PER_ROW, spacing=10, size_hint_y=None, padding=10)
        self.grid.bind(minimum_height=self.grid.setter('height'))
        self.scroll.add_widget(self.grid)

        bottom = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
        self.prev = Button(text="← Prev", size_hint_y=None, height=60)
        self.label = Label(text="Page", size_hint_y=None, height=60)
        self.next = Button(text="Next →", size_hint_y=None, height=60)
        self.prev.bind(on_press=self.prev_page)
        self.next.bind(on_press=self.next_page)
        bottom.add_widget(self.prev)
        bottom.add_widget(self.label)
        bottom.add_widget(self.next)

        self.layout.add_widget(top)
        self.layout.add_widget(self.scroll)
        self.layout.add_widget(bottom)
        self.add_widget(self.layout)

    def load(self, data):
        self.collection = data
        self.page = 0
        self.apply_sort()
        self.refresh()

    def apply_sort(self):
        textures = self.collection["_textures"]
        names = self.collection.get("_textureNames", [])
        if self.sort_mode == "A":
            self.sorted_indices = sorted(range(len(textures)), key=lambda i: names[i] if i < len(names) else "")
        elif self.sort_mode == "S":
            self.sorted_indices = sorted(range(len(textures)), key=lambda i: self.get_res(i))
        else:
            from random import sample
            self.sorted_indices = sample(range(len(textures)), len(textures))

    def change_sort(self, *_):
        modes = {"A": "R", "R": "S", "S": "A"}
        labels = {"A": "Sort: By Alphabet", "R": "Sort: By Random", "S": "Sort: By Size"}
        self.sort_mode = modes[self.sort_mode]
        self.sort.text = labels[self.sort_mode]
        self.apply_sort()
        self.page = 0
        self.refresh()

    def get_res(self, index):
        try:
            raw = base64.b64decode(self.collection["_textures"][index])
            img = PILImage.open(BytesIO(raw))
            return img.width * img.height
        except: return 0

    def refresh(self):
        self.grid.clear_widgets()
        textures = self.collection["_textures"]
        total = len(textures)
        total_pages = (total + SPRITES_PER_PAGE - 1) // SPRITES_PER_PAGE
        self.label.text = f"Page {self.page+1} / {total_pages}"
        start = self.page * SPRITES_PER_PAGE
        end = min(start + SPRITES_PER_PAGE, total)

        for i in range(start, end):
            idx = self.sorted_indices[i]
            try:
                raw = base64.b64decode(textures[idx])
                tile = SpriteTile(raw=raw, on_press_callback=self.zoom, index=i)
                self.grid.add_widget(tile)
            except Exception as e:
                print("Sprite error:", e)

    def next_page(self, *_):
        total = len(self.collection["_textures"])
        if self.page < (total - 1) // SPRITES_PER_PAGE:
            self.page += 1
        else:
            self.page = 0
        self.refresh()

    def prev_page(self, *_):
        if self.page > 0:
            self.page -= 1
        else:
            self.page = (len(self.collection["_textures"]) - 1) // SPRITES_PER_PAGE
        self.refresh()

    def zoom(self, index):
        zoom_screen = self.manager.get_screen("zoom")
        zoom_screen.load(self.collection, self.sorted_indices, index)
        self.manager.current = "zoom"
class ZoomScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collection = None
        self.indices = []
        self.index = 0
        self.save_path = cached.get("save_path")

        self.layout = BoxLayout(orientation='vertical')

        self.top_bar = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
        self.back = Button(text="Back", size_hint_y=None, height=60)
        self.save1 = Button(text="Save Original", size_hint_y=None, height=60)
        self.save2 = Button(text="Save Resized", size_hint_y=None, height=60)
        self.back.bind(on_press=lambda *_: setattr(self.manager, "current", "viewer"))
        self.save1.bind(on_press=self.save_original)
        self.save2.bind(on_press=self.save_resized)
        self.top_bar.add_widget(self.back)
        self.top_bar.add_widget(self.save1)
        self.top_bar.add_widget(self.save2)

        self.img = Image()
        self.info = Label(size_hint_y=None, height=50)

        self.zoom_bottom_bar = BoxLayout(size_hint_y=None, height=80, padding=10, spacing=10)
        self.prev_btn = Button(text="← Previous", size_hint_y=None, height=60)
        self.counter = Label(text="Image X of Y", size_hint_y=None, height=60)
        self.next_btn = Button(text="Next →", size_hint_y=None, height=60)
        self.prev_btn.bind(on_press=self.prev)
        self.next_btn.bind(on_press=self.next)
        self.zoom_bottom_bar.add_widget(self.prev_btn)
        self.zoom_bottom_bar.add_widget(self.counter)
        self.zoom_bottom_bar.add_widget(self.next_btn)

        self.layout.add_widget(self.top_bar)
        self.layout.add_widget(self.img)
        self.layout.add_widget(self.info)
        self.layout.add_widget(self.zoom_bottom_bar)
        self.add_widget(self.layout)

    def load(self, collection, indices, current_idx):
        self.collection = collection
        self.indices = indices
        self.index = current_idx
        self.display()

    def display(self):
        try:
            i = self.indices[self.index]
            textures = self.collection["_textures"]
            raw = base64.b64decode(textures[i])
            names = self.collection.get("_textureNames", [])
            name = names[i] if i < len(names) else f"sprite_{i}"
            self.sprite_name = name
            self.raw = raw

            pil_img = PILImage.open(BytesIO(raw))
            w, h = pil_img.size
            scale = max(1, min(ZOOM_SIZE // w, ZOOM_SIZE // h))
            resized = pil_img.resize((w * scale, h * scale), PILImage.NEAREST)
            buf = BytesIO()
            resized.save(buf, format="PNG")
            buf.seek(0)
            self.img.texture = CoreImage(buf, ext="png").texture
            self.info.text = f"{name} ({w}×{h})"
            self.counter.text = f"Image {self.index+1} of {len(self.indices)}"
        except Exception as e:
            print("Zoom error:", e)

    def next(self, *_):
        self.index = (self.index + 1) % len(self.indices)
        self.display()

    def prev(self, *_):
        self.index = (self.index - 1 + len(self.indices)) % len(self.indices)
        self.display()

    def save_original(self, *_): self.save(False)
    def save_resized(self, *_): self.save(True)

    def save(self, resized=False):
        if not self.raw:
            return
        try:
            if not self.save_path or not os.path.exists(self.save_path):
                self.select_save_path(resized)
                return
            self._do_save(self.save_path, resized)
        except Exception as e:
            print("Save error:", e)

    def select_save_path(self, resized):
        self.selected_path = None
        box = BoxLayout(orientation='vertical')
        chooser = FileChooserIconView(path="/sdcard/", dirselect=True, size_hint=(1, 0.9))
        confirm = Button(text="Use This Folder", size_hint=(1, 0.1))

        def on_selection(_, selection):
            if selection:
                self.selected_path = selection[0]

        def on_confirm(_):
            if self.selected_path and os.path.isdir(self.selected_path):
                self.save_path = self.selected_path
                # Save both json_path and save_path
                cached["json_path"] = self.manager.get_screen("list").path
                cached["save_path"] = self.save_path
                save_cached(cached)
                popup.dismiss()
                self._do_save(self.save_path, resized)

        chooser.bind(selection=on_selection)
        confirm.bind(on_press=on_confirm)
        box.add_widget(chooser)
        box.add_widget(confirm)
        popup = Popup(title="Select Save Folder", content=box, size_hint=(0.9, 0.9))
        popup.open()

    def _do_save(self, path, resized):
        try:
            img = PILImage.open(BytesIO(self.raw))
            if resized:
                scale = max(1, min(ZOOM_SIZE // img.width, ZOOM_SIZE // img.height))
                img = img.resize((img.width * scale, img.height * scale), PILImage.NEAREST)
            filename = f"{self.sprite_name}_{'resized' if resized else 'original'}.png"
            img.save(os.path.join(path, filename))
            print("Saved:", filename)
        except Exception as e:
            print("Save error:", e)
class SpriteApp(App):
    def build(self):
        sm = ScreenManager()
        sm.add_widget(CollectionList(name="list"))
        sm.add_widget(SpriteViewer(name="viewer"))
        sm.add_widget(ZoomScreen(name="zoom"))
        return sm

if __name__ == "__main__":
    SpriteApp().run()


