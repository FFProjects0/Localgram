import sys
import os
import glob
import subprocess
import re
import math
import vlc
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# ——— Natural sort key ———
def natural_key(s):
    parts = re.split(r'(\d+)', s)
    return [int(p) if p.isdigit() else p.lower() for p in parts]

# ——— Helper: center-crop to square ———
def crop_to_square(pixmap: QPixmap) -> QPixmap:
    w, h = pixmap.width(), pixmap.height()
    side = min(w, h)
    x = (w - side) // 2
    y = (h - side) // 2
    return pixmap.copy(x, y, side, side)

# ——— 1. Load follower/following counts ———
with open("counts.txt", encoding="utf-8") as f:
    follower_count, following_count = map(int, f.read().splitlines())

# ——— 2. Load profile & posts ———
def load_text(path):
    return open(path, encoding="utf-8").read().strip()

username     = load_text("user.txt")
display_name = load_text("display.txt")
description  = load_text("desc.txt")
links        = load_text("links.txt").splitlines()

def load_posts(path):
    posts = []
    for ln in open(path, encoding="utf-8"):
        idx, rest = ln.strip().split('$', 1)
        date, title = rest.split(':', 1)
        posts.append({"id": idx, "date": date, "title": title})
    return posts

video_posts     = load_posts("videos.txt")
slideshow_posts = load_posts("slideshows.txt")

# ——— 3. Ensure thumbnail via ffmpeg ———
def ensure_thumb(video_path):
    base, _ = os.path.splitext(video_path)
    thumb = base + ".jpg"
    if not os.path.exists(thumb):
        subprocess.run([
            "ffmpeg", "-ss", "00:00:01", "-i", video_path,
            "-frames:v", "1", "-q:v", "2", "-y", thumb
        ], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    return thumb if os.path.exists(thumb) else ""

# ——— 4. Profile header widget ———
class ProfileHeaderWidget(QWidget):
    def __init__(self):
        super().__init__()
        # Username
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        user_lbl = QLabel(username)
        user_lbl.setStyleSheet("font-weight:bold; font-size:18pt; color:white;")

        # Avatar
        avatar = QLabel()
        pix = QPixmap("cover.png").scaled(100,100,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        avatar.setPixmap(pix)
        avatar.setFixedSize(100,100)
        avatar.setStyleSheet("border-radius:50px;")

        # Counts
        counts = QHBoxLayout()
        counts.addWidget(QLabel(f"<b>{len(video_posts)+len(slideshow_posts)}</b><br>Posts"))
        counts.addWidget(QLabel(f"<b>{follower_count}</b><br>Followers"))
        counts.addWidget(QLabel(f"<b>{following_count}</b><br>Following"))

        # Display name & description
        bio = QLabel(f"<b>{display_name}</b><br>{description}")
        bio.setWordWrap(True)
        bio.setStyleSheet("color:white;")

        # Links
        links_layout = QVBoxLayout()
        for url in links:
            link = QLabel(f"<a href='{url}' style='color:#3897f0'>{url}</a>")
            link.setOpenExternalLinks(True)
            links_layout.addWidget(link)

        # Layout assembly
        top = QHBoxLayout()
        top.addWidget(avatar)
        right = QVBoxLayout()
        right.addLayout(counts)
        top.addLayout(right)

        main = QVBoxLayout(self)
        main.setContentsMargins(10,10,10,10)
        main.addWidget(user_lbl, 0, Qt.AlignCenter)
        main.addLayout(top)
        main.addWidget(bio)
        main.addLayout(links_layout)

    def mask_image(imgdata, imgtype ='png', size = 64):

        # Load image
        image = QImage.fromData(imgdata, imgtype)

        # convert image to 32-bit ARGB (adds an alpha
        # channel ie transparency factor):
        image.convertToFormat(QImage.Format_ARGB32)

        # Crop image to a square:
        imgsize = min(image.width(), image.height())
        rect = QRect(
            (image.width() - imgsize) / 2,
            (image.height() - imgsize) / 2,
            imgsize,
            imgsize,
            )

        image = image.copy(rect)

        # Create the output image with the same dimensions
        # and an alpha channel and make it completely transparent:
        out_img = QImage(imgsize, imgsize, QImage.Format_ARGB32)
        out_img.fill(Qt.transparent)

        # Create a texture brush and paint a circle
        # with the original image onto the output image:
        brush = QBrush(image)

        # Paint the output image
        painter = QPainter(out_img)
        painter.setBrush(brush)

        # Don't draw an outline
        painter.setPen(Qt.NoPen)

        # drawing circle
        painter.drawEllipse(0, 0, imgsize, imgsize)

        # closing painter event
        painter.end()

        # Convert the image to a pixmap and rescale it.
        pr = QWindow().devicePixelRatio()
        pm = QPixmap.fromImage(out_img)
        pm.setDevicePixelRatio(pr)
        size *= pr
        pm = pm.scaled(size, size, Qt.KeepAspectRatio,
                       Qt.SmoothTransformation)

        # return back the pixmap data
        return pm

# ——— 5. Clickable label climbs to open_detail() ———
class ClickableLabel(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setCursor(Qt.PointingHandCursor)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            w = self.parent()
            # climb until we find open_detail()
            while w and not hasattr(w, "open_detail"):
                w = w.parent()
            if w:
                w.open_detail()

# ——— 6. Video thumbnail widget ———
class VideoThumbWidget(QWidget):
    def __init__(self, post):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self.post   = post
        self.detail = None
        # Load, crop, and store pixmap
        path = f"Videos/{post['id']}.mp4"
        thumb = ensure_thumb(path)
        orig = QPixmap(thumb) if thumb else QPixmap()
        self.crop = crop_to_square(orig)

        # Preload overlay icon
        self.icon = QPixmap(resource_path("reel.svg")).scaled(32,32,Qt.KeepAspectRatio,Qt.SmoothTransformation)

        # Styling
        self.setStyleSheet("border:1px solid white;")
        self.lbl = ClickableLabel(self)
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl.setAlignment(Qt.AlignCenter)

        self.icon_lbl = QLabel(self)
        self.icon_lbl.setPixmap(self.icon)
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        # Stack image + icon
        container = QFrame(self)
        stack = QStackedLayout(container)
        stack.setContentsMargins(0,0,0,0)
        stack.addWidget(self.lbl)
        stack.addWidget(self.icon_lbl)
        stack.setStackingMode(QStackedLayout.StackAll)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        layout.addWidget(container, alignment=Qt.AlignCenter)

    def open_detail(self):
        if not self.detail or not self.detail.isVisible():
            self.detail = VideoDetail(self.post, lambda: setattr(self, "detail", None))
        self.detail.show()
        self.detail.raise_()

    def setThumbnailSize(self, size):
        pm = self.crop.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl.setPixmap(pm)
        # Position icon at top-right
        self.icon_lbl.move(self.lbl.x() + size - 36, self.lbl.y() + 4)

# ——— 7. Video detail window ———
class VideoDetail(QWidget):
    def __init__(self, post, on_close):
        super().__init__()
        self._on_close = on_close
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle(post['title'])
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        vpath = f"Videos/{post['id']}.mp4"
        inst   = vlc.Instance()
        self.player = inst.media_player_new()
        self.player.set_media(inst.media_new(vpath))

        vf = QFrame(self)
        vf.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        if sys.platform.startswith("linux"):
            self.player.set_xwindow(vf.winId())
        elif sys.platform == "win32":
            self.player.set_hwnd(vf.winId())
        else:
            self.player.set_nsobject(int(vf.winId()))

        title = QLabel(post['title'], alignment=Qt.AlignCenter)
        title.setStyleSheet("color:white;")
        title.setMaximumHeight(30)

        v = QVBoxLayout(self)
        v.setContentsMargins(0,0,0,0)
        v.addWidget(vf, 5)
        v.addWidget(title, 1)

        self.player.play()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Space:
            self._toggle()

    def mouseReleaseEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._toggle()

    def _toggle(self):
        if self.player.is_playing():
            self.player.pause()
        else:
            self.player.play()

    def closeEvent(self, e):
        self.player.stop()
        try:
            self.player.release()
        except:
            pass
        self._on_close()
        super().closeEvent(e)

# ——— 8. Slideshow thumbnail widget ———
class SlideThumbWidget(QWidget):
    def __init__(self, post):
        super().__init__()
        self.post   = post
        self.detail = None
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        imgs = sorted(
            [fn for fn in glob.glob(f"Slideshows/{post['id']}/*")
             if os.path.splitext(fn)[1].lower() in (".jpg",".jpeg",".png",".bmp",".gif")],
            key=lambda fn: natural_key(os.path.basename(fn))
        )
        orig = QPixmap(imgs[0]) if imgs else QPixmap()
        self.crop = crop_to_square(orig)

        self.setStyleSheet("border:1px solid white;")
        self.lbl = ClickableLabel(self)
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.lbl.setAlignment(Qt.AlignCenter)

        self.icon_lbl = QLabel(self)
        icon = QPixmap(resource_path("slide.svg")).scaled(32,32,Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.icon_lbl.setPixmap(icon)
        self.icon_lbl.setAttribute(Qt.WA_TransparentForMouseEvents)

        container = QFrame(self)
        stack     = QStackedLayout(container)
        stack.setContentsMargins(0,0,0,0)
        stack.addWidget(self.lbl)
        stack.addWidget(self.icon_lbl)
        stack.setStackingMode(QStackedLayout.StackAll)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(container, alignment=Qt.AlignCenter)

    def open_detail(self):
        if not self.detail or not self.detail.isVisible():
            self.detail = SlideDetail(self.post, lambda: setattr(self, "detail", None))
        self.detail.show()
        self.detail.raise_()

    def setThumbnailSize(self, size):
        pm = self.crop.scaled(size, size, Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.lbl.setPixmap(pm)
        self.icon_lbl.move(self.lbl.x() + size - 36, self.lbl.y() + 4)

# ——— 9. Slideshow detail window ———
class SlideDetail(QWidget):
    def __init__(self, post, on_close):
        super().__init__()
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        self._on_close = on_close
        self.setAttribute(Qt.WA_DeleteOnClose)
        self.setWindowState(Qt.WindowMaximized)
        self.setWindowTitle(post['title'])

        folder = f"Slideshows/{post['id']}"
        self.images = sorted(
            [fn for fn in glob.glob(folder+"/*")
             if os.path.splitext(fn)[1].lower() in (".jpg",".jpeg",".png",".bmp",".gif")],
            key=lambda fn: natural_key(os.path.basename(fn))
        )
        self.idx = 0

        # ——— New: look for offset file ———
        offset_file = os.path.join(folder, "offset.txt")
        if os.path.exists(offset_file):
            try:
                offset = float(open(offset_file, encoding="utf-8").read().strip())
            except:
                offset = 0.0
        else:
            offset = 0.0

        # ——— Find audio track ———
        audio = next(
            (f for ext in (".mp3",".wav",".ogg",".flac")
             for f in glob.glob(f"{folder}/*" + ext)),
            None
        )
        if audio:
            inst = vlc.Instance()
            self.ap = inst.media_player_new()
            media = inst.media_new(audio)
            self.ap.set_media(media)
            # play and then seek
            self.ap.play()
            # store the QTimer so we can cancel it on close
            self._seek_timer = QTimer(self)
            self._seek_timer.setSingleShot(True)
            self._seek_timer.timeout.connect(lambda: self.ap.set_time(int(offset * 1000)))
            self._seek_timer.start(100)
            now = QLabel(f"Now playing: {os.path.basename(audio)}", alignment=Qt.AlignCenter)
        else:
            now = None

        self.top = QLabel("", alignment=Qt.AlignCenter)
        self.top.setStyleSheet("color:white;")
        self.lbl = QLabel(alignment=Qt.AlignCenter)
        self.lbl.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        prev = QPushButton("<")
        nxt  = QPushButton(">")
        prev.clicked.connect(self.prev)
        nxt.clicked.connect(self.next)
        nav = QHBoxLayout()
        nav.addWidget(prev)
        nav.addWidget(self.lbl, 3)
        nav.addWidget(nxt)

        title = QLabel(post['title'], alignment=Qt.AlignCenter)
        title.setStyleSheet("color:white;")
        title.setMaximumHeight(30)

        L = QVBoxLayout(self)
        L.setContentsMargins(0,0,0,0)
        if now: L.addWidget(now)
        L.addWidget(self.top)
        L.addLayout(nav, 5)
        L.addWidget(title, 1)

        self.show_image()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.show_image()

    def show_image(self):
        if not self.images: return
        pix = QPixmap(self.images[self.idx]).scaled(
            self.lbl.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
        )
        self.lbl.setPixmap(pix)
        self.top.setText(f"Slide {self.idx+1} of {len(self.images)}")

    def next(self):
        if self.idx < len(self.images)-1:
            self.idx += 1
            self.show_image()

    def prev(self):
        if self.idx > 0:
            self.idx -= 1
            self.show_image()

    def closeEvent(self, e):
        if hasattr(self, 'ap'):
            self.ap.stop()
            try:
                self.ap.release()
            except:
                pass
        self._on_close()
        super().closeEvent(e)

# ——— 10. Posts grid with dynamic sizing ———
class PostsGridWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.cells = []
        cont = QWidget()
        self.grid = QGridLayout(cont)
        self.grid.setHorizontalSpacing(3)
        self.grid.setVerticalSpacing(3)
        self.setWindowIcon(QIcon(resource_path("icon.ico")))

        posts = sorted(video_posts + slideshow_posts, key=lambda p: p['date'], reverse=True)
        r = c = 0
        for p in posts:
            w = VideoThumbWidget(p) if p in video_posts else SlideThumbWidget(p)
            self.cells.append(w)
            self.grid.addWidget(w, r, c, alignment=Qt.AlignCenter)
            c += 1
            if c >= 3:
                c = 0
                r += 1

        scroll = QScrollArea()
        scroll.horizontalScrollBar().setEnabled(False)
        scroll.horizontalScrollBar().setVisible(False)
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        scroll.setWidget(cont)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(0,0,0,0)
        lay.addWidget(scroll)

    def resizeEvent(self, e):
        total_w = self.width()
        cell_w  = math.floor(total_w / 3)
        for w in self.cells:
            w.setThumbnailSize(cell_w)
        super().resizeEvent(e)

# ——— 11. Main window & dark mode ———
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Instagram-Style Dark Viewer")
        self.setWindowIcon(QIcon(resource_path("icon.ico")))
        central = QWidget()
        v = QVBoxLayout(central)
        v.setContentsMargins(0,0,0,0)
        v.addWidget(ProfileHeaderWidget())
        v.addWidget(PostsGridWidget())
        self.setCentralWidget(central)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyleSheet("""
        QWidget { background: #000; }
        QLabel  { color: #fff; font-family: Helvetica, Arial; }
        QPushButton {
            color: #fff; background: #262626; border:none;
            border-radius:4px; padding:4px 8px;
        }
        QPushButton:hover { background: #333; }
        QScrollArea, QFrame { background: #000; }
    """)
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec_())
