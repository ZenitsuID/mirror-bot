import signal

from os import path as ospath, remove as osremove, execl as osexecl
from subprocess import run as srun
from psutil import disk_usage, cpu_percent, swap_memory, cpu_count, virtual_memory, net_io_counters, Process as psprocess
from time import time
from pyrogram import idle
from sys import executable
from telegram import ParseMode, InlineKeyboardMarkup
from telegram.ext import CommandHandler

from bot import bot, app, dispatcher, updater, botStartTime, IGNORE_PENDING_REQUESTS, PORT, alive, web, AUTHORIZED_CHATS, LOGGER, Interval, rss_session, a2c
from .helper.ext_utils.fs_utils import start_cleanup, clean_all, exit_clean_up
from .helper.telegram_helper.bot_commands import BotCommands
from .helper.telegram_helper.message_utils import sendMessage, sendMarkup, editMessage, sendLogFile
from .helper.ext_utils.telegraph_helper import telegraph
from .helper.ext_utils.bot_utils import get_readable_file_size, get_readable_time
from .helper.telegram_helper.filters import CustomFilters
from .helper.telegram_helper.button_build import ButtonMaker
from .modules import authorize, list, cancel_mirror, mirror_status, mirror, clone, watch, shell, eval, delete, speedtest, count, leech_settings, search, rss


def stats(update, context):
    currentTime = get_readable_time(time() - botStartTime)
    total, used, free, disk= disk_usage('/')
    total = get_readable_file_size(total)
    used = get_readable_file_size(used)
    free = get_readable_file_size(free)
    sent = get_readable_file_size(net_io_counters().bytes_sent)
    recv = get_readable_file_size(net_io_counters().bytes_recv)
    cpuUsage = cpu_percent(interval=0.5)
    p_core = cpu_count(logical=False)
    t_core = cpu_count(logical=True)
    swap = swap_memory()
    swap_p = swap.percent
    swap_t = get_readable_file_size(swap.total)
    swap_u = get_readable_file_size(swap.used)
    memory = virtual_memory()
    mem_p = memory.percent
    mem_t = get_readable_file_size(memory.total)
    mem_a = get_readable_file_size(memory.available)
    mem_u = get_readable_file_size(memory.used)
    stats = f'<b>Waktu Aktif Bot:</b> {currentTime}\n\n'\
            f'<b>Total Ruang Disk:</b> {total}\n'\
            f'<b>Digunakan:</b> {used} | <b>Free:</b> {free}\n\n'\
            f'<b>Mengunggah:</b> {sent}\n'\
            f'<b>Unduh:</b> {recv}\n\n'\
            f'<b>CPU:</b> {cpuUsage}%\n'\
            f'<b>RAM:</b> {mem_p}%\n'\
            f'<b>DISK:</b> {disk}%\n\n'\
            f'<b>Inti Fisik:</b> {p_core}\n'\
            f'<b>Jumlah Inti:</b> {t_core}\n\n'\
            f'<b>MENUKAR:</b> {swap_t} | <b>Used:</b> {swap_p}%\n'\
            f'<b>Jumlah Memori:</b> {mem_t}\n'\
            f'<b>Memori Gratis:</b> {mem_a}\n'\
            f'<b>Memori yang Digunakan:</b> {mem_u}\n'
    sendMessage(stats, context.bot, update)


def start(update, context):
    buttons = ButtonMaker()
    buttons.buildbutton("Repo", "https://www.github.com/Zenitsu-ID/mirror-bot")
    buttons.buildbutton("Report", "https://t.me/ZenitsuXD")
    reply_markup = InlineKeyboardMarkup(buttons.build_menu(2))
    if CustomFilters.authorized_user(update) or CustomFilters.authorized_chat(update):
        start_string = f'''
This bot can mirror all your links to Google Drive!
Type /{BotCommands.HelpCommand} to get a list of available commands
'''
        sendMarkup(start_string, context.bot, update, reply_markup)
    else:
        sendMarkup('Bukan pengguna yang sah, gunakan bot mirror Anda sendiri', context.bot, update, reply_markup)

def restart(update, context):
    restart_message = sendMessage("Memulai ulang...", context.bot, update)
    if Interval:
        Interval[0].cancel()
    alive.kill()
    procs = psprocess(web.pid)
    for proc in procs.children(recursive=True):
        proc.kill()
    procs.kill()
    clean_all()
    srun(["python3", "update.py"])
    a2cproc = psprocess(a2c.pid)
    for proc in a2cproc.children(recursive=True):
        proc.kill()
    a2cproc.kill()
    with open(".restartmsg", "w") as f:
        f.truncate(0)
        f.write(f"{restart_message.chat.id}\n{restart_message.message_id}\n")
    osexecl(executable, executable, "-m", "bot")


def ping(update, context):
    start_time = int(round(time() * 1000))
    reply = sendMessage("Starting Ping", context.bot, update)
    end_time = int(round(time() * 1000))
    editMessage(f'{end_time - start_time} ms', reply)


def log(update, context):
    sendLogFile(context.bot, update)


help_string_telegraph = f'''<br>
<b>/{BotCommands.HelpCommand}</b>: Untuk mendapatkan pesan ini
<br><br>
<b>/{BotCommands.MirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring ke Google Drive. Mengirim <b>/{BotCommands.MirrorCommand}</b> untuk bantuan lebih lanjut
<br><br>
<b>/{BotCommands.ZipMirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring dan unggah file/folder yang dikompres dengan ekstensi zip
<br><br>
<b>/{BotCommands.UnzipMirrorCommand}</b> [download_url][magnet_link]: Mulai mirroring dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun
<br><br>
<b>/{BotCommands.QbMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai mirroring menggunakan qBittorrent, Gunakan <b>/{BotCommands.QbMirrorCommand} s</b> to select files before downloading
<br><br>
<b>/{BotCommands.QbZipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai mirroring menggunakan qBittorrent dan unggah file/folder yang dikompres dengan ekstensi zip
<br><br>
<b>/{BotCommands.QbUnzipMirrorCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai mirroring menggunakan qBittorrent dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun
<br><br>
<b>/{BotCommands.LeechCommand}</b> [download_url][magnet_link]: Mulai leeching ke Telegram, Gunakan <b>/{BotCommands.LeechCommand} s</b> to select files before leeching
<br><br>
<b>/{BotCommands.ZipLeechCommand}</b> [download_url][magnet_link]: Mulai leeching ke Telegram dan unggah file/folder yang dikompres dengan ekstensi zip
<br><br>
<b>/{BotCommands.UnzipLeechCommand}</b> [download_url][magnet_link][torent_file]: Mulai leeching ke Telegram dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun
<br><br>
<b>/{BotCommands.QbLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai leeching ke Telegram menggunakan qBittorrent, Gunakan <b>/{BotCommands.QbLeechCommand} s</b> untuk memilih file sebelum leeching
<br><br>
<b>/{BotCommands.QbZipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai leeching ke Telegram menggunakan qBittorrent dan unggah file/folder yang dikompres dengan ekstensi zip
<br><br>
<b>/{BotCommands.QbUnzipLeechCommand}</b> [magnet_link][torrent_file][torrent_file_url]: Mulai leeching ke Telegram menggunakan qBittorrent dan unggah file/folder yang diekstrak dari ekstensi arsip apa pun
<br><br>
<b>/{BotCommands.CloneCommand}</b> [drive_url][gdtot_url]: Salin file/folder ke Google Drive
<br><br>
<b>/{BotCommands.CountCommand}</b> [drive_url][gdtot_url]: Hitung file/folder Google Drive
<br><br>
<b>/{BotCommands.DeleteCommand}</b> [drive_url]: Hapus file/folder dari Google Drive (Hanya Pemilik & Sudo)
<br><br>
<b>/{BotCommands.WatchCommand}</b> [tautan yang didukung yt-dlp]: Mirror yt-dlp supported link. Send <b>/{BotCommands.WatchCommand}</b> for more help
<br><br>
<b>/{BotCommands.ZipWatchCommand}</b> [tautan yang didukung yt-dlp]: Mirror tautan yang didukung yt-dlp sebagai zip
<br><br>
<b>/{BotCommands.LeechWatchCommand}</b> [tautan yang didukung yt-dlp]: Tautan yang didukung leech yt-dlp
<br><br>
<b>/{BotCommands.LeechZipWatchCommand}</b> [tautan yang didukung yt-dlp]: Tautan yang didukung leech yt-dlp sebagai zip
<br><br>
<b>/{BotCommands.LeechSetCommand}</b>: Pengaturan leech
<br><br>
<b>/{BotCommands.SetThumbCommand}</b>: Balas foto untuk mengaturnya sebagai Thumbnail
<br><br>
<b>/{BotCommands.RssListCommand}</b>: Daftar semua info feed rss berlangganan
<br><br>
<b>/{BotCommands.RssGetCommand}</b>: [Title] [Number](last N links): Ambil paksa N tautan terakhir
<br><br>
<b>/{BotCommands.RssSubCommand}</b>: [Title] [Tautan Rss] f: [filter]: Berlangganan umpan rss baru
<br><br>
<b>/{BotCommands.RssUnSubCommand}</b>: [Title]: Berhenti berlangganan umpan rss berdasarkan title
<br><br>
<b>/{BotCommands.RssUnSubAllCommand}</b>: Hapus semua langganan umpan rss
<br><br>
<b>/{BotCommands.CancelMirror}</b>: Balas pesan yang digunakan untuk mengunduh dan unduhan itu akan dibatalkan
<br><br>
<b>/{BotCommands.CancelAllCommand}</b>: Batalkan semua tugas pengunduhan
<br><br>
<b>/{BotCommands.ListCommand}</b> [query]: Cari di Google Drive
<br><br>
<b>/{BotCommands.SearchCommand}</b> [query]: Cari torrent dengan API
<br>situs: <code>rarbg, 1337x, yts, etzv, tgx, torlock, piratebay, nyaasi, ettv</code><br><br>
<b>/{BotCommands.StatusCommand}</b>: Menunjukkan status semua unduhan
<br><br>
<b>/{BotCommands.StatsCommand}</b>: Tampilkan Statistik mesin tempat bot dihosting
'''

help = telegraph.create_page(
        title='Bantuan Mirror-Bot',
        content=help_string_telegraph,
    )["path"]

help_string = f'''
/{BotCommands.PingCommand}: Periksa berapa lama waktu yang dibutuhkan untuk melakukan Ping Bot

/{BotCommands.AuthorizeCommand}: Otorisasi obrolan atau pengguna untuk menggunakan bot (Hanya dapat dipanggil oleh Pemilik & Sudo bot)

/{BotCommands.UnAuthorizeCommand}: Batalkan otorisasi obrolan atau pengguna untuk menggunakan bot (Hanya dapat dipanggil oleh Pemilik & Sudo bot)

/{BotCommands.AuthorizedUsersCommand}: Tampilkan pengguna resmi (Hanya Pemilik & Sudo)

/{BotCommands.AddSudoCommand}: Tambahkan pengguna Sudo (Hanya Pemilik)

/{BotCommands.RmSudoCommand}: Hapus pengguna Sudo (Hanya Pemilik)

/{BotCommands.RestartCommand}: Mulai ulang dan perbarui bot

/{BotCommands.LogCommand}: Dapatkan file log bot. Berguna untuk mendapatkan laporan kerusakan

/{BotCommands.SpeedCommand}: Periksa Kecepatan Internet Tuan Rumah

/{BotCommands.ShellCommand}: Jalankan perintah di Shell (Hanya Pemilik)

/{BotCommands.ExecHelpCommand}: Dapatkan bantuan untuk modul Pelaksana (Hanya Pemilik)
'''

def bot_help(update, context):
    button = ButtonMaker()
    button.buildbutton("Perintah lainnya", f"https://telegra.ph/{help}")
    reply_markup = InlineKeyboardMarkup(button.build_menu(1))
    sendMarkup(help_string, context.bot, update, reply_markup)

botcmds = [

        (f'{BotCommands.MirrorCommand}', 'Mirror'),
        (f'{BotCommands.ZipMirrorCommand}','Mirror dan unggah sebagai zip'),
        (f'{BotCommands.UnzipMirrorCommand}','Mirror dan ekstrak file'),
        (f'{BotCommands.QbMirrorCommand}','Mirror torrent menggunakan qBittorrent'),
        (f'{BotCommands.QbZipMirrorCommand}','Mirror torrent dan unggah sebagai zip menggunakan qb'),
        (f'{BotCommands.QbUnzipMirrorCommand}','Mirror torrent dan ekstrak file menggunakan qb'),
        (f'{BotCommands.WatchCommand}','Mirror tautan yang didukung yt-dlp'),
        (f'{BotCommands.ZipWatchCommand}','Mirror tautan yang didukung yt-dlp sebagai zip'),
        (f'{BotCommands.CloneCommand}','Salin file/folder ke Drive'),
        (f'{BotCommands.LeechCommand}','Leech'),
        (f'{BotCommands.ZipLeechCommand}','Leech dan mengunggah as zip'),
        (f'{BotCommands.UnzipLeechCommand}','Leech dan ekstrak file'),
        (f'{BotCommands.QbLeechCommand}','Leech torrent menggunakan qBittorrent'),
        (f'{BotCommands.QbZipLeechCommand}','Leech torrent dan unggah sebagai zip menggunakan qb'),
        (f'{BotCommands.QbUnzipLeechCommand}','Leech torrent dan ekstrak menggunakan qb'),
        (f'{BotCommands.LeechWatchCommand}','Tautan yang didukung leech yt-dlp'),
        (f'{BotCommands.LeechZipWatchCommand}','Tautan yang didukung leech yt-dlp sebagai zip'),
        (f'{BotCommands.CountCommand}','Menghitung file/folder Drive'),
        (f'{BotCommands.DeleteCommand}','Hapus file/folder dari Drive'),
        (f'{BotCommands.CancelMirror}','Membatalkan tugas'),
        (f'{BotCommands.CancelAllCommand}','Batalkan semua tugas pengunduhan'),
        (f'{BotCommands.ListCommand}','Cari di Drive'),
        (f'{BotCommands.LeechSetCommand}','Pengaturan leech'),
        (f'{BotCommands.SetThumbCommand}','Setel thumbnail'),
        (f'{BotCommands.StatusCommand}','Dapatkan pesan status mirror'),
        (f'{BotCommands.StatsCommand}','Statistik penggunaan bot'),
        (f'{BotCommands.PingCommand}','Ping botnya'),
        (f'{BotCommands.RestartCommand}','Mulai ulang bot'),
        (f'{BotCommands.LogCommand}','Dapatkan bot Log'),
        (f'{BotCommands.HelpCommand}','Dapatkan bantuan terperinci')
    ]

def main():
    # bot.set_my_commands(botcmds)
    start_cleanup()
    # Check if the bot is restarting
    if ospath.isfile(".restartmsg"):
        with open(".restartmsg") as f:
            chat_id, msg_id = map(int, f)
        bot.edit_message_text("Berhasil memulai kembali!", chat_id, msg_id)
        osremove(".restartmsg")

    start_handler = CommandHandler(BotCommands.StartCommand, start, run_async=True)
    ping_handler = CommandHandler(BotCommands.PingCommand, ping,
                                  filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    restart_handler = CommandHandler(BotCommands.RestartCommand, restart,
                                     filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    help_handler = CommandHandler(BotCommands.HelpCommand,
                                  bot_help, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    stats_handler = CommandHandler(BotCommands.StatsCommand,
                                   stats, filters=CustomFilters.authorized_chat | CustomFilters.authorized_user, run_async=True)
    log_handler = CommandHandler(BotCommands.LogCommand, log, filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(ping_handler)
    dispatcher.add_handler(restart_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(stats_handler)
    dispatcher.add_handler(log_handler)
    updater.start_polling(drop_pending_updates=IGNORE_PENDING_REQUESTS)
    LOGGER.info("Bot Sudah Aktif!")
    signal.signal(signal.SIGINT, exit_clean_up)
    if rss_session is not None:
        rss_session.start()

app.start()
main()
idle()
