import base64
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import os
import re
import json
import logging
from datetime import datetime, timedelta, timezone
from threading import Thread
from urllib.parse import urlparse
from dotenv import load_dotenv
from telegram.helpers import escape_markdown
load_dotenv()  # Loads variables from your local .env file

import requests
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.constants import ParseMode
from telegram.error import BadRequest
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    ContextTypes,
    filters,
)

from data_config import Theatres, Languages, Formats, TimePeriods

# ======================================================================
# LOGGING SETUP
# ======================================================================
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
log = logging.getLogger(__name__)

# ======================================================================
# CONFIGURATION
# ======================================================================
load_dotenv()  # Loads variables from your local .env file

BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

GITHUB_REPO_WATCHES = os.getenv("GITHUB_REPO_WATCHES")
GITHUB_TOKEN_WATCHES = os.getenv("GITHUB_TOKEN_WATCHES")
GITHUB_WATCHES_PATH = os.getenv("GITHUB_WATCHES_PATH")
GITHUB_WSTATE_PATH = os.getenv("GITHUB_WSTATE_PATH")
GITHUB_BRANCH_WATCHES = os.getenv("GITHUB_BRANCH_WATCHES")
GROUP_CHAT_ID_WATCHES = os.getenv("GROUP_CHAT_ID_WATCHES")


GITHUB_REPO_SHOWS = os.getenv("GITHUB_REPO_SHOWS")
GITHUB_TOKEN_SHOWS = os.getenv("GITHUB_TOKEN_SHOWS")
GITHUB_SHOWS_PATH = os.getenv("GITHUB_SHOWS_PATH")
GITHUB_SSTATE_PATH = os.getenv("GITHUB_SSTATE_PATH")
GITHUB_BRANCH_SHOWS = os.getenv("GITHUB_BRANCH_SHOWS")
GROUP_CHAT_ID_SHOWS = os.getenv("GROUP_CHAT_ID_SHOWS")

THEATRES_PER_PAGE = 6
WATCHES_PER_PAGE = 3  # 3 to 4 is ideal so full names fit comfortably on mobile

WATCHES_CACHE = None  # <--- ADD THIS
SHOWS_CACHE = None

# Conversation States
# Conversation States (Watches + Manual Shows)
# Conversation States (Watches + Manual Shows with Seat/Row Prefs)
(
    STATE_URL,
    STATE_LANGUAGE,
    STATE_FORMAT,
    STATE_THEATRE,
    STATE_DATE,
    STATE_CUSTOM_DATE,
    STATE_TIME,
    STATE_SHOW_NAME,
    STATE_SHOW_VENUE,
    STATE_SHOW_SESSION,
    STATE_SHOW_DATE,
    STATE_SHOW_TIME,
    STATE_SHOW_SEAT_COUNT,
    STATE_SHOW_ADJACENT,
    STATE_SHOW_ROWS,
STATE_SHOW_ROW_SEATS
) = range(16)


# Parse comma-separated IDs into sets of integers
def parse_id_list(env_var: str) -> set[int]:
    raw = os.getenv(env_var, "")
    return {int(x.strip()) for x in raw.split(",") if x.strip().isdigit()}

ALLOWED_USERS = parse_id_list("ALLOWED_USERS")

# ============================================================
# GITHUB JSON STORAGE
# ============================================================

GITHUB_API_BASE = "https://api.github.com"

def _github_headers(isWatch):
    token = GITHUB_TOKEN_WATCHES if isWatch else GITHUB_TOKEN_SHOWS
    return {
        "Authorization": f"Bearer {token}", 
        "Accept": "application/vnd.github+json", 
        "X-GitHub-Api-Version": "2022-11-28", 
        "User-Agent": "bms-telegram-bot"
    }

def _github_get_file(path, isWatch):
    repo = GITHUB_REPO_WATCHES if isWatch else GITHUB_REPO_SHOWS
    r = requests.get(f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}", headers=_github_headers(isWatch), timeout=20)
    if r.status_code == 404: 
        return None, None
    r.raise_for_status()
    payload = r.json()
    raw = base64.b64decode(payload["content"]).decode("utf-8")
    return json.loads(raw), payload.get("sha")


def _github_put_file(path, data, message, isWatch):
    repo = GITHUB_REPO_WATCHES if isWatch else GITHUB_REPO_SHOWS
    branch = GITHUB_BRANCH_WATCHES if isWatch else GITHUB_BRANCH_SHOWS
    url = f"{GITHUB_API_BASE}/repos/{repo}/contents/{path}"
    content = json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    
    for attempt in range(3):
        _, sha = _github_get_file(path, isWatch)
        body = {
            "message": message, 
            "content": base64.b64encode(content.encode()).decode(), 
            "branch": branch
        }
        if sha: 
            body["sha"] = sha
        r = requests.put(url, headers=_github_headers(isWatch), json=body, timeout=20)
        if r.status_code in (200, 201): 
            return
        if r.status_code == 409 and attempt < 2: 
            continue
        r.raise_for_status()
    raise RuntimeError(f"Could not update GitHub file: {path}")


def load_watches() -> list:
    global WATCHES_CACHE
    if WATCHES_CACHE is not None:
        return WATCHES_CACHE
    data, _ = _github_get_file(GITHUB_WATCHES_PATH, True)
    WATCHES_CACHE = data if isinstance(data, list) else []
    return WATCHES_CACHE

def save_watches(watches: list):
    global WATCHES_CACHE
    _github_put_file(GITHUB_WATCHES_PATH, watches, "Update BMS watches", True)
    WATCHES_CACHE = watches
    log.info("WATCHES SAVED TO GITHUB & CACHE UPDATED | count=%d", len(watches))


def load_shows() -> list:
    global SHOWS_CACHE
    if SHOWS_CACHE is not None:
        return SHOWS_CACHE
    data, _ = _github_get_file(GITHUB_SHOWS_PATH, False)
    SHOWS_CACHE = data if isinstance(data, list) else []
    return SHOWS_CACHE

def save_shows(shows: list):
    global SHOWS_CACHE
    _github_put_file(GITHUB_SHOWS_PATH, shows, "Update BMS shows", False)
    SHOWS_CACHE = shows


async def is_authorized(update: Update) -> bool:
    """Verifies if the incoming user ID is in ALLOWED_USERS."""
    user = update.effective_user
    if not user or user.id not in ALLOWED_USERS:
        user_id = user.id if user else "Unknown"
        user_name = user.full_name if user else "Unknown"
        
        log.warning(f"⛔ Unauthorized access attempt | ID: {user_id} ---> Name: {user_name}")

        # Optional: Send callback feedback to prevent Telegram UI freeze
        if update.callback_query:
            await update.callback_query.answer("⛔ Access Denied", show_alert=True)
            
        return False
    return True


def build_watches_view(watches: list, page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    if not watches:
        return "📭 No active watches found.", None

    total_pages = max(1, (len(watches) + WATCHES_PER_PAGE - 1) // WATCHES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))

    start_idx = page * WATCHES_PER_PAGE
    end_idx = start_idx + WATCHES_PER_PAGE
    page_watches = watches[start_idx:end_idx]

    # 1. Build the text display with full, unclipped names
    lines = [f"📋 *Active Watches* (Page {page + 1}/{total_pages}):\n"]
    keyboard = []

    for offset, w in enumerate(page_watches):
        global_idx = start_idx + offset
        display_num = global_idx + 1
        full_name = w.get("name", f"Watch_{global_idx}")

        # Full name displayed in the message bubble
        lines.append(f"*{display_num}.* `{full_name}`")

        # Compact numbered action buttons
        keyboard.append([
            InlineKeyboardButton(f"🔍 Inspect {display_num}", callback_data=f"insp_{global_idx}"),
            InlineKeyboardButton(f"❌ Stop {display_num}", callback_data=f"stop_{global_idx}")
        ])

    # 2. Add pagination navigation row if there are multiple pages
    if total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"wpage_{page - 1}"))
        
        nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
        
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"wpage_{page + 1}"))
            
        keyboard.append(nav_row)

    return "\n".join(lines), InlineKeyboardMarkup(keyboard)


def build_shows_view(shows: list, page: int = 0) -> tuple[str, InlineKeyboardMarkup]:
    if not shows:
        return "📭 No active shows found.", None
    total_pages = max(1, (len(shows) + WATCHES_PER_PAGE - 1) // WATCHES_PER_PAGE)
    page = max(0, min(page, total_pages - 1))
    start_idx = page * WATCHES_PER_PAGE
    page_shows = shows[start_idx:start_idx + WATCHES_PER_PAGE]

    lines = [f"📋 *Active Manual Shows* (Page {page + 1}/{total_pages}):\n"]
    keyboard = []
    for offset, s in enumerate(page_shows):
        global_idx = start_idx + offset
        display_num = global_idx + 1
        lines.append(f"*{display_num}.* `{s.get('name')}` | Venue: `{s.get('venue_code')}` | Session: `{s.get('session_id')}`")
        keyboard.append([
            InlineKeyboardButton(f"❌ Remove {display_num}", callback_data=f"delshow_{global_idx}")
        ])
    if total_pages > 1:
        nav_row = []
        if page > 0: nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"spage_{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1: nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"spage_{page + 1}"))
        keyboard.append(nav_row)
    return "\n".join(lines), InlineKeyboardMarkup(keyboard)

# RENDER HEALTH SERVER
# ============================================================

class HealthHandler(
    BaseHTTPRequestHandler
):

    def do_GET(self):

        if self.path in (
            "/",
            "/health",
        ):

            body = b"OK"

            self.send_response(200)

            self.send_header(
                "Content-Type",
                "text/plain",
            )

            self.send_header(
                "Content-Length",
                str(len(body)),
            )

            self.end_headers()

            self.wfile.write(body)

        else:

            self.send_response(404)
            self.end_headers()

    def log_message(
        self,
        format,
        *args,
    ):
        return


def start_health_server():
    """
    Render Web Services require the application to listen
    on the PORT supplied by Render.
    """

    port = int(
        os.getenv(
            "PORT",
            "10000",
        )
    )

    server = ThreadingHTTPServer(
        (
            "0.0.0.0",
            port,
        ),
        HealthHandler,
    )

    thread = Thread(
        target=server.serve_forever,
        daemon=True,
    )

    thread.start()

    log.info(
        "Health server listening on 0.0.0.0:%s",
        port,
    )



# ======================================================================
# HELPER FUNCTIONS
# ======================================================================


async def show_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_authorized(update): return ConversationHandler.END

    keyboard = [
        [InlineKeyboardButton("➕ Add Watches", callback_data="menu_new_watch")],
        [InlineKeyboardButton("📋 View Active Watches", callback_data="menu_list_watches")],
        [InlineKeyboardButton("➕ Add Shows", callback_data="menu_new_show")],
        [InlineKeyboardButton("📋 View Active Shows", callback_data="menu_list_shows")],
        [InlineKeyboardButton("ℹ️ Help", callback_data="menu_help")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    text = "🍿 *BMS Ticket Watcher Dashboard*\n\nSelect an option below:"

    if update.message:
        await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    elif update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)
    return ConversationHandler.END

async def handle_main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "menu_new_watch":
        await query.edit_message_text("🔗 *New Watch Setup*\n\nPlease paste the full *BookMyShow movie link*:", parse_mode=ParseMode.MARKDOWN)
        return STATE_URL
    elif query.data == "menu_list_watches":
        watches = load_watches()
        text, reply_markup = build_watches_view(watches, page=0)
        kb_list = list(reply_markup.inline_keyboard) if reply_markup and reply_markup.inline_keyboard else []
        kb_list.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb_list), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif query.data == "menu_new_show":
        await query.edit_message_text("🎬 *Add Manual Show*\n\nEnter a reference name for this show (e.g., `Leo - AGS Vivira`):", parse_mode=ParseMode.MARKDOWN)
        context.user_data["show"] = {}
        return STATE_SHOW_NAME
    elif query.data == "menu_list_shows":
        shows = load_shows()
        text, reply_markup = build_shows_view(shows, page=0)
        kb_list = list(reply_markup.inline_keyboard) if reply_markup and reply_markup.inline_keyboard else []
        kb_list.append([InlineKeyboardButton("🏠 Main Menu", callback_data="menu_main")])
        await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(kb_list), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif query.data == "menu_help":
        help_text = "ℹ️ *Instructions:*\nUse *Add Watches* for URL filters or *Add Shows* for direct manual session tracking."
        kb = [[InlineKeyboardButton("🏠 Back to Menu", callback_data="menu_main")]]
        await query.edit_message_text(help_text, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN)
        return ConversationHandler.END
    elif query.data == "menu_main":
        await show_main_menu(update, context)
        return ConversationHandler.END


# Manual Show Flow Handlers
async def receive_show_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["show"]["name"] = update.message.text.strip()
    await update.message.reply_text("Enter Venue Code (e.g., `INTO` or `RAKK`):", parse_mode=ParseMode.MARKDOWN)
    return STATE_SHOW_VENUE

async def receive_show_venue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["show"]["venue_code"] = update.message.text.strip().upper()
    await update.message.reply_text("Enter Session ID (e.g., `90164`):", parse_mode=ParseMode.MARKDOWN)
    return STATE_SHOW_SESSION

async def receive_show_session(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["show"]["session_id"] = update.message.text.strip()
    await update.message.reply_text("Enter Date in `YYYYMMDD` format (e.g., `20260915`):", parse_mode=ParseMode.MARKDOWN)
    return STATE_SHOW_DATE

async def receive_show_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["show"]["date"] = update.message.text.strip()
    await update.message.reply_text("Enter Show Time for user clarity (e.g., `10:00 AM`):", parse_mode=ParseMode.MARKDOWN)
    return STATE_SHOW_TIME

async def receive_show_time(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data["show"]["show_time"] = update.message.text.strip()
    await update.message.reply_text("How many seats do you need? (e.g., `2` or `4`):", parse_mode=ParseMode.MARKDOWN)
    return STATE_SHOW_SEAT_COUNT

async def receive_show_seat_count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        count = int(update.message.text.strip())
        if count <= 0: raise ValueError()
        context.user_data["show"]["seat_count"] = count
    except ValueError:
        await update.message.reply_text("⚠️ Please enter a valid positive number:")
        return STATE_SHOW_SEAT_COUNT

    kb = [
        [
            InlineKeyboardButton("✅ Yes (Strictly Adjacent)", callback_data="show_adj_yes"),
            InlineKeyboardButton("❌ No (Distributed OK)", callback_data="show_adj_no")
        ]
    ]
    await update.message.reply_text(
        "👥 *Adjacency Requirement*\n\nDo you require strictly adjacent/consecutive seats?",
        reply_markup=InlineKeyboardMarkup(kb),
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_SHOW_ADJACENT

async def receive_show_adjacency(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    context.user_data["show"]["require_adjacent"] = (query.data == "show_adj_yes")

    await query.edit_message_text(
        "🔤 *Preferred Rows*\n\nEnter preferred rows separated by commas (e.g., `H,I,J`) or type `ALL`:",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_SHOW_ROWS

async def receive_show_rows(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().upper()
    show = context.user_data["show"]
    
    if text == "ALL" or text == "ANY":
        show["row_preferences"] = {} # Empty means any row/seat is fine
        return await finalize_manual_show(update, context)
        
    rows = [r.strip() for r in text.split(",") if r.strip()]
    show["pending_rows"] = rows
    show["row_preferences"] = {}
    
    # Prompt for the first row's seats
    first_row = rows[0]
    await update.message.reply_text(
        f"🔢 *Preferred Seats for Row {first_row}*\n\n"
        "Enter preferred seat numbers separated by commas (e.g., `10,11,12`) or type `ANY`:",
        parse_mode=ParseMode.MARKDOWN
    )
    return STATE_SHOW_ROW_SEATS


async def receive_row_seats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip().upper()
    show = context.user_data["show"]
    
    pending_rows = show.get("pending_rows", [])
    current_row = pending_rows.pop(0)
    
    # Save preference for this row
    seats = [] if text in ("ANY", "ALL") else [s.strip() for s in text.split(",") if s.strip()]
    show["row_preferences"][current_row] = seats
    
    if pending_rows:
        # Ask for the next row
        next_row = pending_rows[0]
        await update.message.reply_text(
            f"🔢 *Preferred Seats for Row {next_row}*\n\n"
            "Enter preferred seat numbers separated by commas or type `ANY`:",
            parse_mode=ParseMode.MARKDOWN
        )
        return STATE_SHOW_ROW_SEATS
    else:
        # All rows configured, finalize save
        return await finalize_manual_show(update, context)

async def finalize_manual_show(update: Update, context: ContextTypes.DEFAULT_TYPE):
    show_entry = context.user_data["show"]

    raw_date = show_entry.get("date", "")
    try:
      formatted_date = datetime.strptime(raw_date, "%Y%m%d").strftime("%d%m%y")
    except ValueError:
      formatted_date = raw_date
    
    thread_id = None
    if GROUP_CHAT_ID_SHOWS:
        try:
            esc = lambda text: escape_markdown(str(text), version=2)
            topic_name = f"{show_entry.get('name', 'Show')}_{show_entry.get('venue_code', 'Venue')}_{formatted_date}|{show_entry.get('show_time', 'Time')}"[:128]
            topic = await context.bot.create_forum_topic(chat_id=GROUP_CHAT_ID_SHOWS, name=topic_name)
            thread_id = topic.message_thread_id
            
            if show_entry["row_preferences"]:
                prefs_summary = ", ".join([f"Row {r}: {s}" if s else f"Row {r}: ANY" for r, s in show_entry["row_preferences"].items()])
            else:
                prefs_summary = "ALL ROWS / ANY SEATS"

            adj_text = "Yes (Strictly Adjacent)" if show_entry.get("require_adjacent", True) else "No (Distributed OK)"

            summary = (
                "🎉 *Manual Show Configuration Summary*\n\n"
                f"🎬 *Name:* {esc(show_entry['name'])}\n"
                f"🏛️ *Venue Code:* {esc(show_entry['venue_code'])}\n"
                f"🆔 *Session ID:* {esc(show_entry['session_id'])}\n"
                f"📅 *Date:* {esc(show_entry['date'])}\n"
                f"⏰ *Time:* {esc(show_entry['show_time'])}\n"
                f"💺 *Seats Required:* {esc(show_entry['seat_count'])}\n"
                f"👥 *Strict Adjacent:* {esc(adj_text)}\n"
                f"📍 *Row Preferences:* {esc(prefs_summary)}\n\n"
                "🔔 _Automated alerts for this manual show will appear in this topic\\._"
            )
            topic_msg = await context.bot.send_message(
                chat_id=GROUP_CHAT_ID_SHOWS, message_thread_id=thread_id, text=summary, parse_mode=ParseMode.MARKDOWN_V2
            )
            await context.bot.pin_chat_message(chat_id=GROUP_CHAT_ID_SHOWS, message_id=topic_msg.message_id)
        except Exception as e:
            log.error(f"Failed to create show forum topic: {e}")

    show_entry["message_thread_id"] = thread_id
    
    shows = load_shows()
    shows.append(show_entry)
    save_shows(shows)

    await update.message.reply_text(
        f"✅ *Manual Show Added Successfully!*\n\n"
        f"Name: `{show_entry['name']}`\n"
        f"Venue: `{show_entry['venue_code']}`\n"
        f"Session ID: `{show_entry['session_id']}`\n"
        f"A dedicated topic has been created in the group.",
        parse_mode=ParseMode.MARKDOWN
    )
    context.user_data.clear()
    return ConversationHandler.END


    
def parse_bms_url(url: str) -> dict:
    path = urlparse(url).path.strip("/")
    parts = path.split("/")

    event_code = None
    region_slug = None
    movie_slug = ""

    for part in parts:
        if re.match(r"^ET\d{8,}$", part):
            event_code = part

    if "movies" in parts:
        idx = parts.index("movies")
        if idx + 1 < len(parts):
            region_slug = parts[idx + 1]
        if idx + 2 < len(parts):
            movie_slug = parts[idx + 2]

    if not event_code or not region_slug:
        raise ValueError("Invalid URL: missing event code (ET...) or city region.")

    movie_name = movie_slug.replace("-", " ").title() if movie_slug else "MovieWatch"
    movie_name=movie_name.replace(" ","")
    return {
        "event_code": event_code,
        "region_slug": region_slug.lower(),
        "movie_slug": movie_slug,
        "movie_name": movie_name,
    }


def get_next_10_dates() -> list[tuple[str, str]]:
    dates = []
    today = datetime.now()
    for i in range(10):
        target = today + timedelta(days=i)
        dates.append((target.strftime("%Y%m%d"), target.strftime("%a, %d %b")))
    return dates


async def safe_edit_reply_markup(query, reply_markup):
    try:
        await query.edit_message_reply_markup(reply_markup=reply_markup)
    except BadRequest as e:
        if "Message is not modified" not in str(e):
            raise


def build_multiselect_keyboard(
    options: list,
    selected: set,
    step_prefix: str,
    columns: int = 2,
    allow_custom_date: bool = False,
    page: int = 0,
    paginated: bool = False,
    require_selection: bool = False,
    exclude_any: bool = False,
) -> InlineKeyboardMarkup:
    keyboard = []
    row = []

    active_options = options
    total_pages = 1

    if paginated:
        total_pages = max(1, (len(options) + THEATRES_PER_PAGE - 1) // THEATRES_PER_PAGE)
        page = max(0, min(page, total_pages - 1))
        start_idx = page * THEATRES_PER_PAGE
        end_idx = start_idx + THEATRES_PER_PAGE
        active_options = options[start_idx:end_idx]

    for item in active_options:
        val = item[0] if isinstance(item, tuple) else item
        label = item[1] if isinstance(item, tuple) else item

        orig_idx = options.index(item)

        mark = "✅ " if val in selected else ""
        btn_text = f"{mark}{label}"
        row.append(InlineKeyboardButton(btn_text, callback_data=f"tgl_{orig_idx}"))

        if len(row) == columns:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    if paginated and total_pages > 1:
        nav_row = []
        if page > 0:
            nav_row.append(InlineKeyboardButton("⬅️ Prev", callback_data=f"page_{page - 1}"))
        nav_row.append(InlineKeyboardButton(f"📄 {page + 1}/{total_pages}", callback_data="noop"))
        if page < total_pages - 1:
            nav_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"page_{page + 1}"))
        keyboard.append(nav_row)

    ctrl_row = []
    
    if not exclude_any:
        ctrl_row.append(
            InlineKeyboardButton(
                "🌐 Any / All" if selected else "✅ Any / All",
                callback_data="tgl_ANY",
            )
        )

    ctrl_row.append(InlineKeyboardButton("⬅️ Back", callback_data=f"back_{step_prefix}"))

    if require_selection and not selected:
        ctrl_row.append(InlineKeyboardButton("⚠️ Select a date to proceed", callback_data="alert_no_selection"))
    else:
        ctrl_row.append(InlineKeyboardButton("Next ➡️", callback_data=f"next_{step_prefix}"))

    keyboard.append(ctrl_row)

    if allow_custom_date:
        keyboard.append([
            InlineKeyboardButton("➕ Add Custom Date (YYYYMMDD)", callback_data="add_custom_date")
        ])

    keyboard.append([
        InlineKeyboardButton("❌ Cancel", callback_data="cancel_watch")
    ])

    return InlineKeyboardMarkup(keyboard)


def append_to_watches_file(watch_entry: dict):
    watches = load_watches()
    watches.append(watch_entry)  # Append to array
    save_watches(watches)
    log.info("WATCH APPENDED TO GITHUB | total_count=%d", len(watches))


# ======================================================================
# CONVERSATION STEP HANDLERS
# ======================================================================

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"User {update.effective_user.id} requested the main menu.")
    await show_main_menu(update, context)
    return ConversationHandler.END


async def receive_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()
    log.info(f"Received URL input: {url}")

    try:
        parsed = parse_bms_url(url)
    except Exception as e:
        log.warning(f"Failed to parse URL '{url}': {e}")
        await update.message.reply_text(
            f"❌ *Could not parse URL:* {e}\n\nPlease send a valid BookMyShow event URL:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_URL

    context.user_data["watch"] = {
        "name": parsed["movie_name"],
        "url": url,
        "event_code": parsed["event_code"],
        "region_slug": parsed["region_slug"],
        "languages": set(),
        "formats": set(),
        "theatre": set(),
        "dates": set(),
        "time_period": set(),
    }

    options = Languages.get_all()
    context.user_data["current_options"] = options
    context.user_data["current_page"] = 0

    kb = build_multiselect_keyboard(
        options=options,
        selected=context.user_data["watch"]["languages"],
        step_prefix="language",
        columns=2,
    )

    await update.message.reply_text(
        f"🎬 *Movie:* {parsed['movie_name']}\n"
        f"📍 *City:* {parsed['region_slug'].title()}\n\n"
        "📌 *Step 1: Select Languages*\n"
        "_(Tap to toggle, select 'Any' to match all, then click Next)_",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    return STATE_LANGUAGE


async def handle_language_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    log.info(f"STATE_LANGUAGE callback data received: {data}")
    watch = context.user_data["watch"]
    options = context.user_data["current_options"]

    if data == "next_language":
        options = Formats.get_all()
        context.user_data["current_options"] = options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(
            options=options,
            selected=watch["formats"],
            step_prefix="format",
            columns=2,
        )
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n"
            "📌 *Step 2: Select Screen Formats*\n"
            "_(Tap to toggle, select 'Any' to match all, then click Next)_",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_FORMAT

    if data == "back_language":
        await query.edit_message_text("🚫 Setup restarted. Send a valid BookMyShow movie link:")
        return STATE_URL

    if data.startswith("page_"):
        context.user_data["current_page"] = int(data.split("_")[1])
    elif data == "tgl_ANY":
        watch["languages"].clear()
    elif data.startswith("tgl_"):
        idx = int(data.split("_")[1])
        item = options[idx]
        if item in watch["languages"]:
            watch["languages"].remove(item)
        else:
            watch["languages"].add(item)

    kb = build_multiselect_keyboard(
        options=options,
        selected=watch["languages"],
        step_prefix="language",
        columns=2,
        page=context.user_data.get("current_page", 0),
    )
    await safe_edit_reply_markup(query, reply_markup=kb)
    return STATE_LANGUAGE


async def handle_format_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    log.info(f"STATE_FORMAT callback data received: {data}")
    watch = context.user_data["watch"]
    options = context.user_data["current_options"]

    if data == "next_format":
        city_slug = watch["region_slug"]
        city_theatres = Theatres.get_by_city(city_slug) or Theatres.get_all()
        context.user_data["current_options"] = city_theatres
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(
            options=city_theatres,
            selected=watch["theatre"],
            step_prefix="theatre",
            columns=1,
            paginated=True,
        )
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n"
            f"📌 *Step 3: Select Theatres in {city_slug.title()}*\n"
            "_(Use pagination below to browse venues)_",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_THEATRE

    if data == "back_format":
        options = Languages.get_all()
        context.user_data["current_options"] = options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(options, watch["languages"], "language", 2)
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n📌 *Step 1: Select Languages*",
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
        return STATE_LANGUAGE

    if data.startswith("page_"):
        context.user_data["current_page"] = int(data.split("_")[1])
    elif data == "tgl_ANY":
        watch["formats"].clear()
    elif data.startswith("tgl_"):
        idx = int(data.split("_")[1])
        item = options[idx]
        if item in watch["formats"]:
            watch["formats"].remove(item)
        else:
            watch["formats"].add(item)

    kb = build_multiselect_keyboard(
        options=options,
        selected=watch["formats"],
        step_prefix="format",
        columns=2,
        page=context.user_data.get("current_page", 0),
    )
    await safe_edit_reply_markup(query, reply_markup=kb)
    return STATE_FORMAT


async def handle_theatre_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    log.info(f"STATE_THEATRE callback data received: {data}")
    watch = context.user_data["watch"]
    options = context.user_data["current_options"]

    if data == "next_theatre":
        date_options = get_next_10_dates()
        context.user_data["current_options"] = date_options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(
            options=date_options,
            selected=watch["dates"],
            step_prefix="date",
            columns=2,
            allow_custom_date=True,
            require_selection=True,
            exclude_any=True,
        )
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n"
            "📌 *Step 4: Select Dates (Required)*\n"
            "_(Choose at least one date or add a custom date)_",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_DATE

    if data == "back_theatre":
        options = Formats.get_all()
        context.user_data["current_options"] = options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(options, watch["formats"], "format", 2)
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n📌 *Step 2: Select Formats*",
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
        return STATE_FORMAT

    if data.startswith("page_"):
        context.user_data["current_page"] = int(data.split("_")[1])
    elif data == "tgl_ANY":
        watch["theatre"].clear()
    elif data.startswith("tgl_"):
        idx = int(data.split("_")[1])
        item = options[idx]
        if item in watch["theatre"]:
            watch["theatre"].remove(item)
        else:
            watch["theatre"].add(item)

    kb = build_multiselect_keyboard(
        options=options,
        selected=watch["theatre"],
        step_prefix="theatre",
        columns=1,
        page=context.user_data.get("current_page", 0),
        paginated=True,
    )
    await safe_edit_reply_markup(query, reply_markup=kb)
    return STATE_THEATRE


async def handle_date_toggle(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    data = query.data
    log.info(f"STATE_DATE callback data received: {data}")
    watch = context.user_data["watch"]
    options = context.user_data["current_options"]

    if data == "alert_no_selection":
        await query.answer("⚠️ Please select at least one date before proceeding!", show_alert=True)
        return STATE_DATE

    await query.answer()

    if data == "add_custom_date":
        await query.edit_message_text(
            "📅 *Enter Custom Date*\n\n"
            "Please send the date in `YYYYMMDD` format (e.g., `20260915`):",
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_CUSTOM_DATE

    if data == "next_date":
        if not watch["dates"]:
            await query.answer("⚠️ Please select at least one date!", show_alert=True)
            return STATE_DATE

        time_options = TimePeriods.get_all()
        context.user_data["current_options"] = time_options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(
            options=time_options,
            selected=watch["time_period"],
            step_prefix="time",
            columns=1,
        )
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n"
            "📌 *Step 5: Select Preferred Show Times*",
            reply_markup=kb,
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_TIME

    if data == "back_date":
        city_slug = watch["region_slug"]
        city_theatres = Theatres.get_by_city(city_slug) or Theatres.get_all()
        context.user_data["current_options"] = city_theatres
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(city_theatres, watch["theatre"], "theatre", 1, paginated=True)
        await query.edit_message_text(
            f"🎬 *{watch['name']}*\n\n📌 *Step 3: Select Theatres*",
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN
        )
        return STATE_THEATRE

    if data.startswith("page_"):
        context.user_data["current_page"] = int(data.split("_")[1])
    elif data.startswith("tgl_"):
        idx = int(data.split("_")[1])
        date_code = options[idx][0]
        if date_code in watch["dates"]:
            watch["dates"].remove(date_code)
        else:
            watch["dates"].add(date_code)

    kb = build_multiselect_keyboard(
        options=options,
        selected=watch["dates"],
        step_prefix="date",
        columns=2,
        allow_custom_date=True,
        page=context.user_data.get("current_page", 0),
        require_selection=True,
        exclude_any=True,
    )
    await safe_edit_reply_markup(query, reply_markup=kb)
    return STATE_DATE


async def receive_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    log.info(f"Custom date received: {text}")
    watch = context.user_data["watch"]

    if not re.match(r"^\d{8}$", text):
        await update.message.reply_text(
            "⚠️ Invalid format! Please enter an 8-digit date code like `20260920`:",
            parse_mode=ParseMode.MARKDOWN,
        )
        return STATE_CUSTOM_DATE

    watch["dates"].add(text)

    date_options = get_next_10_dates()
    context.user_data["current_options"] = date_options

    kb = build_multiselect_keyboard(
        options=date_options,
        selected=watch["dates"],
        step_prefix="date",
        columns=2,
        allow_custom_date=True,
        require_selection=True,
        exclude_any=True,
    )

    await update.message.reply_text(
        f"✅ Added date `{text}`.\nSelect more or tap Next:",
        reply_markup=kb,
        parse_mode=ParseMode.MARKDOWN,
    )
    return STATE_DATE

async def handle_time_toggle_and_save(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data
    log.info(f"STATE_TIME callback data received: {data}")
    watch = context.user_data["watch"]
    options = context.user_data["current_options"]

    # Define Indian Standard Time (IST: UTC+5:30)
    IST = timezone(timedelta(hours=5, minutes=30))
    current_time_str = datetime.now(IST).strftime("%Y%m%d%H%M%S")

    if data in ("save_watch", "next_time"):
        log.info("Saving watch entry to file and creating group topic...")
        watch_name = watch["name"] + "_" + current_time_str
        
        # 1. Prepare raw variables for the summary
        raw_langs = ", ".join(sorted(list(watch["languages"]))) or "ALL"
        raw_formats = ", ".join(sorted(list(watch["formats"]))) or "ALL"
        raw_dates = ", ".join(sorted(list(watch["dates"])))
        raw_times = ", ".join(sorted(list(watch["time_period"]))) or "ALL"
        theatre_count = len(watch["theatre"])
        raw_theatres = f"{theatre_count} selected" if theatre_count > 0 else "ALL"

        # 2. Escape variables for MARKDOWN_V2
        esc = lambda text: escape_markdown(str(text), version=2)

        summary = (
            "🎉 *Watch Configuration Summary*\n\n"
            f"🎬 *Movie:* {esc(watch_name)}\n"
            f"🌐 *Languages:* {esc(raw_langs)}\n"
            f"📦 *Formats:* {esc(raw_formats)}\n"
            f"🏛️ *Theatres:* {esc(raw_theatres)}\n"
            f"📅 *Dates:* {esc(raw_dates)}\n"
            f"⏰ *Times:* {esc(raw_times)}\n\n"
            "🔔 _Automated alerts for this watch will appear in this topic\\._"
        )

        # 3. Create a Forum Topic, send the summary, and pin it
        thread_id = None
        if GROUP_CHAT_ID_WATCHES:
            try:
                # Create the topic
                topic = await context.bot.create_forum_topic(
                    chat_id=GROUP_CHAT_ID_WATCHES, 
                    name=watch_name[:128] # Telegram limits topic names to 128 chars
                )
                thread_id = topic.message_thread_id
                
                # Send the summary directly into the new topic
                topic_msg = await context.bot.send_message(
                    chat_id=GROUP_CHAT_ID_WATCHES,
                    message_thread_id=thread_id,
                    text=summary,
                    parse_mode=ParseMode.MARKDOWN_V2
                )
                
                # Pin the summary message inside the topic
                await context.bot.pin_chat_message(
                    chat_id=GROUP_CHAT_ID_WATCHES,
                    message_id=topic_msg.message_id
                )
            except Exception as e:
                log.error(f"Failed to create topic or pin message: {e}")

        # 4. Save to GitHub with the thread_id
        new_watch_entry = {
            "name": watch_name,
            "url": watch["url"],
            "dates": sorted(list(watch["dates"])),
            "theatre": sorted(list(watch["theatre"])),
            "time_period": sorted(list(watch["time_period"])),
            "discover_variants": True,
            "languages": sorted(list(watch["languages"])),
            "formats": sorted(list(watch["formats"])),
            "message_thread_id": thread_id, 
        }

        append_to_watches_file(new_watch_entry)

        # 5. Confirm to the user in their current chat menu
        dm_confirmation = summary + f"\n\n✅ *Setup Complete\\!* A dedicated topic has been created in the group\\."
        await query.edit_message_text(dm_confirmation, parse_mode=ParseMode.MARKDOWN_V2)
        
        context.user_data.clear()
        return ConversationHandler.END

    if data == "back_time":
        date_options = get_next_10_dates()
        context.user_data["current_options"] = date_options
        context.user_data["current_page"] = 0
        kb = build_multiselect_keyboard(
            date_options, watch["dates"], "date", 2, 
            allow_custom_date=True, require_selection=True, exclude_any=True
        )
        escaped_watch_name = escape_markdown(watch['name'], version=2)
        await query.edit_message_text(
            f"🎬 *{escaped_watch_name}*\n\n📌 *Step 4: Select Dates*",
            reply_markup=kb, parse_mode=ParseMode.MARKDOWN_V2
        )
        return STATE_DATE

    if data == "tgl_ANY":
        watch["time_period"].clear()
    elif data.startswith("tgl_"):
        idx = int(data.split("_")[1])
        
        # Grab the raw option from the list
        raw_option = options[idx]
        
        # Extract JUST the string (e.g., "morning") if it's a tuple
        time_key = raw_option[0] if isinstance(raw_option, tuple) else raw_option
        
        if time_key in watch["time_period"]:
            watch["time_period"].remove(time_key)
        else:
            watch["time_period"].add(time_key)

    kb = build_multiselect_keyboard(
        options=options,
        selected=watch["time_period"],
        step_prefix="time",
        columns=2,
    )
    await safe_edit_reply_markup(query, reply_markup=kb)
    return STATE_TIME

async def cancel_watch(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info("Setup workflow cancelled.")
    context.user_data.clear()
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.edit_message_text("🚫 Setup canceled.")
    elif update.message:
        await update.message.reply_text("🚫 Setup canceled.")
    return ConversationHandler.END


# ======================================================================
# NEW STANDALONE COMMAND HANDLERS (/watches, /stop, /inspect)
# ======================================================================

async def list_watches_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    log.info(f"User {update.effective_user.id} requested paginated watch list.")
    watches = load_watches()

    text, reply_markup = build_watches_view(watches, page=0)
    await update.message.reply_text(
        text,
        reply_markup=reply_markup,
        parse_mode=ParseMode.MARKDOWN
    )

async def list_shows_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text, reply_markup = build_shows_view(load_shows(), page=0)
    await update.message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

async def handle_watch_actions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # --- ADD THIS SECURITY CHECK FIRST ---
    if not await is_authorized(update):
        return
    query = update.callback_query
    await query.answer()
    data = query.data
    watches = load_watches()

    # --- 1. HANDLE PAGE FLIP ---
    if data.startswith("wpage_"):
        page_num = int(data.split("_")[1])
        text, reply_markup = build_watches_view(watches, page=page_num)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

    # --- 2. INSPECT WATCH ---
    elif data.startswith("insp_"):
        idx = int(data.split("_")[1])
        if idx >= len(watches):
            await query.edit_message_text("⚠️ Watch not found. The list might have changed.")
            return

        matched = watches[idx]
        langs_str = ", ".join(matched.get("languages", [])) or "ALL"
        formats_str = ", ".join(matched.get("formats", [])) or "ALL"
        dates_str = ", ".join(matched.get("dates", []))
        times_str = ", ".join(matched.get("time_period", [])) or "ALL"
        theatres_str = f"{len(matched.get('theatre', []))} selected" if matched.get("theatre") else "ALL"

        details = (
            f"🔍 *Watch Details: {escape_markdown(matched.get('name', ''), version=2)}*\n\n"
            f"🔗 *URL:* {escape_markdown(matched.get('url', ''), version=2)}\n"
            f"🌐 *Languages:* {escape_markdown(langs_str, version=2)}\n"
            f"📦 *Formats:* {escape_markdown(formats_str, version=2)}\n"
            f"🏛️ *Theatres:* {escape_markdown(theatres_str, version=2)}\n"
            f"📅 *Dates:* {escape_markdown(dates_str, version=2)}\n"
            f"⏰ *Times:* {escape_markdown(times_str, version=2)}"
        )

        kb = [[InlineKeyboardButton("⬅️ Back to List", callback_data="back_to_list")]]
        await query.edit_message_text(details, reply_markup=InlineKeyboardMarkup(kb), parse_mode=ParseMode.MARKDOWN_V2)

    # --- 3. INTENT TO STOP ---
    elif data.startswith("stop_"):
        idx = int(data.split("_")[1])
        if idx >= len(watches):
            return

        exact_watch_name = watches[idx].get("name")
        kb = [
            [
                InlineKeyboardButton("✅ Yes, Stop It", callback_data=f"confirmstop_{idx}"),
                InlineKeyboardButton("❌ Cancel", callback_data="back_to_list")
            ]
        ]
        await query.edit_message_text(
            f"⚠️ *Are you sure you want to stop tracking:*\n`{escape_markdown(exact_watch_name, version=2)}`?",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    # --- 4. CONFIRM STOP ---
    elif data.startswith("confirmstop_"):
        idx = int(data.split("_")[1])
        if idx >= len(watches):
            return

        matched = watches[idx]
        exact_watch_name = matched.get("name")

        # Delete Topic
        thread_id = matched.get("message_thread_id")
        if thread_id and GROUP_CHAT_ID_WATCHES:
            try:
                await context.bot.delete_forum_topic(chat_id=GROUP_CHAT_ID_WATCHES, message_thread_id=thread_id)
            except Exception as e:
                log.error(f"Failed to delete forum topic: {e}")

        # Update GitHub Watches & Cache
        updated_watches = [w for i, w in enumerate(watches) if i != idx]
        save_watches(updated_watches)

        # Clear State Cache
        deleted_count = 0
        try:
            bms_state, sha = _github_get_file(GITHUB_WSTATE_PATH,True)
            if bms_state and isinstance(bms_state, dict):
                keys_to_delete = [k for k in bms_state.keys() if k.lower().startswith(exact_watch_name.lower())]
                if keys_to_delete:
                    for k in keys_to_delete:
                        del bms_state[k]
                    _github_put_file(GITHUB_WSTATE_PATH, bms_state, f"Cleared states for {exact_watch_name}",True)
                    deleted_count = len(keys_to_delete)
        except Exception as e:
            log.error(f"Failed to clear bms_state.json: {e}")

        kb = [[InlineKeyboardButton("⬅️ Back to List", callback_data="back_to_list")]]
        await query.edit_message_text(
            f"✅ *Successfully stopped watch\\!*\n"
            f"🗑️ Deleted Topic for: `{escape_markdown(exact_watch_name, version=2)}`\n"
            f"🧹 Cleared `{deleted_count}` state variant\\(s\\)\\.",
            reply_markup=InlineKeyboardMarkup(kb),
            parse_mode=ParseMode.MARKDOWN_V2
        )

    # --- 5. NAVIGATE BACK TO LIST ---
    elif data == "back_to_list":
        fresh_watches = load_watches()
        text, reply_markup = build_watches_view(fresh_watches, page=0)
        await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=ParseMode.MARKDOWN)

# ======================================================================
# BOT RUNNER
# ======================================================================
auth_filter = filters.User(user_id=list(ALLOWED_USERS)) if ALLOWED_USERS else filters.ALL
def main():
    if BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE" or not BOT_TOKEN:
        print("❌ Error: Set the TELEGRAM_BOT_TOKEN environment variable first.")
        return

    # --- ADD THESE TWO LINES ---
    print("📥 Pre-loading watches from GitHub into memory...")
    load_watches()

    app = ApplicationBuilder().token(BOT_TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[
CommandHandler("start", start_command, filters=auth_filter),
            CommandHandler("newwatch", start_command, filters=auth_filter),
            CallbackQueryHandler(handle_main_menu, pattern="^menu_new_watch$"), # NEW: Button entry point
            MessageHandler(filters.Regex(r"bookmyshow\.com"), receive_url),
        ],
        states={
            STATE_URL: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_url)
            ],
            STATE_LANGUAGE: [
                CallbackQueryHandler(cancel_watch, pattern="^cancel_watch$"),
                CallbackQueryHandler(handle_language_toggle),
            ],
            STATE_FORMAT: [
                CallbackQueryHandler(cancel_watch, pattern="^cancel_watch$"),
                CallbackQueryHandler(handle_format_toggle),
            ],
            STATE_THEATRE: [
                CallbackQueryHandler(cancel_watch, pattern="^cancel_watch$"),
                CallbackQueryHandler(handle_theatre_toggle),
            ],
            STATE_DATE: [
                CallbackQueryHandler(cancel_watch, pattern="^cancel_watch$"),
                CallbackQueryHandler(handle_date_toggle),
            ],
            STATE_CUSTOM_DATE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_custom_date)
            ],
            STATE_TIME: [
                CallbackQueryHandler(cancel_watch, pattern="^cancel_watch$"),
                CallbackQueryHandler(handle_time_toggle_and_save),
            ],

            STATE_SHOW_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_name)],
    STATE_SHOW_VENUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_venue)],
    STATE_SHOW_SESSION: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_session)],
    STATE_SHOW_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_date)],
    STATE_SHOW_TIME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_time)],
    STATE_SHOW_SEAT_COUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_seat_count)],
    STATE_SHOW_ADJACENT: [CallbackQueryHandler(receive_show_adjacency, pattern="^show_adj_")],
    STATE_SHOW_ROWS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_show_rows)],
    STATE_SHOW_ROW_SEATS: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_row_seats)],
        },
        fallbacks=[CommandHandler("cancel", cancel_watch,filters=auth_filter),
                   CallbackQueryHandler(handle_main_menu, pattern="^menu_main$") # Allow going back to menu
                   ],
        allow_reentry=True,  # <--- CRITICAL FIX: Allows /start or URL entry while in an active state
    )

    app.add_handler(conv_handler)
    app.add_handler(
        CallbackQueryHandler(
            handle_main_menu, 
            pattern="^menu_(list_watches|help|main)$"
        )
    )
    # Register the requested standalone handlers
    app.add_handler(CommandHandler("watches", list_watches_command,filters=auth_filter))
    app.add_handler(
    CallbackQueryHandler(
        handle_watch_actions, 
        pattern="^(wpage_|insp_|stop_|confirmstop_|back_to_list)"
    )
)

    print("🤖 Telegram Watch Builder Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    start_health_server()
    main()
