from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler
from telegram import ReplyKeyboardMarkup
import json
import os
from dotenv import load_dotenv

load_dotenv()

usuarios = {}


try:
    with open("dados.json", "r") as f:
        usuarios = json.load(f)
except:
    usuarios = {}


def salvar_dados():
    with open("dados.json", "w") as f:
        json.dump(usuarios, f)


def resetar_usuario(user_id):
    usuarios[user_id] = {"estado": "aguardando_salario", "salario": 0, "gastos": []}


def menu_principal():
    keyboard = [
        ["💸 Registrar gasto"],
        ["📊 Ver gastos"],
        ["📈 Resumo"],
        ["🔄 Resetar"],
    ]
    return ReplyKeyboardMarkup(keyboard, resize_keyboard=True)


async def start(update, context):
    user_id = str(update.message.chat_id)
    if user_id not in usuarios:
        usuarios[user_id] = {
            "salario": None,
            "gastos": [],
            "estado": "aguardando_salario",
        }
    await update.message.reply_text("Digite seu salário para começar.")


async def responder(update, context):
    user_id = str(update.message.chat_id)
    msg = update.message.text.lower()

    if user_id not in usuarios:
        usuarios[user_id] = {
            "salario": None,
            "gastos": [],
            "estado": "aguardando_salario",
        }

    user = usuarios[user_id]

    if user["estado"] == "confirmando_reset":
        if "sim" in msg:
            resetar_usuario(user_id)
            await update.message.reply_text(
                "Conta resetada. Digite seu salário novamente."
            )
        elif "não" in msg or "nao" in msg:
            user["estado"] = "menu"
            await update.message.reply_text(
                "Reset cancelado.", reply_markup=menu_principal()
            )
        salvar_dados()
        return

    if user["estado"] == "aguardando_salario":
        try:
            user["salario"] = float(msg)
            user["estado"] = "menu"
            await update.message.reply_text(
                f"Salário definido: R${user['salario']}", reply_markup=menu_principal()
            )
        except:
            await update.message.reply_text("Digite um número válido.")
        salvar_dados()
        return

    if user["estado"] == "esperando_valor":
        try:
            user["valor_temp"] = float(msg)
            user["estado"] = "esperando_categoria"
            await update.message.reply_text("Digite a categoria do gasto:")
        except:
            await update.message.reply_text("Digite um valor válido.")
        salvar_dados()
        return

    if user["estado"] == "esperando_categoria":
        categoria = msg
        user["gastos"].append({"valor": user["valor_temp"], "categoria": categoria})
        user["estado"] = "menu"
        del user["valor_temp"]
        await update.message.reply_text(
            "Gasto registrado com sucesso.", reply_markup=menu_principal()
        )
        salvar_dados()
        return

    if "resetar" in msg:
        user["estado"] = "confirmando_reset"
        keyboard = [["✅ Sim", "❌ Não"]]
        markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
        await update.message.reply_text(
            "Tem certeza que deseja resetar?", reply_markup=markup
        )
        salvar_dados()
        return

    if "registrar gasto" in msg:
        user["estado"] = "esperando_valor"
        await update.message.reply_text("Digite o valor do gasto:")
        salvar_dados()
        return

    elif "ver gastos" in msg:
        resposta = "Seus gastos:\n"
        for g in user["gastos"]:
            resposta += f"- {g['categoria']}: R${g['valor']}\n"
        await update.message.reply_text(resposta, reply_markup=menu_principal())

    elif "resumo" in msg:
        total = sum(g["valor"] for g in user["gastos"])
        saldo = (user["salario"] or 0) - total
        await update.message.reply_text(
            f"Resumo:\nTotal: R${total:.2f}\nSaldo: R${saldo:.2f}",
            reply_markup=menu_principal(),
        )
    else:
        await update.message.reply_text(
            "Use os botões abaixo:", reply_markup=menu_principal()
        )
    salvar_dados()


token_ambiente = os.getenv("TELEGRAM_TOKEN")
app = ApplicationBuilder().token(token_ambiente).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, responder))

if __name__ == "__main__":
    app.run_polling()
