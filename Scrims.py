import discord
from discord.ext import commands
import os
from Mensaje import menú  # Importar el comando 'menú' desde comandos.py

# Verifica si el token está presente
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    print("Error: El token no está definido en las variables de entorno.")
    exit()  # Detiene la ejecución si no hay token

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.reactions = True
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

# Comando principal que usa el comando importado
@bot.command(aliases=["menú"])
async def menu(ctx):
    try:
        await menú(ctx)  # Llamar al comando 'menú' desde comandos.py
    except Exception as e:
        await ctx.send(f"Error al ejecutar el comando menú: {e}")
        print(f"Error en el comando menú: {e}")

# Manejo de errores para comandos
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        await ctx.send("El comando no existe.")
    else:
        await ctx.send(f"Error al ejecutar el comando: {error}")
        print(f"Error: {error}")

# Iniciar el bot
try:
    bot.run(TOKEN)
except Exception as e:
    print(f"Error al iniciar el bot: {e}")