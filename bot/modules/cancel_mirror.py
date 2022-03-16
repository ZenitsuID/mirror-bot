from telegram import InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler
from time import sleep

from bot import download_dict, dispatcher, download_dict_lock, DOWNLOAD_DIR, QB_SEED
from bot.helper.ext_utils.fs_utils import clean_download
from bot.helper.telegram_helper.bot_commands import BotCommands
from bot.helper.telegram_helper.filters import CustomFilters
from bot.helper.telegram_helper.message_utils import sendMessage, sendMarkup
from bot.helper.ext_utils.bot_utils import getDownloadByGid, MirrorStatus, getAllDownload
from bot.helper.telegram_helper import button_build


def cancel_mirror(update, context):
    args = update.message.text.split(" ", maxsplit=1)
    mirror_message = None
    if len(args) > 1:
        gid = args[1]
        dl = getDownloadByGid(gid)
        if not dl:
            sendMessage(f"GID: <code>{gid}</code> Tidak ditemukan.", context.bot, update)
            return
        mirror_message = dl.message
    elif update.message.reply_to_message:
        mirror_message = update.message.reply_to_message
        with download_dict_lock:
            keys = list(download_dict.keys())
            try:
                dl = download_dict[mirror_message.message_id]
            except:
                pass
    if len(args) == 1 and (
        not mirror_message or mirror_message.message_id not in keys
    ):
        msg = f"Balas ke pesan aktif <code>/{BotCommands.MirrorCommand}</code> yang digunakan untuk memulai pengunduhan atau pengiriman <code>/{BotCommands.CancelMirror} GID</code> untuk membatalkannya!"
        sendMessage(msg, context.bot, update)
        return
    if dl.status() == MirrorStatus.STATUS_ARCHIVING:
        sendMessage("Pengarsipan Sedang Berlangsung, Anda Tidak Dapat Membatalkannya.", context.bot, update)
    elif dl.status() == MirrorStatus.STATUS_EXTRACTING:
        sendMessage("Ekstrak Sedang Berlangsung, Anda Tidak Dapat Membatalkannya.", context.bot, update)
    elif dl.status() == MirrorStatus.STATUS_SPLITTING:
        sendMessage("Split Sedang Berlangsung, Anda Tidak Dapat Membatalkannya.", context.bot, update)
    else:
        dl.download().cancel_download()

def cancel_all(status):
    gid = ''
    while True:
        dl = getAllDownload(status)
        if dl:
            if dl.gid() != gid:
                gid = dl.gid()
                dl.download().cancel_download()
                sleep(1)
        else:
            break

def cancell_all_buttons(update, context):
    buttons = button_build.ButtonMaker()
    buttons.sbutton("Mengunduh", "canall down")
    buttons.sbutton("Mengunggah", "canall up")
    if QB_SEED:
        buttons.sbutton("Seeding", "canall seed")
    buttons.sbutton("Cloning", "canall clone")
    buttons.sbutton("Semua", "canall all")
    button = InlineKeyboardMarkup(buttons.build_menu(2))
    sendMarkup('Pilih tugas untuk dibatalkan.', context.bot, update, button)

def cancel_all_update(update, context):
    query = update.callback_query
    user_id = query.from_user.id
    data = query.data
    data = data.split(" ")
    if CustomFilters._owner_query(user_id):
        query.answer()
        query.message.delete()
        cancel_all(data[1])
    else:
        query.answer(text="Anda tidak memiliki izin untuk menggunakan tombol ini!", show_alert=True)



cancel_mirror_handler = CommandHandler(BotCommands.CancelMirror, cancel_mirror,
                                       filters=(CustomFilters.authorized_chat | CustomFilters.authorized_user) & CustomFilters.mirror_owner_filter | CustomFilters.sudo_user, run_async=True)

cancel_all_handler = CommandHandler(BotCommands.CancelAllCommand, cancell_all_buttons,
                                    filters=CustomFilters.owner_filter | CustomFilters.sudo_user, run_async=True)

cancel_all_buttons_handler = CallbackQueryHandler(cancel_all_update, pattern="canall", run_async=True)

dispatcher.add_handler(cancel_all_handler)
dispatcher.add_handler(cancel_mirror_handler)
dispatcher.add_handler(cancel_all_buttons_handler)
