"""
Hormozi Chief Bot â Telegram
Agente com a consciÃªncia do @hormozi-chief do AiOS-CORE.
"""

import os
import logging
from pathlib import Path
from dotenv import load_dotenv
import anthropic
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.constants import ChatAction

# âââ Config ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
load_dotenv(dotenv_path=Path(__file__).parent / ".env", override=True)

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not ANTHROPIC_API_KEY or not TELEGRAM_BOT_TOKEN:
    raise ValueError("Configure ANTHROPIC_API_KEY e TELEGRAM_BOT_TOKEN no arquivo .env")

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

# âââ Anthropic client ââââââââââââââââââââââââââââââââââââââââââââââââââââââââââ
claude = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

# âââ System Prompt (Hormozi Chief) âââââââââââââââââââââââââââââââââââââââââââââ
SYSTEM_PROMPT = """VocÃª Ã© o HORMOZI CHIEF â orquestrador do Hormozi Squad do AiOS-CORE.

ACTIVATION-NOTICE: You are the Hormozi Chief â orchestrator of the Hormozi Squad. You do NOT execute tasks. You DIAGNOSE business problems, ROUTE them to the correct Hormozi specialist, and REVIEW their output. You think in Hormozi's frameworks: Value Equation, Grand Slam Offers, Core 4 Lead Gen, CLOSER framework. Every business problem maps to one of these domains.

## IDENTIDADE
- Nome: Hormozi Chief ð
- Papel: Diagnosticador de problemas de negÃ³cio e roteador de squads
- Estilo: Direto, sem enrolaÃ§Ã£o, diagnÃ³stico preciso. Fala no vocabulÃ¡rio de Hormozi.
- Idioma padrÃ£o: PortuguÃªs (Brasil) â responda SEMPRE em portuguÃªs

## FRAMEWORKS QUE VOCÃ DOMINA
- Value Equation: Dream Outcome Ã Perceived Likelihood Ã· Time Delay Ã Effort & Sacrifice
- Grand Slam Offer: Oferta tÃ£o boa que seria idiota dizer nÃ£o
- Core 4 Lead Gen: Warm/Cold Outreach, Paid Ads, Content (orgÃ¢nico)
- CLOSER Framework: Clarify, Label, Overview, Sell the Vacation, Explain Away, Reinforce
- $100M Offers e $100M Leads (Alex Hormozi)

## DIAGNÃSTICO
Quando alguÃ©m trouxer um problema, siga este protocolo:
1. Qual Ã© o PROBLEMA CENTRAL? (Ofertas, Leads, PrecificaÃ§Ã£o, Vendas, RetenÃ§Ã£o, Escala, Modelo)
2. Em qual estÃ¡gio estÃ¡ o negÃ³cio? (0-R$1M / R$1M-R$10M / R$10M+)
3. Qual framework Hormozi se aplica?
4. Qual especialista do squad deve ser acionado?

## ROTEAMENTO DO SQUAD (16 agentes)
- ð¯ Problema de OFERTA â @hormozi-offers (Grand Slam Offer)
- ð£ Problema de LEADS â @hormozi-leads ($100M Leads)
- ð° Problema de PRECIFICAÃÃO â @hormozi-pricing (Value Equation)
- ð¤ Problema de VENDAS â @hormozi-closer (CLOSER framework)
- ð± Problema de CONTEÃDO â @hormozi-content (Content Machine)
- ð¢ Problema de ANÃNCIOS â @hormozi-ads (Paid Ads)
- ð Problema de RETENÃÃO â @hormozi-retention (LTV / Churn)
- ð Problema de ESCALA â @hormozi-scale ($1Mâ$100M)
- ðï¸ Problema de MODELO â @hormozi-models (Business Model)
- ðª Problema de LANÃAMENTO â @hormozi-launch (Launch methodology)
- ð AUDITORIA â @hormozi-audit
- âï¸ COPY â @hormozi-copy
- ð WORKSHOP â @hormozi-workshop
- ð¡ HOOKS â @hormozi-hooks
- ð§© ADVISORIA â @hormozi-advisor

## REGRAS
- NUNCA execute tarefas â vocÃª DIAGNOSTICA e ROTEIA
- Sempre identifique em qual estÃ¡gio o negÃ³cio estÃ¡
- Seja direto e cortante â Hormozi nÃ£o enrola
- Toda resposta deve ter um diagnÃ³stico claro e prÃ³ximo passo
- Responda SEMPRE em portuguÃªs do Brasil
- Use emojis com moderaÃ§Ã£o para deixar mais visual

## COMANDOS DISPONÃVEIS
- /diagnostico â inicia um diagnÃ³stico do negÃ³cio
- /squad â mostra todos os 16 agentes do squad
- /equacao â aplica a Value Equation em uma oferta
- /reset â limpa o histÃ³rico da conversa

Quando o usuÃ¡rio se apresentar ou descrever o negÃ³cio, faÃ§a perguntas diretas para identificar o problema central. ApÃ³s o diagnÃ³stico, indique qual agente especialista do squad deve ser consultado e POR QUÃ.
"""

# âââ HistÃ³rico de conversas por usuÃ¡rio ââââââââââââââââââââââââââââââââââââââââ
# { user_id: [{"role": "user"|"assistant", "content": "..."}] }
conversation_history: dict[int, list[dict]] = {}

MAX_HISTORY = 20  # mÃ¡ximo de mensagens por usuÃ¡rio


def get_history(user_id: int) -> list[dict]:
    return conversation_history.get(user_id, [])


def add_to_history(user_id: int, role: str, content: str) -> None:
    if user_id not in conversation_history:
        conversation_history[user_id] = []
    conversation_history[user_id].append({"role": role, "content": content})
    # MantÃ©m sÃ³ as Ãºltimas MAX_HISTORY mensagens
    if len(conversation_history[user_id]) > MAX_HISTORY:
        conversation_history[user_id] = conversation_history[user_id][-MAX_HISTORY:]


def clear_history(user_id: int) -> None:
    conversation_history[user_id] = []


# âââ Chamada Ã  API do Claude ââââââââââââââââââââââââââââââââââââââââââââââââââââ
def ask_hormozi(user_id: int, user_message: str) -> str:
    add_to_history(user_id, "user", user_message)
    messages = get_history(user_id)

    try:
        response = claude.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=[
                {
                    "type": "text",
                    "text": SYSTEM_PROMPT,
                    "cache_control": {"type": "ephemeral"},  # cache do system prompt
                }
            ],
            messages=messages,
        )

        reply = response.content[0].text
        add_to_history(user_id, "assistant", reply)
        return reply

    except anthropic.RateLimitError:
        return "â ï¸ Muitas requisiÃ§Ãµes em pouco tempo. Aguarde 30 segundos e tente novamente."
    except anthropic.AuthenticationError:
        return "â Erro de autenticaÃ§Ã£o com a API. Verifique sua AMTTHOPIC_API_KEY."
    except Exception as e:
        logger.error(f"Erro na API: {e}")
        return "â Erro interno. Tente novamente em alguns instantes."


# âââ Handlers do Telegram ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    user_id = user.id
    clear_history(user_id)

    welcome = (
        f"ð *Hormozi Chief aqui.*\n\n"
        f"Sou o orquestrador do Hormozi Squad â 16 especialistas em escalar negÃ³cios "
        f"usando os frameworks de Alex Hormozi.\n\n"
        f"Meu trabalho Ã© *diagnosticar* seu problema de negÃ³cio e *rotear* para o especialista certo.\n\n"
        f"*Me conta:* qual Ã© o maior problema do seu negÃ³cio agora?"
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")


async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    clear_history(user_id)
    await update.message.reply_text(
        "ð HistÃ³rico limpo. ComeÃ§ando do zero.\n\nDe volta ao origem."
    )


async def diagnostico(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    prompt = (
        "Inicie um diagnÃ³stico estruturado do meu negÃ³cio. "
        "FaÃ§a as perguntas certas para identificar o problema central."
    )
    await update.message.chat.send_action(ChatAction.TYPING)
    reply = ask_hormozi(user_id, prompt)
    await update.message.reply_text(reply)


async def squad(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    roster = (
        "ð *HORMOZI SQUAD â 16 Especialistas*\n\n"
        "ð¯ `@hormozi-chief` â Orquestrador (vocÃª estÃ¡ aqui)\n"
        "ð¦ `@hormozi-offers` â Grand Slam Offers\n"
        "ð£ `@hormozi-leads` â 	100M Leads\n"
        "ð° `@hormozi-pricing` â PrecificaÃ§Ã£o por valor\n"
        "ð¤ `@hormozi-closer` â Framework CLOSER\n"
        "ð¢ `@hormozi-ads` â AnÃºncios pagos\n"
        "ð± `@hormozi-content` â MÃ¡quina de conteÃºdo\n"
        "ðª `@hormozi-hooks` â CriaÃ§Ã£o de hooks\n"
        "ð `@hormozi-launch` â EstratÃ©gia de lanÃ§amento\n"
        "ð `@hormozi-retention` â RetenÃ§Ã£o e LTV\n"
        "ð `@hormozi-scale` â Escalar de $1M a $100M+\n"
        "ðï¸ `@hormozi-models` â Modelagem de negÃ³cio\n"
        "ð `@hormozi-audit` â Auditoria de negÃ³cio\n"
        "âï¸ `@hormozi-copy` â Copy estilo Hormozi \n"
        "ð `@hormozi-workshop` â Design de workshops\n"
        "ð¡ `@hormozi-advisor` â Conselho estratÃ©gico\n\n"
        "_Me conta seu problema e eu roteio para o especialista certo._"
    )
    await update.message.reply_text(roster, parse_mode="Markdown")


async def equacao(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    prompt = (
        "Aplique a Value Equation de Hormozi na minha oferta atual. "
        "Me pergunte o que precisa saber para fazer a anÃ¡lise."
    )
    await update.message.chat.send_action(ChatAction.TYPING)
    reply = ask_hormozi(user_id, prompt)
    await update.message.reply_text(reply)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    user_text = update.message.text

    logger.info(f"[{user_id}] â {user_text[:80]}")

    # Mostra "digitando..."
    await update.message.chat.send_action(ChatAction.TYPING)

    reply = ask_hormozi(user_id, user_text)

    # Telegram tem limite de 4096 chars por mensagem
    if len(reply) > 4000:
        chunks = [reply[i:i+4000] for i in range(0, len(reply), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk)
    else:
        await update.message.reply_text(reply)


# âââ InicializaÃ§Ã£o do bot ââââââââââââââââââââââââââââââââââââââââââââââââââââââ
def main() -> None:
    logger.info("ð Hormozi Chief Bot iniciando...")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    # Comandos
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("diagnostico", diagnostico))
    app.add_handler(CommandHandler("squad", squad))
    app.add_handler(CommandHandler("equacao", equacao))

    # Mensagens de texto
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("â Bot rodando. Pressione Ctrl+C para parar.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
