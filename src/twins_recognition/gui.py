"""tkinter GUI 実装: 画像/フォルダ選択して結果表示"""
import tkinter as tk
from tkinter import filedialog, ttk, messagebox
import threading
import os
from typing import List

from .processor import analyze_image
from .cli import collect_images

class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Twins Recognition (Local)")
        self.geometry("640x480")
        self._build()

    def _build(self):
        frm = ttk.Frame(self)
        frm.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        btn_img = ttk.Button(frm, text="画像を選択", command=self.select_image)
        btn_img.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        btn_dir = ttk.Button(frm, text="フォルダを選択", command=self.select_folder)
        btn_dir.grid(row=0, column=1, padx=5, pady=5, sticky="w")
        self.tree = ttk.Treeview(frm, columns=("label", "distance", "faces"), show="headings")
        self.tree.heading("label", text="分類")
        self.tree.heading("distance", text="距離")
        self.tree.heading("faces", text="検出顔数")
        self.tree.grid(row=1, column=0, columnspan=4, sticky="nsew")
        frm.rowconfigure(1, weight=1)
        frm.columnconfigure(3, weight=1)
        self.status = tk.StringVar(value="準備完了")
        ttk.Label(frm, textvariable=self.status).grid(row=2, column=0, columnspan=4, sticky="w")

    def select_image(self):
        path = filedialog.askopenfilename(
            title="画像選択",
            filetypes=[("Images", ".jpg .jpeg .png .bmp .webp .tif .tiff .gif .jp2 .ppm .pnm .pbm .pgm")]
        )
        if not path:
            return
        self.process_images([path])

    def select_folder(self):
        folder = filedialog.askdirectory(title="フォルダ選択")
        if not folder:
            return
        imgs = collect_images(folder)
        if not imgs:
            messagebox.showinfo("情報", "画像が見つかりません")
            return
        self.process_images(imgs)

    def process_images(self, paths: List[str]):
        self.status.set("処理中...")
        self.tree.delete(*self.tree.get_children())
        def worker():
            for p in paths:
                try:
                    a = analyze_image(p)
                    dist = a.classification.distance
                    self.tree.insert("", tk.END, values=(a.classification.label, f"{dist:.3f}" if dist else "-", len(a.faces)))
                except Exception as e:
                    self.tree.insert("", tk.END, values=(f"error:{e}", "-", "-"))
            self.status.set("完了")
        threading.Thread(target=worker, daemon=True).start()


def run_gui():
    app = App()
    app.mainloop()

if __name__ == "__main__":
    run_gui()
