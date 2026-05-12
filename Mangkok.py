# app.py
import tkinter as tk
import customtkinter as ctk
import threading
import time
from PIL import Image
from Mie import Bot
from EsTeh import log_message, resource_path

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("BOT MIE AYAM")
        self.geometry("900x600")
        try:
            self.iconbitmap(resource_path("assets/logo.ico"))
        except:
            pass

        # layout
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # sidebar
        self.sidebar_frame = ctk.CTkFrame(self, width=260, corner_radius=0, fg_color="gray20")
        self.sidebar_frame.grid(row=0, column=0, rowspan=6, sticky="nsew")
        self.sidebar_frame.grid_rowconfigure(11, weight=1)

        custom_font = ctk.CTkFont(family="Helvetica", size=13)

        # logo
        try:
            self.logo_image_dark = ctk.CTkImage(light_image=Image.open(resource_path("assets/dark-logo.png")), size=(90, 90))
            self.logo_image_light = ctk.CTkImage(light_image=Image.open(resource_path("assets/light-logo.png")), size=(90, 90))
            self.logo_image_label = ctk.CTkLabel(self.sidebar_frame, image=self.logo_image_dark, text="")
            self.logo_image_label.grid(row=0, column=0, padx=20, pady=(12, 10))
        except:
            pass

        # URL input
        self.link_label = ctk.CTkLabel(self.sidebar_frame, text="TikTok video URL:", font=custom_font, anchor="w")
        self.link_label.grid(row=1, column=0, padx=16, pady=(6,2), sticky="w")
        self.link_entry = ctk.CTkEntry(self.sidebar_frame, width=220, font=custom_font)
        self.link_entry.grid(row=2, column=0, padx=16, pady=(0,8))

        # Amount
        self.amount_label = ctk.CTkLabel(self.sidebar_frame, text="Amount (0 = unlimited):", font=custom_font, anchor="w")
        self.amount_label.grid(row=3, column=0, padx=16, pady=(2,2), sticky="w")
        self.amount_entry = ctk.CTkEntry(self.sidebar_frame, width=220, font=custom_font)
        self.amount_entry.insert(0, "0")
        self.amount_entry.grid(row=4, column=0, padx=16, pady=(0,8))

        # Mode selection
        self.mode_var = tk.StringVar(value="Views")
        self.mode_label = ctk.CTkLabel(self.sidebar_frame, text="Mode:", font=custom_font, anchor="w")
        self.mode_label.grid(row=5, column=0, padx=16, pady=(2,2), sticky="w")
        self.mode_menu = ctk.CTkOptionMenu(
            self.sidebar_frame,
            values=["Views", "Hearts", "Followers", "Shares", "Favorites"],
            variable=self.mode_var,
            width=220,
            font=custom_font
        )
        self.mode_menu.grid(row=6, column=0, padx=16, pady=(0,12))

        # Setup / Start button
        self.start_button = ctk.CTkButton(self.sidebar_frame, text="Setup", command=lambda: threading.Thread(target=self.setup_bot).start(), font=custom_font)
        self.start_button.grid(row=7, column=0, padx=16, pady=(4,10))

        # Stats & log area (main frame)
        self.main_frame = ctk.CTkFrame(self, corner_radius=0)
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        self.tab_view = ctk.CTkTabview(self.main_frame)
        self.tab_view.grid(row=0, column=0, padx=12, pady=12, sticky="nsew")

        self.log_tab = self.tab_view.add("Log")
        self.log_text = ctk.CTkTextbox(self.log_tab, height=360, width=560, font=custom_font)
        self.log_text.pack(padx=12, pady=12, fill="both", expand=True)

        self.stats_tab = self.tab_view.add("Stats")
        self.stats_frame = ctk.CTkFrame(self.stats_tab)
        self.stats_frame.pack(fill="both", expand=True, padx=12, pady=12)

        # Stats labels
        self.views = 0
        self.hearts = 0
        self.followers = 0
        self.shares = 0
        self.favorites = 0
        self.elapsed_time = 0
        self.start_time = None

        self.stats_labels = {
            "views": ctk.CTkLabel(self.stats_frame, text="Views Sent: 0", font=custom_font),
            "hearts": ctk.CTkLabel(self.stats_frame, text="Hearts Sent: 0", font=custom_font),
            "followers": ctk.CTkLabel(self.stats_frame, text="Followers Sent: 0", font=custom_font),
            "shares": ctk.CTkLabel(self.stats_frame, text="Shares Sent: 0", font=custom_font),
            "favorites": ctk.CTkLabel(self.stats_frame, text="Favorites Sent: 0", font=custom_font),
            "elapsed_time": ctk.CTkLabel(self.stats_frame, text="Elapsed Time: 00:00:00", font=custom_font)
        }

        for i, label in enumerate(self.stats_labels.values()):
            label.pack(anchor="w", pady=6)

        # Control flags
        self.running = False

        # Instantiate bot (provide log_message function)
        self.bot = Bot(self, log_message)

        # Theme switch + footer
        self.theme_switch_var = tk.StringVar(value="dark")
        self.theme_switch = ctk.CTkSwitch(self.sidebar_frame, text="Dark Mode", variable=self.theme_switch_var, onvalue="dark", offvalue="light", command=self.switch_theme, font=custom_font)
        self.theme_switch.grid(row=10, column=0, padx=16, pady=(6,6), sticky="s")

        self.version_label = ctk.CTkLabel(self, text="Version 1.2.0", fg_color="transparent", font=ctk.CTkFont(size=10))
        self.version_label.grid(row=11, column=0, padx=10, pady=(2,8), sticky="s")

    def switch_theme(self):
        if self.theme_switch_var.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def setup_bot(self):
        """Called on Setup button -> start browser and wait for manual captcha in browser."""
        self.start_button.configure(state="disabled", text="Setting up...")
        try:
            self.bot.setup_bot()
            # after setup, allow user to Start manually
            self.start_button.configure(state="normal", text="Start", command=self.start_bot)
            self.log_text.insert(tk.END, "Setup complete. Press START when ready.\n")
        except Exception as e:
            self.log_text.insert(tk.END, f"Setup failed: {e}\n")
            self.start_button.configure(text="Setup", state="normal")

    def start_bot(self):
        """Start the bot loop (after user solved captcha manually)."""
        vidUrl = self.link_entry.get().strip()
        if not vidUrl:
            log_message(self, "Please enter a video URL first.")
            return

        try:
            amount = int(self.amount_entry.get().strip())
        except:
            log_message(self, "Amount must be a number (0 = unlimited).")
            return

        mode = self.mode_var.get()
        # disable inputs while running
        self.link_entry.configure(state="disabled")
        self.amount_entry.configure(state="disabled")
        self.mode_menu.configure(state="disabled")
        self.start_button.configure(text="Stop", command=self.stop_bot)

        self.running = True
        self.bot.running = True
        self.start_time = time.time()

        # clear log
        self.log_text.delete(1.0, tk.END)
        log_message(self, f"Bot starting (mode={mode}, amount={amount})")

        # start threads: bot loop + ui stats updater
        threading.Thread(target=self.bot.loop, args=(vidUrl, mode, amount), daemon=True).start()
        threading.Thread(target=self.update_stats_label, daemon=True).start()

    def stop_bot(self):
        self.log_text.insert(tk.END, "Stopping bot...\n")
        self.link_entry.configure(state="normal")
        self.amount_entry.configure(state="normal")
        self.mode_menu.configure(state="normal")
        self.running = False
        self.bot.running = False
        self.start_button.configure(text="Start", command=self.start_bot)
        # preserve elapsed_time
        if self.start_time:
            self.elapsed_time = time.time() - self.start_time
        log_message(self, "Bot stopped.")

    def update_stats_label(self):
        while self.running and self.bot.running:
            # update elapsed
            elapsed = int(time.time() - self.start_time) if self.start_time else 0
            timestr = time.strftime('%H:%M:%S', time.gmtime(elapsed))
            try:
                self.stats_labels["elapsed_time"].configure(text=f"Elapsed Time: {timestr}")
                self.stats_labels["views"].configure(text=f"Views Sent: {self.views}")
                self.stats_labels["hearts"].configure(text=f"Hearts Sent: {self.hearts}")
                self.stats_labels["followers"].configure(text=f"Followers Sent: {self.followers}")
                self.stats_labels["shares"].configure(text=f"Shares Sent: {self.shares}")
                self.stats_labels["favorites"].configure(text=f"Favorites Sent: {self.favorites}")
            except Exception:
                pass
            time.sleep(1)

if __name__ == "__main__":
    ctk.set_appearance_mode("dark")
    app = App()
    app.mainloop()
