import os
import random
import logging
from dotenv import load_dotenv
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaAnimation
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from favs import add_favorite, get_user_favorites
import hashlib

load_dotenv()
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GIPHY_KEY = os.getenv("GIPHY_API_KEY")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

CAPTIONS = [
    "Olha esse fofinho 😻",
    "Um GIF pra melhorar o dia",
    "obaa gato",
    "Chegou o envio oficial de fofura 💌",
    "Esse pediu carinho virtual",
    "purr",
    "Gatos conseguem girar as orelhas até 180° 👂",
    "Ronronar de gato pode ajudar humanos a relaxar 😽",
    "Gatos amassam pãozinho para marcar território!!",
    "O nariz do gato é super sensível — eles reconhecem você pelo cheiro 😺",
    "🫶"
]
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🐱 gatinho normal", callback_data="menu::normal")],
        [InlineKeyboardButton("🟪 gatinho pixel", callback_data="menu::pixel")],
        [InlineKeyboardButton("🎨 gatinho pintura", callback_data="menu::art")],
        [InlineKeyboardButton("🎮 gatinho jogo", callback_data="menu::game")],
        [InlineKeyboardButton("💫 gatinho anime", callback_data="menu::anime")],
        [InlineKeyboardButton("🎲 Surpreenda-me!", callback_data="menu::random")],
        [InlineKeyboardButton("✨ Ver mais estilos", callback_data="menu::more_styles")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Miau! Escolha seu gatinho preferido 😸👇",
        reply_markup=reply_markup
    )
# dicionário global para cache de GIFs por categoria
gif_cache = {}

def fetch_gif_url_cached(query="cat", limit=20):
    """Busca GIFs da API do GIPHY ou retorna do cache se já tiver carregado"""
    # se já temos GIFs no cache para essa query
    if query in gif_cache and gif_cache[query]:
        return gif_cache[query].pop(0)  # pega o próximo da lista

    # caso contrário, busca na API
    if not GIPHY_KEY:
        return None
    url = "https://api.giphy.com/v1/gifs/search"
    params = {"api_key": GIPHY_KEY, "q": query, "limit": limit, "rating": "pg-13", "lang": "pt"}
    try:
        r = requests.get(url, params=params, timeout=8)
        r.raise_for_status()
        data = r.json().get("data", [])
        if not data:
            return None

        # salva todas as URLs no cache
        urls = [item["images"]["original"]["url"] for item in data]
        random.shuffle(urls)
        gif_cache[query] = urls

        return gif_cache[query].pop(0)
    except Exception as e:
        logger.exception("Erro ao buscar GIF:")
        return None
async def send_cat_gif(update_or_query, context, query="cat"):
    gif_url = fetch_gif_url_cached(query=query)
    if not gif_url:
        msg = "Ops, a GIPHY está ocupada 😿 Tente novamente mais tarde."
        if hasattr(update_or_query, "callback_query") and update_or_query.callback_query:
            await update_or_query.callback_query.message.reply_text(msg)
        else:
            await update_or_query.message.reply_text(msg)
        return

    # gera id curto
    gif_id = hashlib.md5(gif_url.encode()).hexdigest()[:10]

    # salva mapeamento id -> url
    if "gif_map" not in context.user_data:
        context.user_data["gif_map"] = {}
    context.user_data["gif_map"][gif_id] = gif_url

    caption = random.choice(CAPTIONS) + " " + random.choice(["😺", "🐾", "💕", "✨"])

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Mais!", callback_data=f"more::{query}")],
        [InlineKeyboardButton("⭐ Favorito", callback_data=f"fav::{gif_id}")],
        [InlineKeyboardButton("⬅️ Voltar ao menu", callback_data="menu::start")],
    ])

    try:
        if hasattr(update_or_query, "callback_query") and update_or_query.callback_query:
            cq = update_or_query.callback_query
            await cq.answer()
            await cq.message.reply_animation(animation=gif_url, caption=caption, reply_markup=keyboard)
        else:
            await update_or_query.message.reply_animation(animation=gif_url, caption=caption, reply_markup=keyboard)
    except Exception:
        logger.exception("Erro enviando GIF")
        if hasattr(update_or_query, "message") and update_or_query.message:
            await update_or_query.message.reply_text("Ops, não consegui enviar o GIF agora 😿")

async def menu_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    action = cq.data.split("::", 1)[1]

    if action == "start":
        await cq.message.delete()
        await start(cq, context)
        return

    if action == "more_styles":
        extras = [
            ("🚀 gato astronauta", "astronaut cat"),
            ("💻 gato hacker", "hacker cat"),
            ("🗡️ gato samurai", "samurai cat"),
            ("🪄 gato mágico", "magic cat"),
            ("🌸 gato kawaii", "kawaii cat"),
            ("🌌 gato neon", "neon cat")
        ]
        keyboard = [[InlineKeyboardButton(name, callback_data=f"menu::extra::{query}")] for name, query in extras]
        keyboard.append([InlineKeyboardButton("⬅️ Voltar ao menu", callback_data="menu::start")])
        reply_markup = InlineKeyboardMarkup(keyboard)
        await cq.message.delete()
        await cq.message.reply_text("Escolha um estilo extra de gatinho:", reply_markup=reply_markup)
        return

    if action.startswith("extra::"):
        query = action.split("::", 1)[1]
        await send_cat_gif(update, context, query)
        return

    if action == "normal":
        return await send_cat_gif(update, context, "cute cat")
    if action == "pixel":
        return await send_cat_gif(update, context, "pixel cat")
    if action == "art":
        return await send_cat_gif(update, context, "painting cat")
    if action == "game":
        return await send_cat_gif(update, context, "8bit cat")
    if action == "anime":
        return await send_cat_gif(update, context, "anime cat")
    if action == "random":
        q = random.choice(["pixel cat", "painting cat", "cute cat", "8bit cat", "anime cat"])
        return await send_cat_gif(update, context, q)

async def callback_more(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query.data
    if query.startswith("more::"):
        q = query.split("::", 1)[1]
        await send_cat_gif(update, context, q)

async def cat_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = "cat"
    if context.args:
        query = " ".join(context.args)
    await send_cat_gif(update, context, query)

async def text_listener(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").lower()
    
    triggers_gif = ["gatinho", "gato", "cat", "kitty", "miado"]
    if any(t in text for t in triggers_gif):
        await send_cat_gif(update, context, "cute cat")
        return

    if "oi" in text or "olá" in text or "bom dia" in text:
        respostas = [
            "Miau! 😺 Que bom te ver!",
            "Oie! 🐾 Pronta para ver gatinhos?",
            "Oi! 😸 Vamos alegrar o dia com GIFs de gatinho?"
        ]
        await update.message.reply_text(random.choice(respostas))
        return

    if "triste" in text or "deprimida" in text or "cansada" in text:
        respostas = [
            "Não fique triste… olha esse gatinho fofo! 🐱💕",
            "Um abraço virtual e um GIF de gatinho para animar 😽",
            "Miau! 🐾 Aqui vai um pouco de fofura para você!"
        ]
        await update.message.reply_text(random.choice(respostas))
        await send_cat_gif(update, context, "cute cat")
        return

    if "obrigada" in text or "obrigado" in text:
        respostas = [
            "Miau 😸 De nada! Sempre pronto para mandar GIFs fofinhos!",
            "Gatinho feliz por ajudar 🐾",
            "Ronronando de alegria por você! 😽"
        ]
        await update.message.reply_text(random.choice(respostas))
        return
    
async def callback_favorite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    cq = update.callback_query
    await cq.answer()
    data = cq.data

    if data.startswith("fav::"):
        gif_id = data.split("::", 1)[1]

        # pega URL salva
        gif_url = context.user_data.get("gif_map", {}).get(gif_id)
        if not gif_url:
            await cq.message.reply_text("Não consegui salvar nos favoritos 😿")
            return

        user_id = cq.from_user.id
        add_favorite(user_id, gif_url)
        await cq.message.reply_text("💖 GIF adicionado aos seus favoritos!")

async def show_favorites(update: Update, context: ContextTypes.DEFAULT_TYPE):
    gifs = get_user_favorites(update.effective_user.id)
    if not gifs:
        await update.message.reply_text("Você ainda não tem favoritos 😿")
        return
    for url in gifs:
        await update.message.reply_animation(url)

def main():
    if not TELEGRAM_TOKEN:
        raise RuntimeError("Coloque o TELEGRAM_TOKEN no .env")

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("cat", cat_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_listener))
    app.add_handler(CallbackQueryHandler(menu_handler, pattern=r"^menu::"))
    app.add_handler(CallbackQueryHandler(callback_more, pattern=r"^more::"))
    app.add_handler(CallbackQueryHandler(callback_favorite, pattern=r"^fav::"))
    app.add_handler(CommandHandler("favoritos", show_favorites))

    print("Bot iniciado")
    app.run_polling()

if __name__ == "__main__":
    main()
