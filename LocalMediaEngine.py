import os
import sys
import threading
import queue
import subprocess
import re
import webbrowser
import customtkinter as ctk
from tkinter import filedialog

# ==========================================
# 0. RESOURCE PATH HELPER (FOR PYINSTALLER)
# ==========================================
def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

FFMPEG_BIN = resource_path("ffmpeg.exe")
COOKIES_FILE = resource_path("cookies.txt")


# ==========================================
# 1. CORE APPLICATION CLASS (GUI & ROUTING)
# ==========================================
class ModernMediaApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("LOCAL MEDIA ENGINE | Offline Privacy-First Converter")
        self.geometry("950x650")
        ctk.set_appearance_mode("dark")
        self.configure(fg_color="#1e2329")

        self.target_folder = os.path.join(os.path.expanduser("~"), "Downloads", "MediaEngine_Output")
        if not os.path.exists(self.target_folder):
            os.makedirs(self.target_folder, exist_ok=True)
            
        self.task_queue = queue.Queue()
        self.current_page = None
        self.is_animating = False
        
        self.cancel_flag = False
        self.current_process = None
        self.success_count = 0

        self.container = ctk.CTkFrame(self, fg_color="transparent")
        self.container.pack(fill="both", expand=True)
        
        self.frames = {}
        for F in (HomePage, YouTubePage, DocumentFormatPage, CodecExtractionPage):
            page_name = F.__name__
            frame = F(parent=self.container, controller=self)
            self.frames[page_name] = frame
            frame.place(relx=1.5, rely=0, relwidth=1, relheight=1) 

        self.current_page = self.frames["HomePage"]
        self.current_page.place(relx=0, rely=0, relwidth=1, relheight=1)

        self.build_floating_status()
        self.check_queue()

    def check_queue(self):
        try:
            while True:
                msg = self.task_queue.get_nowait()
                if msg["type"] == "status":
                    self.update_status(msg["text"], msg.get("color", "info"))
                elif msg["type"] == "metrics":
                    if hasattr(self.current_page, 'update_metrics'):
                        self.current_page.update_metrics(
                            size=msg.get("size"), 
                            speed=msg.get("speed"), 
                            time=msg.get("time"),
                            progress=msg.get("progress")
                        )
                elif msg["type"] == "success_redirect":
                    self.success_count += 1
                    # Redirect on odd sequences: 1, 3, 5, 7, etc.
                    if self.success_count % 2 != 0:
                        webbrowser.open("https://localmediaengineofficial.blogspot.com/p/process-complete-your-media-has-been.html")
        except queue.Empty:
            pass
        finally:
            self.after(100, self.check_queue)

    def change_target_folder(self):
        folder = filedialog.askdirectory(initialdir=self.target_folder)
        if folder:
            self.target_folder = folder
            for frame in self.frames.values():
                if hasattr(frame, 'lbl_folder'):
                    frame.lbl_folder.configure(text=f"Target: {self.target_folder}")
            self.update_status("Target folder updated successfully.", "success")

    def update_status(self, message, msg_type="info"):
        colors = {"info": "#a8c7fa", "success": "#4ade80", "error": "#ef4444", "warning": "#fbbf24"}
        text_color = colors.get(msg_type, "#a8c7fa")
        self.lbl_status.configure(text=f"STATUS: {msg_type.upper()} |\n{message}", text_color=text_color)

    def show_frame(self, page_name, direction="left"):
        if self.is_animating: return
        self.is_animating = True
        next_page = self.frames[page_name]
        if self.current_page == next_page:
            self.is_animating = False
            return
        start_x = 1.0 if direction == "left" else -1.0
        next_page.place(relx=start_x, rely=0, relwidth=1, relheight=1)
        next_page.tkraise()
        self.slide_animation(self.current_page, next_page, start_x, 0)

    def slide_animation(self, current_page, next_page, current_pos, step):
        steps = 20
        if step <= steps:
            offset = (step / steps) * (1.0 if current_pos > 0 else -1.0)
            current_page.place(relx=0 - offset, rely=0)
            next_page.place(relx=current_pos - offset, rely=0)
            self.after(15, lambda: self.slide_animation(current_page, next_page, current_pos, step + 1))
        else:
            current_page.place_forget()
            next_page.place(relx=0, rely=0)
            self.current_page = next_page
            self.is_animating = False

    def build_floating_status(self):
        self.status_frame = ctk.CTkFrame(self, fg_color="#23353b", corner_radius=12, border_width=1, border_color="#3b5358")
        self.status_frame.place(relx=0.97, rely=0.95, anchor="se")
        self.lbl_status = ctk.CTkLabel(self.status_frame, text="STATUS: IDLE |\nSystem Ready...", justify="left", text_color="#a8c7fa")
        self.lbl_status.pack(padx=20, pady=15)


# ==========================================
# 2. UI PAGES
# ==========================================
class HomePage(ctk.CTkFrame):
    def __init__(self, parent, controller):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller
        self.main_box = ctk.CTkFrame(self, fg_color="#22272e", corner_radius=12, border_width=1, border_color="#3d444d")
        self.main_box.place(relx=0.5, rely=0.45, anchor="center")
        ctk.CTkLabel(self.main_box, text="SELECT WORKSPACE", font=ctk.CTkFont(size=16, weight="bold"), text_color="#e6edf3").pack(pady=(30, 20))
        self.btn_frame = ctk.CTkFrame(self.main_box, fg_color="transparent")
        self.btn_frame.pack(padx=40, pady=(0, 40))

        btn_yt = ctk.CTkButton(self.btn_frame, text="🌐\nYouTube Video\nDownload", width=160, height=100, fg_color="#1f2937", command=lambda: controller.show_frame("YouTubePage", "left"))
        btn_yt.pack(side="left", padx=10)
        btn_doc = ctk.CTkButton(self.btn_frame, text="📄\nDocument &\nFormat Hub", width=160, height=100, fg_color="#1f2937", command=lambda: controller.show_frame("DocumentFormatPage", "left"))
        btn_doc.pack(side="left", padx=10)
        btn_codec = ctk.CTkButton(self.btn_frame, text="🎬\nCodec &\nExtraction Hub", width=160, height=100, fg_color="#1f2937", command=lambda: controller.show_frame("CodecExtractionPage", "left"))
        btn_codec.pack(side="left", padx=10)

class BaseSubPage(ctk.CTkFrame):
    def __init__(self, parent, controller, title):
        super().__init__(parent, fg_color="transparent")
        self.controller = controller

        self.btn_back = ctk.CTkButton(self, text="← Back to Menu", width=120, fg_color="transparent", border_width=1, border_color="#3d444d", command=lambda: controller.show_frame("HomePage", "right"))
        self.btn_back.pack(anchor="nw", padx=30, pady=(30, 0))

        self.main_frame = ctk.CTkFrame(self, fg_color="#22272e", corner_radius=12, border_width=1, border_color="#3d444d")
        self.main_frame.pack(padx=60, pady=20, fill="both", expand=True)
        self.lbl_title = ctk.CTkLabel(self.main_frame, text=title.upper(), font=ctk.CTkFont(size=15, weight="bold"), text_color="#e6edf3")
        self.lbl_title.pack(anchor="w", padx=30, pady=(20, 10))

    def build_file_inputs(self, source_placeholder="C:\\Videos\\INPUT_FILE.mp4", allow_browse=True):
        self.file_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.file_frame.pack(fill="x", padx=30, pady=(0, 10))
        
        self.file_entry = ctk.CTkEntry(self.file_frame, placeholder_text=source_placeholder, height=45, fg_color="#161b22", border_color="#3d444d")
        self.file_entry.pack(side="left", fill="x", expand=True, padx=(0, 10 if allow_browse else 0))
        self.file_entry.bind("<FocusOut>", self.check_file_size)
        
        if allow_browse:
            self.btn_browse_file = ctk.CTkButton(self.file_frame, text="📁", width=45, height=45, fg_color="#21262d", command=self.browse_file)
            self.btn_browse_file.pack(side="right")

        self.folder_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.folder_frame.pack(fill="x", padx=30, pady=(0, 15))
        self.lbl_folder = ctk.CTkLabel(self.folder_frame, text=f"Target: {self.controller.target_folder}", text_color="#8b949e")
        self.lbl_folder.pack(side="left")
        ctk.CTkButton(self.folder_frame, text="Change Folder", width=120, fg_color="#21262d", command=self.controller.change_target_folder).pack(side="right")

    def build_metrics_panel(self):
        self.metrics_frame = ctk.CTkFrame(self.main_frame, fg_color="#161b22", border_color="#3d444d", border_width=1)
        self.metrics_frame.pack(fill="x", padx=30, pady=(0, 15))
        
        self.lbl_size = ctk.CTkLabel(self.metrics_frame, text="Total Size: --", text_color="#8b949e", font=ctk.CTkFont(size=11))
        self.lbl_size.pack(side="left", expand=True, pady=8)
        
        self.lbl_progress = ctk.CTkLabel(self.metrics_frame, text="Progress: --", text_color="#8b949e", font=ctk.CTkFont(size=11, weight="bold"))
        self.lbl_progress.pack(side="left", expand=True, pady=8)
        
        self.lbl_speed = ctk.CTkLabel(self.metrics_frame, text="Speed: --", text_color="#8b949e", font=ctk.CTkFont(size=11))
        self.lbl_speed.pack(side="left", expand=True, pady=8)
        self.lbl_time = ctk.CTkLabel(self.metrics_frame, text="Est. Time: --", text_color="#8b949e", font=ctk.CTkFont(size=11))
        self.lbl_time.pack(side="left", expand=True, pady=8)

    def build_action_buttons(self, command_callback):
        self.action_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.action_frame.pack(pady=(10, 20))
        
        self.btn_start = ctk.CTkButton(self.action_frame, text="START PROCESSING", font=ctk.CTkFont(weight="bold"), fg_color="#4ade80", hover_color="#22c55e", text_color="#064e3b", height=45, width=220, command=command_callback)
        self.btn_start.pack(side="left", padx=10)

        self.btn_cancel = ctk.CTkButton(self.action_frame, text="CANCEL", font=ctk.CTkFont(weight="bold"), fg_color="#ef4444", hover_color="#dc2626", text_color="#7f1d1d", height=45, width=100, command=self.cancel_job)
        self.btn_cancel.pack(side="left", padx=10)

    def cancel_job(self):
        self.controller.cancel_flag = True
        if self.controller.current_process:
            try:
                self.controller.current_process.kill()
            except:
                pass
        self.controller.update_status("Task Cancelled by User.", "warning")
        self.update_metrics(size="--", progress="Cancelled", speed="--", time="--")

    def browse_file(self):
        path = filedialog.askopenfilename()
        if path:
            self.file_entry.delete(0, 'end')
            self.file_entry.insert(0, path)
            self.check_file_size()

    def check_file_size(self, event=None):
        path = self.file_entry.get().strip().strip('"')
        if os.path.exists(path):
            size_mb = os.path.getsize(path) / (1024 * 1024)
            self.update_metrics(size=f"{size_mb:.2f} MB", progress="Ready", speed="--", time="--")

    def update_metrics(self, size=None, speed=None, time=None, progress=None):
        if size: self.lbl_size.configure(text=f"Total Size: {size}")
        if progress: self.lbl_progress.configure(text=f"Progress: {progress}")
        if speed: self.lbl_speed.configure(text=f"Speed: {speed}")
        if time: self.lbl_time.configure(text=f"Est. Time: {time}")

class YouTubePage(BaseSubPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "YouTube Video Download")
        self.build_file_inputs(source_placeholder="Paste URL here: https://youtu.be/...", allow_browse=False)
        self.build_metrics_panel()
        
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=30, pady=10)
        ctk.CTkLabel(self.options_frame, text="Select Mode:", text_color="#8b949e").pack(side="left")
        
        yt_options = ["YouTube full video and audio", "YouTube video only no audio", "YouTube audio only .mp3"]
        self.combo_mode = ctk.CTkComboBox(self.options_frame, values=yt_options, width=300, fg_color="#161b22", border_color="#3b82f6", button_color="#3b82f6")
        self.combo_mode.pack(side="right", fill="x", expand=True, padx=(20, 0))
        self.build_action_buttons(self.execute)

    def execute(self):
        url = self.file_entry.get().strip()
        mode = self.combo_mode.get()
        if not url: return self.controller.update_status("Please paste a URL.", "error")
        threading.Thread(target=process_engine, args=(self.controller, url, mode, "youtube"), daemon=True).start()

class DocumentFormatPage(BaseSubPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Document & Format Hub")
        self.build_file_inputs(source_placeholder="C:\\Path\\To\\Input_File (Media or Doc)")
        self.build_metrics_panel()
        
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=30, pady=10)

        self.col1 = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.col1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(self.col1, text="Media Format:", text_color="#8b949e").pack(anchor="w")
        format_opts = ["Video to .mp4", "Video to .gif", "Video to .webm", "Video to .mov", "Video to .mkv", "Audio to .wav", "Image to .png", "Image to .jpeg"]
        self.combo_format = ctk.CTkComboBox(self.col1, values=["-- None --"] + format_opts, fg_color="#161b22", border_color="#3d444d")
        self.combo_format.pack(fill="x", pady=5)

        self.col2 = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.col2.pack(side="right", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(self.col2, text="Document Route:", text_color="#8b949e").pack(anchor="w")
        doc_opts = [".docx to .pdf", ".pdf to .docx", ".pdf to image (.png)", ".jpeg to .pdf", ".png to .pdf"]
        self.combo_doc = ctk.CTkComboBox(self.col2, values=["-- None --"] + doc_opts, fg_color="#161b22", border_color="#3d444d")
        self.combo_doc.pack(fill="x", pady=5)
        self.build_action_buttons(self.execute)

    def execute(self):
        path = self.file_entry.get().strip().strip('"')
        fmt = self.combo_format.get()
        doc = self.combo_doc.get()
        if not path or not os.path.exists(path): return self.controller.update_status("Invalid file path.", "error")
        action = fmt if fmt != "-- None --" else doc
        if action == "-- None --": return self.controller.update_status("Select a conversion format.", "error")
        threading.Thread(target=process_engine, args=(self.controller, path, action, "format_doc"), daemon=True).start()

class CodecExtractionPage(BaseSubPage):
    def __init__(self, parent, controller):
        super().__init__(parent, controller, "Codec & Extraction Hub")
        self.build_file_inputs()
        self.build_metrics_panel()
        
        self.options_frame = ctk.CTkFrame(self.main_frame, fg_color="transparent")
        self.options_frame.pack(fill="x", padx=30, pady=10)

        self.col1 = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.col1.pack(side="left", fill="x", expand=True, padx=(0, 10))
        ctk.CTkLabel(self.col1, text="Codec Options:", text_color="#8b949e").pack(anchor="w")
        codec_opts = [
            "Standard AVC (H.264) to HEVC (H.265)", 
            "HEVC (H.265) to Standard AVC (H.264)", 
            "Standard AVC (H.264) to AV1",
            "AV1 to Standard AVC (H.264)",
            "Video to Apple ProRes 422", 
            "Apple ProRes to Standard Video (.mp4)"
        ]
        self.combo_codec = ctk.CTkComboBox(self.col1, values=["-- None --"] + codec_opts, fg_color="#161b22", border_color="#3b82f6", button_color="#3b82f6")
        self.combo_codec.pack(fill="x", pady=5)

        self.col2 = ctk.CTkFrame(self.options_frame, fg_color="transparent")
        self.col2.pack(side="right", fill="x", expand=True, padx=(10, 0))
        ctk.CTkLabel(self.col2, text="Media Extraction:", text_color="#8b949e").pack(anchor="w")
        
        extract_opts = ["Extract Audio", "Extract Video"]
        
        self.combo_extract = ctk.CTkComboBox(self.col2, values=["-- None --"] + extract_opts, fg_color="#161b22", border_color="#3b82f6", button_color="#3b82f6")
        self.combo_extract.pack(fill="x", pady=5)
        self.build_action_buttons(self.execute)

    def execute(self):
        path = self.file_entry.get().strip().strip('"')
        codec = self.combo_codec.get()
        extract = self.combo_extract.get()
        if not path or not os.path.exists(path): return self.controller.update_status("Invalid file path.", "error")
        action = codec if codec != "-- None --" else extract
        if action == "-- None --": return self.controller.update_status("Select an operation.", "error")
        threading.Thread(target=process_engine, args=(self.controller, path, action, "codec_ext"), daemon=True).start()


# ==========================================
# 3. BACKEND PROCESSING ENGINE
# ==========================================
def process_engine(app, input_data, action, mode):
    app.cancel_flag = False 
    app.current_process = None
    app.task_queue.put({"type": "status", "text": "Initializing Engine...", "color": "info"})
    
    out_dir = app.target_folder
    base_name = "output"
    if os.path.exists(input_data):
        base_name = os.path.splitext(os.path.basename(input_data))[0]
        
    creation_flags = 0
    if os.name == "nt":
        creation_flags = 0x08000000 
        
    try:
        # --- YOUTUBE MODE ---
        if mode == "youtube":
            import yt_dlp
            def hook(d):
                if app.cancel_flag: raise Exception("Cancelled by User")
                if d['status'] == 'downloading':
                    try:
                        app.task_queue.put({
                            "type": "metrics", 
                            "size": d.get('_total_bytes_str', '--'), 
                            "progress": d.get('_downloaded_bytes_str', '--'), 
                            "speed": d.get('_speed_str', '--'), 
                            "time": d.get('_eta_str', '--')
                        })
                    except: pass

            opts = {'outtmpl': os.path.join(out_dir, '%(title)s.%(ext)s'), 'progress_hooks': [hook], 'ffmpeg_location': FFMPEG_BIN}
            if os.path.exists(COOKIES_FILE): opts['cookiefile'] = COOKIES_FILE
            
            if action == "YouTube full video and audio": opts.update({'format': 'bestvideo+bestaudio/best', 'merge_output_format': 'mp4'})
            elif action == "YouTube video only no audio": opts.update({'format': 'bestvideo'})
            elif action == "YouTube audio only .mp3": opts.update({'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}]})
                
            app.task_queue.put({"type": "status", "text": "Downloading stream...", "color": "info"})
            with yt_dlp.YoutubeDL(opts) as ydl:
                ydl.download([input_data])
            
            if not app.cancel_flag:
                app.task_queue.put({"type": "status", "text": "Download Complete!", "color": "success"})
                app.task_queue.put({"type": "success_redirect"})
            return

        # --- FFMPEG (Formats, Codecs, Extractions) ---
        cmd = [FFMPEG_BIN, "-y", "-i", input_data]
        is_ffmpeg = False
        out_file = os.path.join(out_dir, f"{base_name}_processed.mp4")
        
        # FORMATS
        if action == "Video to .mp4":
            out_file = os.path.join(out_dir, f"{base_name}.mp4")
            cmd.extend(["-c:v", "libx264", "-preset", "fast", "-c:a", "aac"])
            is_ffmpeg = True
        elif action == "Video to .gif":
            out_file = os.path.join(out_dir, f"{base_name}.gif")
            cmd.extend(["-vf", "fps=15,scale=640:-1:flags=lanczos", "-c:v", "gif"])
            is_ffmpeg = True
        elif action == "Video to .webm":
            out_file = os.path.join(out_dir, f"{base_name}.webm")
            cmd.extend(["-c:v", "libvpx", "-b:v", "1M", "-c:a", "libvorbis"])
            is_ffmpeg = True
        elif action == "Video to .mov":
            out_file = os.path.join(out_dir, f"{base_name}.mov")
            cmd.extend(["-c:v", "libx264", "-c:a", "aac"])
            is_ffmpeg = True
        elif action == "Video to .mkv":
            out_file = os.path.join(out_dir, f"{base_name}.mkv")
            cmd.extend(["-c:v", "copy", "-c:a", "copy"])
            is_ffmpeg = True
        elif action == "Audio to .wav":
            out_file = os.path.join(out_dir, f"{base_name}.wav")
            cmd.extend(["-vn", "-c:a", "pcm_s16le"])
            is_ffmpeg = True
        elif action in ["Image to .png", "Image to .jpeg"]:
            ext = "." + action.split(".")[-1]
            out_file = os.path.join(out_dir, f"{base_name}{ext}")
            cmd.extend(["-c", "copy"])
            is_ffmpeg = True
            
        # CODECS
        elif action == "Standard AVC (H.264) to HEVC (H.265)":
            out_file = os.path.join(out_dir, f"{base_name}_HEVC.mp4")
            cmd.extend(["-c:v", "libx265", "-pix_fmt", "yuv420p", "-c:a", "copy"])
            is_ffmpeg = True
        elif action == "HEVC (H.265) to Standard AVC (H.264)":
            out_file = os.path.join(out_dir, f"{base_name}_AVC.mp4")
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy"])
            is_ffmpeg = True
        elif action == "Standard AVC (H.264) to AV1":
            out_file = os.path.join(out_dir, f"{base_name}_AV1.mkv")
            cmd.extend(["-c:v", "libaom-av1", "-cpu-used", "6", "-c:a", "copy"])
            is_ffmpeg = True
        elif action == "AV1 to Standard AVC (H.264)":
            out_file = os.path.join(out_dir, f"{base_name}_AVC_from_AV1.mp4")
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "copy"])
            is_ffmpeg = True
        elif action == "Video to Apple ProRes 422":
            out_file = os.path.join(out_dir, f"{base_name}_master.mov")
            cmd.extend(["-c:v", "prores_ks", "-profile:v", "3", "-pix_fmt", "yuv422p10le", "-c:a", "pcm_s16le"])
            is_ffmpeg = True
        elif action == "Apple ProRes to Standard Video (.mp4)":
            out_file = os.path.join(out_dir, f"{base_name}_from_prores.mp4")
            cmd.extend(["-c:v", "libx264", "-pix_fmt", "yuv420p", "-c:a", "aac"])
            is_ffmpeg = True
            
        # EXTRACTIONS
        elif action == "Extract Audio":
            out_file = os.path.join(out_dir, f"{base_name}_audio.mp3")
            cmd.extend(["-vn", "-c:a", "libmp3lame", "-q:a", "2"])
            is_ffmpeg = True
        elif action == "Extract Video":
            ext = os.path.splitext(input_data)[1] or ".mp4"
            out_file = os.path.join(out_dir, f"{base_name}_video_only{ext}")
            cmd.extend(["-map", "v:0", "-c:v", "copy", "-an"])
            is_ffmpeg = True

        if is_ffmpeg:
            cmd.append(out_file)
            app.task_queue.put({"type": "status", "text": "Encoding Media...", "color": "info"})
            
            process = subprocess.Popen(
                cmd, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT, 
                text=True, 
                universal_newlines=True,
                creationflags=creation_flags 
            )
            app.current_process = process
            
            for line in iter(process.stdout.readline, ''):
                if app.cancel_flag: break
                
                # Math conversion for KB to MB and Bitrate to MB/s
                size_match = re.search(r"size=\s*(\d+)[kK][bB]?", line)
                bitrate_match = re.search(r"bitrate=\s*([\d\.]+)\s*kbits/s", line, re.IGNORECASE)
                
                prog_str = None
                speed_str = None
                
                if size_match:
                    mb_size = int(size_match.group(1)) / 1024
                    prog_str = f"{mb_size:.2f} MB"
                    
                if bitrate_match:
                    mb_speed = float(bitrate_match.group(1)) / 8192
                    speed_str = f"{mb_speed:.2f} MB/s"
                
                if prog_str or speed_str:
                    app.task_queue.put({
                        "type": "metrics", 
                        "progress": prog_str if prog_str else "--",
                        "speed": speed_str if speed_str else "--", 
                        "time": "Computing..."
                    })
                    
            process.wait()
            if app.cancel_flag: return
            
            if process.returncode == 0:
                app.task_queue.put({"type": "status", "text": f"Saved: {os.path.basename(out_file)}", "color": "success"})
                app.task_queue.put({"type": "success_redirect"})
            else:
                app.task_queue.put({"type": "status", "text": "Engine Error. Check format compatibility.", "color": "error"})
            return

        # --- DOCUMENTS ---
        app.task_queue.put({"type": "status", "text": "Processing Document...", "color": "info"})
        
        # New Custom Word COM Script to prevent freeze!
        if action == ".docx to .pdf":
            try:
                import win32com.client
                import pythoncom
                pythoncom.CoInitialize()
                
                # Setup invisible, silent Word instance
                word = win32com.client.Dispatch("Word.Application")
                word.Visible = False
                word.DisplayAlerts = False # THIS FIXES THE FREEZE
                
                # Paths must be absolute for COM objects
                in_abs = os.path.abspath(input_data)
                out_abs = os.path.abspath(os.path.join(out_dir, f"{base_name}.pdf"))
                
                doc = word.Documents.Open(in_abs)
                doc.SaveAs(out_abs, FileFormat=17) # 17 = PDF format
                doc.Close()
                word.Quit()
                
            except Exception as e:
                try: word.Quit() 
                except: pass
                raise Exception(f"Word must be closed first. COM Error: {str(e)}")
            finally:
                try: pythoncom.CoUninitialize()
                except: pass
            
        elif action == ".pdf to .docx":
            from pdf2docx import Converter
            out_path = os.path.join(out_dir, f"{base_name}.docx")
            cv = Converter(input_data)
            cv.convert(out_path)
            cv.close()
            
        elif action in [".jpeg to .pdf", ".png to .pdf"]:
            from PIL import Image
            out_path = os.path.join(out_dir, f"{base_name}.pdf")
            img = Image.open(input_data).convert('RGB')
            img.save(out_path)
            
        elif action == ".pdf to image (.png)":
            import fitz 
            doc = fitz.open(input_data)
            for i in range(len(doc)):
                if app.cancel_flag: return
                page = doc.load_page(i)
                pix = page.get_pixmap(dpi=300)
                out_path = os.path.join(out_dir, f"{base_name}_page_{i+1}.png")
                pix.save(out_path)
        
        if not app.cancel_flag:
            app.task_queue.put({"type": "status", "text": "Document Converted Successfully!", "color": "success"})
            app.task_queue.put({"type": "success_redirect"})

    except Exception as e:
        if "Cancelled" in str(e): return
        app.task_queue.put({"type": "status", "text": f"Error: {str(e)}", "color": "error"})

# ==========================================
# 4. ENTRYPOINT
# ==========================================
if __name__ == "__main__":
    app = ModernMediaApp()
    app.mainloop()