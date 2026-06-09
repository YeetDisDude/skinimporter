import io
import base64
import json
import os
import threading
import ctypes
import tkinter
import tkinter.filedialog
import tkinter.messagebox
import customtkinter
import requests
from PIL import Image
from datetime import datetime
from colorama import Fore, Style, init

init(autoreset=True)

from skinimporter import add_skins, append_skin, clear_modded_skins, get_added_skins, delete_skin
from skin_utils import get_skin_size, is_valid_skin_size, is_skin_size_64x64, get_import_ready_skin_base64

def log_message(message_type: str, title: str, message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if message_type == "INFO":
        color = Fore.CYAN
    elif message_type == "ERROR":
        color = Fore.RED
    elif message_type == "WARNING":
        color = Fore.YELLOW
    else:
        color = Fore.WHITE
    
    print(f"{color}[{timestamp}] [{message_type}] {title}: {message}{Style.RESET_ALL}")

def show_info(title: str, message: str):
    log_message("INFO", title, message)
    tkinter.messagebox.showinfo(title, message)

def show_error(title: str, message: str):
    log_message("ERROR", title, message)
    tkinter.messagebox.showerror(title, message)

def show_warning(title: str, message: str):
    log_message("WARNING", title, message)
    tkinter.messagebox.showwarning(title, message)

customtkinter.set_appearance_mode("System")  # Modes: "System" (standard), "Dark", "Light"
customtkinter.set_default_color_theme("blue")  # Themes: "blue" (standard), "green", "dark-blue"

BUTTON_FG_COLOR = "#7C3AED"
BUTTON_HOVER_COLOR = "#5B21B6"
BUTTON_TEXT_COLOR = "white"

VERSION = "1.3"

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()

        # configure window
        self.title(f"Skin Importer v{VERSION}")
        self.geometry(f"{1100}x{580}")

        try:
            ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("YeetDisDude.SkinImporter")
        except Exception:
            pass

        icon_ico_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.ico")
        if os.path.exists(icon_ico_path):
            try:
                self.iconbitmap(icon_ico_path)
            except Exception:
                pass

        icon_png_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "icon.png")
        if os.path.exists(icon_png_path):
            try:
                self._taskbar_icon_image = tkinter.PhotoImage(file=icon_png_path)
                self.iconphoto(True, self._taskbar_icon_image)
            except Exception:
                pass

        # configure grid layout (sidebar + content)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # create sidebar frame with widgets
        self.sidebar_frame = customtkinter.CTkFrame(self, width=140, corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(6, weight=1)

        self.logo_label = customtkinter.CTkLabel(self.sidebar_frame, text="Skin Importer",
                                                  font=customtkinter.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        tab_names = ["Upload Skin", "Copy Skins", "Manage Skins", "Settings", "How to Use"]
        self.tab_buttons = []
        for i, name in enumerate(tab_names):
            btn = customtkinter.CTkButton(
                self.sidebar_frame, text=name,
                fg_color=BUTTON_FG_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                anchor="w",
                command=lambda idx=i: self.select_tab(idx)
            )
            btn.grid(row=i + 1, column=0, padx=10, pady=5, sticky="ew")
            self.tab_buttons.append(btn)

        self.appearance_mode_label = customtkinter.CTkLabel(self.sidebar_frame, text="Appearance Mode:", anchor="w")
        self.appearance_mode_label.grid(row=7, column=0, padx=20, pady=(10, 0))
        self.appearance_mode_optionemenu = customtkinter.CTkOptionMenu(
            self.sidebar_frame, values=["Light", "Dark", "System"],
            fg_color=BUTTON_FG_COLOR,
            button_color=BUTTON_FG_COLOR,
            button_hover_color=BUTTON_HOVER_COLOR,
            dropdown_fg_color=BUTTON_FG_COLOR,
            dropdown_hover_color=BUTTON_HOVER_COLOR,
            command=self.change_appearance_mode_event)
        self.appearance_mode_optionemenu.grid(row=8, column=0, padx=20, pady=(10, 10))

        # create tab content frames
        self.tab_frames = []
        for i in range(len(tab_names)):
            frame = customtkinter.CTkFrame(self, corner_radius=0, fg_color="transparent")
            frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
            frame.grid_columnconfigure(0, weight=1)
            self.build_tab_content(frame, i)
            frame.grid_remove()
            self.tab_frames.append(frame)

        # set default values
        self.appearance_mode_optionemenu.set("Dark")

        # select first tab
        self.current_tab = None
        self.select_tab(0)

        self.notification_label = customtkinter.CTkLabel(self, text="")
        self._notification_after_id = None

    def build_tab_content(self, frame, index):
        if index == 0:
            frame.grid_rowconfigure(3, weight=1)

            title_label = customtkinter.CTkLabel(frame, text="Upload Skins",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                                  anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

            btn_row = customtkinter.CTkFrame(frame, fg_color="transparent")
            btn_row.grid(row=1, column=0, padx=10, pady=(0, 6), sticky="w")

            browse_btn = customtkinter.CTkButton(btn_row, text="Add Skins", width=120,
                                                  fg_color=BUTTON_FG_COLOR,
                                                  hover_color=BUTTON_HOVER_COLOR,
                                                  text_color=BUTTON_TEXT_COLOR,
                                                  command=self.browse_skin_files)
            browse_btn.grid(row=0, column=0, padx=(0, 10))

            clear_btn = customtkinter.CTkButton(btn_row, text="Clear All", width=100,
                                                fg_color=BUTTON_FG_COLOR,
                                                hover_color=BUTTON_HOVER_COLOR,
                                                border_width=2,
                                                text_color=BUTTON_TEXT_COLOR,
                                                command=self.clear_skin_files)
            clear_btn.grid(row=0, column=1)

            import_row = customtkinter.CTkFrame(frame, fg_color="transparent")
            import_row.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="w")

            import_btn = customtkinter.CTkButton(import_row, text="Import", width=100,
                                                 fg_color=BUTTON_FG_COLOR,
                                                 hover_color=BUTTON_HOVER_COLOR,
                                                 text_color=BUTTON_TEXT_COLOR,
                                                 command=self.import_skin_files)
            import_btn.grid(row=0, column=0)

            self.preview_scroll = customtkinter.CTkScrollableFrame(frame, label_text="Selected Skins")
            self.preview_scroll.grid(row=3, column=0, padx=10, pady=(0, 10), sticky="nsew")
            self._preview_cols = 3
            self.preview_scroll.grid_columnconfigure((0, 1, 2), weight=1)
            self.preview_scroll._parent_canvas.bind("<Configure>", self._on_preview_scroll_resize)

            self._preview_images = []
            self._preview_cards = []
            return
        elif index == 1:
            frame.grid_rowconfigure(4, weight=1)

            title_label = customtkinter.CTkLabel(frame, text="Copy Skins",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                                  anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

            search_row = customtkinter.CTkFrame(frame, fg_color="transparent")
            search_row.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")
            search_row.grid_columnconfigure(1, weight=1)

            player_id_label = customtkinter.CTkLabel(search_row, text="Player ID:", anchor="w")
            player_id_label.grid(row=0, column=0, padx=(0, 8))

            self.player_id_entry = customtkinter.CTkEntry(search_row, placeholder_text="Enter Player ID...")
            validate_cmd = (self.register(self._validate_player_id_input), "%P")
            self.player_id_entry.configure(validate="key", validatecommand=validate_cmd)
            self.player_id_entry.grid(row=0, column=1, sticky="ew", padx=(0, 10))
            self.player_id_entry.bind("<Return>", lambda e: self._search_player())

            search_btn = customtkinter.CTkButton(search_row, text="Search", width=100,
                                                  fg_color=BUTTON_FG_COLOR,
                                                  hover_color=BUTTON_HOVER_COLOR,
                                                  text_color=BUTTON_TEXT_COLOR,
                                                  command=self._search_player)
            search_btn.grid(row=0, column=2)

            # player info panel (hidden until a search succeeds)
            self.player_info_frame = customtkinter.CTkFrame(frame, fg_color="transparent")
            self.player_info_frame.grid(row=2, column=0, padx=10, pady=(0, 4), sticky="ew")
            self.player_info_frame.grid_remove()

            self._player_avatar_image = None
            self.player_avatar_label = customtkinter.CTkLabel(self.player_info_frame, text="")
            self.player_avatar_label.grid(row=0, column=0, rowspan=2, padx=(0, 12))

            self.player_name_label = customtkinter.CTkLabel(
                self.player_info_frame, text="",
                font=customtkinter.CTkFont(size=13, weight="bold"), anchor="w"
            )
            self.player_name_label.grid(row=0, column=1, sticky="w")

            self.player_level_label = customtkinter.CTkLabel(
                self.player_info_frame, text="",
                font=customtkinter.CTkFont(size=11), anchor="w"
            )
            self.player_level_label.grid(row=1, column=1, sticky="w")

            self.search_status_label = customtkinter.CTkLabel(frame, text="", anchor="w",
                                                               font=customtkinter.CTkFont(size=11))
            self.search_status_label.grid(row=3, column=0, padx=10, pady=(0, 4), sticky="ew")

            self.copy_scroll = customtkinter.CTkScrollableFrame(frame, label_text="Player Skins")
            self.copy_scroll.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")
            self._copy_cols = 3
            self._copy_skins_data = []
            self.copy_scroll.grid_columnconfigure((0, 1, 2), weight=1)
            self.copy_scroll._parent_canvas.bind("<Configure>", self._on_copy_scroll_resize)

            self._copy_skin_images = []
            return
        elif index == 2:
            frame.grid_rowconfigure(4, weight=1)

            title_label = customtkinter.CTkLabel(frame, text="Manage Skins",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                                  anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

            subtitle_label = customtkinter.CTkLabel(
                frame,
                text="This is a list of skins you have modded",
                anchor="w",
                font=customtkinter.CTkFont(size=11)
            )
            subtitle_label.grid(row=1, column=0, padx=10, pady=(0, 4), sticky="ew")

            controls_row = customtkinter.CTkFrame(frame, fg_color="transparent")
            controls_row.grid(row=2, column=0, padx=10, pady=(0, 4), sticky="w")

            refresh_btn = customtkinter.CTkButton(
                controls_row,
                text="Refresh",
                width=100,
                fg_color=BUTTON_FG_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                command=self.refresh_manage_skins,
            )
            refresh_btn.grid(row=0, column=0, padx=(0, 8))

            self.manage_status_label = customtkinter.CTkLabel(
                frame,
                text="",
                anchor="w",
                font=customtkinter.CTkFont(size=11)
            )
            self.manage_status_label.grid(row=3, column=0, padx=10, pady=(0, 4), sticky="ew")

            self.manage_scroll = customtkinter.CTkScrollableFrame(frame, label_text="Added Skins")
            self.manage_scroll.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="nsew")
            self._manage_cols = 3
            self._manage_skins_data = []
            self.manage_scroll.grid_columnconfigure((0, 1, 2), weight=1)
            self.manage_scroll._parent_canvas.bind("<Configure>", self._on_manage_scroll_resize)

            self._manage_skin_images = []
            return
        elif index == 3:
            frame.grid_rowconfigure(5, weight=1)

            title_label = customtkinter.CTkLabel(frame, text="Settings",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                                  anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

            clear_btn = customtkinter.CTkButton(
                frame, text="Clear Modded Skins", width=180,
                fg_color=BUTTON_FG_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                command=self.clear_modded_skins
            )
            clear_btn.grid(row=1, column=0, padx=10, pady=(8, 0), sticky="nw")

            credits_header = customtkinter.CTkLabel(
                frame,
                text="Credits",
                anchor="w",
                font=customtkinter.CTkFont(size=13, weight="bold")
            )
            credits_header.grid(row=2, column=0, padx=10, pady=(8, 0), sticky="w")

            credits_names = customtkinter.CTkLabel(
                frame,
                text="Claude - making 99% of this\nStella - for player lookup tool",
                anchor="w",
                font=customtkinter.CTkFont(size=11)
            )
            credits_names.grid(row=3, column=0, padx=10, pady=(2, 0), sticky="w")

            made_by_label = customtkinter.CTkLabel(
                frame,
                text="made by YeetDisDude",
                anchor="w",
                font=customtkinter.CTkFont(size=11, weight="bold")
            )
            made_by_label.grid(row=4, column=0, padx=10, pady=(10, 0), sticky="w")
            return
        elif index == 4:
            title_label = customtkinter.CTkLabel(frame, text="How to Use",
                                                  font=customtkinter.CTkFont(size=18, weight="bold"),
                                                  anchor="w")
            title_label.grid(row=0, column=0, padx=10, pady=(10, 2), sticky="ew")

            upload_title = customtkinter.CTkLabel(
                frame,
                text="1) Upload skins",
                anchor="w",
                font=customtkinter.CTkFont(size=13, weight="bold")
            )
            upload_title.grid(row=1, column=0, padx=10, pady=(6, 2), sticky="w")

            upload_desc = customtkinter.CTkLabel(
                frame,
                text="Add skin files (64x32, 64x64, or any 2:1 size), then import.",
                anchor="w",
                justify="left",
                font=customtkinter.CTkFont(size=12)
            )
            upload_desc.grid(row=2, column=0, padx=10, pady=(0, 8), sticky="w")

            copy_title = customtkinter.CTkLabel(
                frame,
                text="2) Copy Skins",
                anchor="w",
                font=customtkinter.CTkFont(size=13, weight="bold")
            )
            copy_title.grid(row=3, column=0, padx=10, pady=(0, 2), sticky="w")

            copy_desc = customtkinter.CTkLabel(
                frame,
                text="Enter the player ID you want to copy skins from, then press Add.",
                anchor="w",
                justify="left",
                font=customtkinter.CTkFont(size=12)
            )
            copy_desc.grid(row=4, column=0, padx=10, pady=(0, 10), sticky="w")

            save_note = customtkinter.CTkLabel(
                frame,
                text="If you want the skins to save, click edit skin then save it because they are currently saved to the device.",
                anchor="w",
                justify="left",
                font=customtkinter.CTkFont(size=12, weight="bold")
            )
            save_note.grid(row=5, column=0, padx=10, pady=(0, 10), sticky="w")

            reopen_note = customtkinter.CTkLabel(
                frame,
                text="For the skins to appear, you have to reopen Pixel Gun 3D.",
                anchor="w",
                justify="left",
                font=customtkinter.CTkFont(size=12)
            )
            reopen_note.grid(row=6, column=0, padx=10, pady=(0, 10), sticky="w")
            return
        else:
            return

        title_label = customtkinter.CTkLabel(frame, text=title,
                                              font=customtkinter.CTkFont(size=18, weight="bold"),
                                              anchor="w")
        title_label.grid(row=0, column=0, padx=10, pady=(10, 6), sticky="ew")

        body_label = customtkinter.CTkLabel(frame, text=body, anchor="nw", justify="left")
        body_label.grid(row=1, column=0, padx=10, pady=(0, 10), sticky="nsew")

    def _search_player(self):
        player_id = self.player_id_entry.get().strip()
        if not player_id:
            self.search_status_label.configure(text="Please enter a Player ID.", text_color=("#B91C1C", "#F87171"))
            return
        self.search_status_label.configure(text="Searching...", text_color=("gray10", "gray90"))
        for widget in self.copy_scroll.winfo_children():
            widget.destroy()
        self._copy_skin_images.clear()
        threading.Thread(target=self._do_player_search, args=(player_id,), daemon=True).start()

    def _do_player_search(self, player_id: str):
        url = "https://asteroidpg3d.xyz/api/get_player_info"
        try:
            resp = requests.post(url, json={"player_id": player_id}, timeout=10)
            if resp.status_code == 404:
                try:
                    err_msg = resp.json().get("err", "Player not found.")
                except Exception:
                    err_msg = "Player not found."
                self.after(0, lambda m=err_msg: self._on_search_error(m))
                return
            resp.raise_for_status()
            data = resp.json()
        except requests.RequestException as error:
            msg = str(error)
            self.after(0, lambda m=msg: self.search_status_label.configure(text=f"Request failed: {m}", text_color=("#B91C1C", "#F87171")))
            return
        except Exception as error:
            msg = str(error)
            self.after(0, lambda m=msg: self.search_status_label.configure(text=f"Error: {m}", text_color=("#B91C1C", "#F87171")))
            return
        info = data.get("info", {})
        self.after(0, lambda: self._on_search_result(info))

    def _validate_player_id_input(self, new_value: str) -> bool:
        return new_value.isdigit() or new_value == ""

    def _on_search_error(self, msg: str):
        self.search_status_label.configure(text=msg, text_color=("#B91C1C", "#F87171"))
        self.player_info_frame.grid_remove()
        self.player_avatar_label.configure(image=None, text="")
        self._player_avatar_image = None
        self.player_name_label.configure(text="")
        self.player_level_label.configure(text="")

    def _on_search_result(self, info: dict):
        skins = info.get("skins", [])
        if not skins:
            self.search_status_label.configure(text="No skins found for this player.", text_color=("gray10", "gray90"))
            self.player_info_frame.grid_remove()
            return
        self.search_status_label.configure(text=f"Found {len(skins)} skin(s).", text_color=("gray10", "gray90"))
        self._update_player_info(info)
        self._populate_copy_results(skins)

    def _update_player_info(self, info: dict):
        username = info.get("username") or info.get("name") or "Unknown"
        level = info.get("level") or info.get("rank") or ""
        avatar_b64 = info.get("avatar", "")

        self.player_name_label.configure(text=username)
        self.player_level_label.configure(text=f"Level {level}" if level else "")

        if avatar_b64:
            try:
                img_bytes = base64.b64decode(avatar_b64)
                pil_img = Image.open(io.BytesIO(img_bytes)).resize((48, 48))
                ctk_img = customtkinter.CTkImage(light_image=pil_img, dark_image=pil_img, size=(48, 48))
                self._player_avatar_image = ctk_img
                self.player_avatar_label.configure(image=ctk_img, text="")
            except Exception:
                self.player_avatar_label.configure(image=None, text="")
        else:
            self.player_avatar_label.configure(image=None, text="")

        self.player_info_frame.grid()

    def _populate_copy_results(self, skins: list):
        self._copy_skins_data = skins
        for widget in self.copy_scroll.winfo_children():
            widget.destroy()
        self._copy_skin_images.clear()

        cols = self._copy_cols
        for i in range(20):
            self.copy_scroll.grid_columnconfigure(i, weight=0)
        for i in range(cols):
            self.copy_scroll.grid_columnconfigure(i, weight=1)

        for idx, skin in enumerate(skins):
            col = idx % cols
            row = idx // cols

            card = customtkinter.CTkFrame(self.copy_scroll)
            card.grid(row=row, column=col, padx=8, pady=8)

            frontview_b64 = skin.get("frontview", "")
            if frontview_b64:
                try:
                    img_bytes = base64.b64decode(frontview_b64)
                    pil_img = Image.open(io.BytesIO(img_bytes))
                    w, h = pil_img.size
                    display_w = 64
                    display_h = int(h * 64 / w) if w > 0 else 64
                    ctk_img = customtkinter.CTkImage(
                        light_image=pil_img, dark_image=pil_img,
                        size=(display_w, display_h)
                    )
                    self._copy_skin_images.append(ctk_img)
                    img_label = customtkinter.CTkLabel(card, image=ctk_img, text="")
                    img_label.grid(row=0, column=0, padx=8, pady=(8, 4))
                except Exception:
                    pass

            skin_name = skin.get("name", "Unknown")
            name_label = customtkinter.CTkLabel(card, text=skin_name,
                                                 font=customtkinter.CTkFont(size=11),
                                                 wraplength=100)
            name_label.grid(row=1, column=0, padx=8, pady=(0, 4))

            skin_b64 = skin.get("skin", "")
            add_btn = customtkinter.CTkButton(
                card, text="Add", width=80, height=28,
                fg_color=BUTTON_FG_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                command=lambda b=skin_b64, n=skin_name: self._add_copy_skin(b, n)
            )
            add_btn.grid(row=2, column=0, padx=8, pady=(0, 8))

    def _on_copy_scroll_resize(self, event):
        cols = max(1, event.width // 120 - 1)
        if cols != self._copy_cols:
            self._copy_cols = cols
            if self._copy_skins_data:
                self._populate_copy_results(self._copy_skins_data)

    def _on_preview_scroll_resize(self, event):
        cols = max(1, event.width // 160 - 1)
        if cols != self._preview_cols:
            self._preview_cols = cols
            self._relayout_preview_cards()

    def _relayout_preview_cards(self):
        for i in range(20):
            self.preview_scroll.grid_columnconfigure(i, weight=0)
        for i in range(self._preview_cols):
            self.preview_scroll.grid_columnconfigure(i, weight=1)
        for i, entry in enumerate(self._preview_cards):
            entry["card"].grid(row=i // self._preview_cols, column=i % self._preview_cols, padx=8, pady=8)

    def _add_copy_skin(self, skin_base64: str, skin_name: str):
        if not skin_base64:
            show_error("Error", "No skin data available for this entry.")
            return
        try:
            skin_id = append_skin(skin_base64, skin_name)
        except OSError as error:
            show_error("Error", f"Could not write skin to registry.\n\n{error}")
            return
        self._show_notification(
            f"'{skin_name}' added as skin ID {skin_id}. Saved on this device.",
            duration_ms=3500
        )

    def _show_notification(self, message: str, duration_ms: int = 3000):
        if self._notification_after_id is not None:
            self.after_cancel(self._notification_after_id)
            self._notification_after_id = None

        self.notification_label.configure(text=message)
        self.notification_label.place(relx=0.99, rely=0.98, anchor="se")

        def hide_notification():
            self.notification_label.place_forget()
            self._notification_after_id = None

        self._notification_after_id = self.after(duration_ms, hide_notification)

    def refresh_manage_skins(self):
        try:
            skins = get_added_skins()
        except OSError as error:
            self.manage_status_label.configure(text=f"Could not read registry: {error}")
            self._manage_skins_data = []
            for widget in self.manage_scroll.winfo_children():
                widget.destroy()
            self._manage_skin_images.clear()
            return

        self._manage_skins_data = skins
        self._populate_manage_skins(skins)

    def _populate_manage_skins(self, skins: list):
        for widget in self.manage_scroll.winfo_children():
            widget.destroy()
        self._manage_skin_images.clear()

        if not skins:
            self.manage_status_label.configure(text="No added skins found.")
            return

        self.manage_status_label.configure(text=f"Found {len(skins)} skin(s).")

        cols = self._manage_cols
        for i in range(20):
            self.manage_scroll.grid_columnconfigure(i, weight=0)
        for i in range(cols):
            self.manage_scroll.grid_columnconfigure(i, weight=1)

        for idx, skin in enumerate(skins):
            col = idx % cols
            row = idx // cols

            card = customtkinter.CTkFrame(self.manage_scroll)
            card.grid(row=row, column=col, padx=8, pady=6, sticky="n")
            card.grid_columnconfigure(1, weight=1)

            skin_b64 = skin.get("skin", "")
            if skin_b64:
                try:
                    img_bytes = base64.b64decode(skin_b64)
                    pil_img = Image.open(io.BytesIO(img_bytes)).resize((128, 64), Image.NEAREST)
                    ctk_img = customtkinter.CTkImage(light_image=pil_img, dark_image=pil_img, size=(128, 64))
                    self._manage_skin_images.append(ctk_img)
                    img_label = customtkinter.CTkLabel(card, image=ctk_img, text="")
                    img_label.grid(row=0, column=0, rowspan=2, padx=(8, 10), pady=8)
                except Exception:
                    fallback_label = customtkinter.CTkLabel(card, text="(preview unavailable)")
                    fallback_label.grid(row=0, column=0, rowspan=2, padx=(8, 10), pady=8)

            info_text = f"{skin.get('name', 'Unknown')}\nID: {skin.get('id', '?')}"
            info_label = customtkinter.CTkLabel(card, text=info_text, anchor="w", justify="left")
            info_label.grid(row=0, column=1, padx=(0, 8), pady=(8, 4), sticky="w")

            delete_btn = customtkinter.CTkButton(
                card,
                text="Delete",
                width=90,
                height=28,
                fg_color=BUTTON_FG_COLOR,
                hover_color=BUTTON_HOVER_COLOR,
                text_color=BUTTON_TEXT_COLOR,
                command=lambda sid=skin.get("id", ""), n=skin.get("name", "Unknown"): self._delete_managed_skin(sid, n)
            )
            delete_btn.grid(row=1, column=1, padx=(0, 8), pady=(0, 8), sticky="w")

    def _on_manage_scroll_resize(self, event):
        cols = max(1, event.width // 250 - 1)
        if cols != self._manage_cols:
            self._manage_cols = cols
            if self._manage_skins_data:
                self._populate_manage_skins(self._manage_skins_data)

    def _delete_managed_skin(self, skin_id: str, skin_name: str):
        if not skin_id:
            return
        try:
            delete_skin(skin_id)
        except OSError as error:
            show_error("Error", f"Could not delete skin from registry.\n\n{error}")
            return

        self._show_notification(f"Deleted '{skin_name}' (ID {skin_id}).")
        self.refresh_manage_skins()

    def browse_skin_files(self):
        paths = tkinter.filedialog.askopenfilenames(
            title="Select skin files",
            filetypes=[("PNG files", "*.png"), ("All files", "*.*")]
        )
        for path in paths:
            if any(entry["path"] == path for entry in self._preview_cards):
                continue
            self._add_skin_preview(path)

    def _add_skin_preview(self, path):
        image_size = get_skin_size(path)
        preview_width = 128
        preview_height = max(1, int(round(preview_width * (image_size[1] / image_size[0]))))
        img = Image.open(path).resize((preview_width, preview_height), Image.NEAREST)
        ctk_img = customtkinter.CTkImage(
            light_image=img,
            dark_image=img,
            size=(preview_width, preview_height),
        )
        self._preview_images.append(ctk_img)
        is_convertible_64x64 = is_skin_size_64x64(path)
        is_valid_size = is_valid_skin_size(path) or is_convertible_64x64

        card_index = len(self._preview_cards)
        col = card_index % self._preview_cols
        row = card_index // self._preview_cols

        card = customtkinter.CTkFrame(self.preview_scroll)
        card.grid(row=row, column=col, padx=8, pady=8)

        img_label = customtkinter.CTkLabel(card, image=ctk_img, text="")
        img_label.grid(row=0, column=0, padx=8, pady=(8, 4))

        name_label = customtkinter.CTkLabel(card, text=os.path.basename(path),
                                             font=customtkinter.CTkFont(size=11),
                                             wraplength=130)
        name_label.grid(row=1, column=0, padx=8, pady=(0, 4))

        size_text = f"{image_size[0]}x{image_size[1]}"
        if is_convertible_64x64:
            size_text = f"{size_text} - will auto-convert to 64x32"
        if not is_valid_size:
            size_text = f"{size_text} - expected 64x32 or 2:1"

        size_label = customtkinter.CTkLabel(
            card,
            text=size_text,
            font=customtkinter.CTkFont(size=11),
            text_color=("#0F766E", "#5EEAD4") if is_valid_size else ("#B45309", "#FBBF24")
        )
        size_label.grid(row=2, column=0, padx=8, pady=(0, 4))

        remove_btn = customtkinter.CTkButton(card, text="Remove", width=80, height=24,
                                              fg_color=BUTTON_FG_COLOR,
                                              hover_color=BUTTON_HOVER_COLOR,
                                              border_width=1,
                                              text_color=BUTTON_TEXT_COLOR,
                                              font=customtkinter.CTkFont(size=11),
                                              command=lambda idx=card_index: self._remove_skin_card(idx))
        remove_btn.grid(row=3, column=0, padx=8, pady=(0, 8))

        self._preview_cards.append({
            "card": card,
            "image": ctk_img,
            "path": path,
            "valid_size": is_valid_size,
        })

    def _remove_skin_card(self, index):
        if index >= len(self._preview_cards):
            return
        self._preview_cards[index]["card"].destroy()
        self._preview_cards[index] = None
        # re-layout remaining cards
        live = [c for c in self._preview_cards if c is not None]
        for i, entry in enumerate(live):
            entry["card"].grid(row=i // self._preview_cols, column=i % self._preview_cols, padx=8, pady=8)
        self._preview_cards = live
        self._preview_images = [c["image"] for c in live]

    def clear_skin_files(self):
        for widget in self.preview_scroll.winfo_children():
            widget.destroy()
        self._preview_images.clear()
        self._preview_cards.clear()

    def import_skin_files(self):
        if not self._preview_cards:
            show_info("Import", "No skin files selected.")
            return

        invalid_files = [os.path.basename(entry["path"]) for entry in self._preview_cards if not entry["valid_size"]]
        if invalid_files:
            show_error(
                "Invalid Skin Size",
                "These files are not 64x32 or another 2:1 size:\n\n" + "\n".join(invalid_files)
            )
            return

        image_paths = [entry["path"] for entry in self._preview_cards]
        skin_names_list = [os.path.basename(path) for path in image_paths]

        imported_ids = []
        try:
            for path, skin_name in zip(image_paths, skin_names_list):
                skin_b64 = get_import_ready_skin_base64(path)
                skin_id = append_skin(skin_b64, skin_name)
                imported_ids.append(skin_id)
        except OSError as error:
            show_error("Import Failed", f"Could not write skins to the registry.\n\n{error}")
            return
        except ValueError as error:
            show_error("Import Failed", str(error))
            return

        show_info(
            "Import Complete",
            f"Added {len(imported_ids)} skin(s).\n\n"
            + "\n".join(skin_names_list)
            + "\n\nClick edit the skin and save it to save the skin to the cloud. Right now it is only saved on this device."
        )


    def clear_modded_skins(self):
        confirmed = tkinter.messagebox.askyesno(
            "Clear Modded Skins",
            "This will delete User Skins, User Name Skins, and Current Equiped Skin from the registry.\n\nContinue?"
        )
        if not confirmed:
            return
        try:
            clear_modded_skins()
        except OSError as error:
            show_error("Error", f"Could not clear registry keys.\n\n{error}")
            return
        show_info("Done", "Modded skins have been cleared from the registry.")

    def select_tab(self, index):
        if self.current_tab is not None:
            self.tab_frames[self.current_tab].grid_remove()
            self.tab_buttons[self.current_tab].configure(fg_color=BUTTON_FG_COLOR, hover_color=BUTTON_HOVER_COLOR)
        self.current_tab = index
        self.tab_frames[index].grid()
        self.tab_buttons[index].configure(fg_color=BUTTON_FG_COLOR, hover_color=BUTTON_HOVER_COLOR)
        if index == 2:
            self.refresh_manage_skins()

    def change_appearance_mode_event(self, new_appearance_mode: str):
        customtkinter.set_appearance_mode(new_appearance_mode)

    def change_scaling_event(self, new_scaling: str):
        new_scaling_float = int(new_scaling.replace("%", "")) / 100
        customtkinter.set_widget_scaling(new_scaling_float)


if __name__ == "__main__":
    print("\n" + "="*60)
    print(f"Starting Skin Importer v{VERSION}")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60 + "\n")
    
    try:
        log_message("INFO", "APP", "Initializing application...")
        app = App()
        log_message("INFO", "APP", "Application initialized successfully")
        app.mainloop()
    except Exception as e:
        import traceback
        print("\n" + "="*60)
        print("ERROR - Application crashed!")
        print("="*60)
        print(f"Reason: {e}")
        print("-"*60)
        traceback.print_exc()
        print("="*60)
        input("Press Enter to close this window...")