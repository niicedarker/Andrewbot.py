import json
import os
import asyncio
import qrcode
import requests
from datetime import datetime
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from deep_translator import GoogleTranslator

TOKEN = "8523831073:AAGH2dQC0wo4fJJv9VcX1FcThdqQMU1hVcI"
NOTES_FILE = "notes.json"
WEATHER_API = "https://wttr.in/" # API météo gratuite, pas besoin de clé

translator = GoogleTranslator(source='auto', target='fr')

# Charger/sauvegarder les notes
def load_notes():
    if os.path.exists(NOTES_FILE):
        with open(NOTES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_notes(notes):
    with open(NOTES_FILE, "w", encoding="utf-8") as f:
        json.dump(notes, f, ensure_ascii=False, indent=2)

notes_db = load_notes()

# Commandes de base
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = (
        "Salut! Je suis ton bot perso 🔥\n\n"
        "**Notes :**\n"
        "/note <texte> - Sauvegarder\n"
        "/mesnotes - Voir notes\n"
        "/delnote <num> - Supprimer\n"
        "/recherchenote <mot> - Chercher\n"
        "/export - Exporter en.txt\n"
        "**Utilitaires :**\n"
        "/meteo <ville> - Météo\n"
        "/traduire <lang> <texte> - Traduire\n"
        "/qr <texte> - Générer QR code\n"
        "/calc <calcul> - Calculatrice\n"
        "/citation - Citation aléatoire\n\n"
        "**Rappels :**\n"
        "/rappel HH:MM message - Rappel simple\n"
        "/rappel JJ/MM HH:MM message - Rappel avec date"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Pong! Bot en ligne ✅")

# Notes
async def note(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Utilise : /note Mon texte à retenir")
        return

    note_text = " ".join(context.args)
    time_now = datetime.now().strftime("%d/%m %H:%M")

    if user_id not in notes_db:
        notes_db[user_id] = []

    notes_db[user_id].append({"text": note_text, "date": time_now})
    save_notes(notes_db)
    await update.message.reply_text(f"Note sauvegardée ✅\n\n**{note_text}**", parse_mode="Markdown")

async def mesnotes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_notes = notes_db.get(user_id, [])

    if not user_notes:
        await update.message.reply_text("Tu n'as aucune note.")
        return

    msg = "**Tes notes :**\n\n"
    for i, note in enumerate(user_notes, 1):
        msg += f"*{i}.* {note['text']} \n_ {note['date']}_\n\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def delnote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Utilise : /delnote 1")
        return
    try:
        index = int(context.args[0]) - 1
        user_notes = notes_db.get(user_id, [])
        if 0 <= index < len(user_notes):
            removed = user_notes.pop(index)
            save_notes(notes_db)
            await update.message.reply_text(f"Note supprimée : {removed['text']}")
        else:
            await update.message.reply_text("Numéro invalide.")
    except ValueError:
        await update.message.reply_text("Donne un numéro valide.")

async def recherchenote(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    if not context.args:
        await update.message.reply_text("Utilise : /recherchenote mot-clé")
        return

    keyword = " ".join(context.args).lower()
    user_notes = notes_db.get(user_id, [])
    results = [n for n in user_notes if keyword in n["text"].lower()]

    if not results:
        await update.message.reply_text("Aucun résultat.")
        return

    msg = f"**Résultats pour '{keyword}' :**\n\n"
    for n in results:
        msg += f"- {n['text']} _({n['date']})_\n"
    await update.message.reply_text(msg, parse_mode="Markdown")

async def export(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = str(update.effective_user.id)
    user_notes = notes_db.get(user_id, [])
    if not user_notes:
        await update.message.reply_text("Tu n'as aucune note à exporter.")
        return

    filename = f"notes_{user_id}.txt"
    with open(filename, "w", encoding="utf-8") as f:
        for i, n in enumerate(user_notes, 1):
            f.write(f"{i}. {n['text']} ({n['date']})\n")

    await update.message.reply_document(document=open(filename, "rb"))
    os.remove(filename)

# Utilitaires
async def meteo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilise : /meteo Paris")
        return
    ville = " ".join(context.args)
    try:
        r = requests.get(f"{WEATHER_API}{ville}?format=3")
        await update.message.reply_text(f"🌤️ Météo {ville} :\n{r.text}")
    except:
        await update.message.reply_text("Ville introuvable.")

async def traduire(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Utilise : /traduire en Hello world")
        return
    lang = context.args[0]
    texte = " ".join(context.args[1:])
    try:
        result = translator.translate(texte, dest=lang)
        await update.message.reply_text(f"**Original :** {texte}\n**Traduit :** {result.text}", parse_mode="Markdown")
    except:
        await update.message.reply_text("Erreur de traduction. Ex: /traduire en Bonjour")

async def qr(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilise : /qr Ton texte")
        return
    texte = " ".join(context.args)
    img = qrcode.make(texte)
    filename = "qr.png"
    img.save(filename)
    await update.message.reply_photo(photo=open(filename, "rb"))
    os.remove(filename)

async def calc(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Utilise : /calc 2+2*5")
        return
    try:
        expr = " ".join(context.args)
        result = eval(expr, {"__builtins__": None}, {})
        await update.message.reply_text(f"{expr} = {result}")
    except:
        await update.message.reply_text("Calcul invalide.")

async def citation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    citations = [
        "Le succès c'est d'aller d'échec en échec sans perdre son enthousiasme. - Churchill",
        "Ce que tu cherches te cherche aussi. - Rumi",
        "La discipline bat le talent quand le talent ne se discipline pas.",
        "Fais de chaque jour ton chef-d'œuvre."
    ]
    import random
    await update.message.reply_text(f"💡 {random.choice(citations)}")

async def anniv_secret(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Date cible : 19 juin 2026 00:00
    date_cible = datetime(2026, 6, 19, 0, 0)
    maintenant = datetime.now()
    
    if maintenant >= date_cible:
        await update.message.reply_text("🎉 Joyeux anniversaire à ta reine ! C'est aujourd'hui !")
        return
    
    diff = date_cible - maintenant
    jours = diff.days
    heures = diff.seconds // 3600
    minutes = (diff.seconds % 3600) // 60
    
    msg = (
        f"👑 Compte à rebours secret activé 👑\n\n"
        f"Anniv de ta reine : **19 juin 2026**\n\n"
        f"Il reste : **{jours} jours, {heures}h {minutes}min**\n\n"
        f"Chut... c'est entre nous 🤫"
    )
    await update.message.reply_text(msg, parse_mode="Markdown")

# Rappels
async def rappel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Utilise : /rappel 14:30 Message ou /rappel 25/12 14:30 Message")
        return

    chat_id = update.effective_chat.id
    try:
        if ":" in context.args[0] and "/" not in context.args[0]:
            time_str = context.args[0]
            message = " ".join(context.args[1:])
            hour, minute = map(int, time_str.split(":"))
            now = datetime.now()
            reminder_time = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
            if reminder_time < now:
                reminder_time = reminder_time.replace(day=now.day + 1)
        else:
            date_str = context.args[0]
            time_str = context.args[1]
            message = " ".join(context.args[2:])
            day, month = map(int, date_str.split("/"))
            hour, minute = map(int, time_str.split(":"))
            year = datetime.now().year
            reminder_time = datetime(year, month, day, hour, minute)

        delay = (reminder_time - datetime.now()).total_seconds()
        if delay < 0:
            await update.message.reply_text("Cette date est déjà passée.")
            return

        await update.message.reply_text(f"Ok, je te rappelle le {reminder_time.strftime('%d/%m %H:%M')} : {message} ⏰")

        async def send_reminder():
            await asyncio.sleep(delay)
            await context.bot.send_message(chat_id=chat_id, text=f"🔔 Rappel : {message}")

        asyncio.create_task(send_reminder())

    except Exception as e:
        await update.message.reply_text("Format invalide. Ex: /rappel 25/12 14:30 Noël")

# Main
if __name__ == "__main__":
    import nest_asyncio
    nest_asyncio.apply()

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(CommandHandler("note", note))
    app.add_handler(CommandHandler("mesnotes", mesnotes))
    app.add_handler(CommandHandler("delnote", delnote))
    app.add_handler(CommandHandler("recherchenote", recherchenote))
    app.add_handler(CommandHandler("export", export))
    app.add_handler(CommandHandler("meteo", meteo))
    app.add_handler(CommandHandler("traduire", traduire))
    app.add_handler(CommandHandler("qr", qr))
    app.add_handler(CommandHandler("reine", anniv_secret))
    app.add_handler(CommandHandler("calc", calc))
    app.add_handler(CommandHandler("citation", citation))
    app.add_handler(CommandHandler("rappel", rappel))

    print("Bot démarré...")
    app.run_polling()
