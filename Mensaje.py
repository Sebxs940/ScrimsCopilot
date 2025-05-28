import discord
from discord.ext import commands
import asyncio
import aiohttp
import os
import yt_dlp  # Librería para descargar videos
import re  # Para buscar URLs en el mensaje

# Si necesitas acceder a funcionalidades de apuestas.py, puedes importarlo
# from apuestas import alguna_funcion_o_variable

# ID de los canales
channels = {
    "Reglas": 1376958975307812947,
    "Logs": 1376958976121372753,
    "Anuncios": 1376964056186880000,
    "Noticias": 1375478735108706405,
    "Configuración": 1371039870595633163,
    "Tickets": 1376965273201934346,
}

# Función para verificar roles permitidos
def user_has_allowed_role(ctx, allowed_roles):
    return any(role.id in allowed_roles for role in ctx.author.roles)

# Comando principal que despliega el menú de opciones
@commands.command(name="menú")
async def menú(ctx):
    # Definir los IDs de los roles permitidos
    allowed_roles = [
        1375317523133894668,  # Administradores
    ]

    # Verificar permisos del usuario
    if not user_has_allowed_role(ctx, allowed_roles):
        return await ctx.send("No tienes permisos para ejecutar este comando.")

    # Verificar si el comando se ejecuta en el canal de configuración
    if ctx.channel.id != channels["Configuración"]:
        return await ctx.send("Este comando solo puede usarse en el canal de configuración.")

    # Embed inicial para solicitar contenido
    embed = discord.Embed(
        title="Escribe un mensaje, adjunta un video o proporciona una URL",
        description=(
            "Puedes:\n"
            "1️⃣ Escribir un mensaje.\n"
            "2️⃣ Adjuntar un archivo de video.\n"
            "3️⃣ Proporcionar una URL de TikTok, YouTube, Pinterest u otros sitios compatibles."
        ),
        color=discord.Color.blue()
    )
    await ctx.send(embed=embed)

    # Esperar un mensaje o archivo del usuario
    def check(message):
        return message.author == ctx.author and message.channel.id == ctx.channel.id and (message.content or message.attachments)

    try:
        user_message = await ctx.bot.wait_for('message', check=check, timeout=120.0)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo de espera agotado.")

    attachment = user_message.attachments[0] if user_message.attachments else None
    downloaded_file = None
    video_url = None

    # Verificar si hay contenido en el mensaje y luego buscar URLs
    if user_message.content:
        url_pattern = r"(https?://[^\s]+)"
        urls = re.findall(url_pattern, user_message.content)
        video_url = urls[0] if urls else None

    # Ignorar enlaces de WhatsApp, Reddit y Discord y dejarlos como texto
    ignored_sites = ["chat.whatsapp.com", "reddit.com", "discord.gg", "discord.com"]
    if video_url and any(site in video_url for site in ignored_sites):
        # Si el enlace es de WhatsApp, Reddit o Discord, no lo intentamos descargar y lo tratamos como texto
        cleaned_message = re.sub(r"https?://[^\s]+", lambda match: match.group(0), user_message.content)
        video_url = None  # No se va a procesar este enlace como video
    else:
        # Validar si la URL es compatible para videos (YouTube, TikTok, Pinterest, etc.)
        if video_url:
            supported_sites = ["youtube.com", "tiktok.com", "vimeo.com", "pin.it"]
            if not any(site in video_url for site in supported_sites):
                return await ctx.send("⚠️ URL no compatible. Proporciona un enlace válido de YouTube, TikTok, Pinterest u otros sitios compatibles.")

            try:
                await ctx.send("🎥 Procesando la URL, por favor espera...")

                # Verificar si la URL es de Pinterest y redirigir si es necesario
                if "pinterest.com" in video_url:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(video_url) as resp:
                            if resp.status == 200:
                                redirect_url = str(resp.url)  # Conseguir la URL final luego de la redirección
                                video_url = redirect_url
                                await ctx.send(f"🔗 Redirigido a: {video_url}")
                            else:
                                return await ctx.send("⚠️ No se pudo obtener la URL de Pinterest.")
                
                ydl_opts = {
                    "outtmpl": "downloaded_video.%(ext)s",
                    "format": "mp4/best",
                }

                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    # Extraemos la información del video y descargamos
                    info = ydl.extract_info(video_url, download=True)
                    downloaded_file = ydl.prepare_filename(info)
            except yt_dlp.utils.DownloadError:
                return await ctx.send("⚠️ Error al descargar el video. La URL puede no ser compatible.")
            except Exception as e:
                return await ctx.send(f"⚠️ Ocurrió un error: {e}")

        # Eliminar las URLs del mensaje y limpiar el contenido
        cleaned_message = re.sub(r"https?://[^\s]+", "", user_message.content)

    # Resumen del contenido recibido
    embed = discord.Embed(
        title="Contenido recibido",
        description=(
            f"📄 Mensaje: {cleaned_message or 'Ninguno'}\n"
            f"📎 Archivo adjunto: {'Sí' if attachment else 'No'}\n"
            f"🔗 URL procesada: {'Sí' if video_url else 'No'}"
        ),
        color=discord.Color.green()
    )
    await ctx.send(embed=embed)

    # Solicitar el ID del canal para enviar el contenido
    embed_channel = discord.Embed(
        title="Escribe el ID del canal",
        description="Escribe el ID del canal donde deseas enviar el contenido recibido.",
        color=discord.Color.orange()
    )
    await ctx.send(embed=embed_channel)

    def check_channel(message):
        return message.author == ctx.author and message.content.isdigit()

    try:
        channel_id_message = await ctx.bot.wait_for('message', check=check_channel, timeout=120.0)
        channel_id = int(channel_id_message.content)
    except asyncio.TimeoutError:
        return await ctx.send("⏰ Tiempo de espera agotado.")

    # Verificar si el canal existe
    channel = ctx.bot.get_channel(channel_id)
    if channel is None:
        return await ctx.send("❌ El ID del canal no es válido o el canal no existe.")

    # Verificar permisos antes de enviar el contenido
    if not channel.permissions_for(ctx.guild.me).send_messages:
        return await ctx.send(f"❌ No tengo permisos para enviar mensajes en {channel.mention}.")

    # Verificar tamaño del archivo antes de enviarlo
    if downloaded_file and os.path.getsize(downloaded_file) > 8 * 1024 * 1024:  # Si el archivo excede 8 MB
        await ctx.send("⚠️ El archivo es demasiado grande para enviarlo. Considera subirlo a un servidor de archivos.")
        return

    # Enviar el contenido al canal especificado
    try:
        if downloaded_file:
            await channel.send(content=cleaned_message, file=discord.File(downloaded_file))
            os.remove(downloaded_file)  # Eliminar el archivo descargado
        elif attachment:
            async with aiohttp.ClientSession() as session:
                async with session.get(attachment.url) as resp:
                    if resp.status == 200:
                        file_data = await resp.read()
                        file_name = attachment.filename
                        await channel.send(
                            content=cleaned_message,
                            file=discord.File(fp=bytes(file_data), filename=file_name)
                        )
        else:
            await channel.send(cleaned_message)
    except discord.Forbidden:
        await ctx.send("❌ No tengo permisos para enviar mensajes en ese canal.")
    except discord.HTTPException as e:
        await ctx.send(f"⚠️ Ocurrió un error al enviar el contenido: {e}")

    # Registro en el canal de Logs
    logs_channel = ctx.bot.get_channel(channels["Logs"])
    if logs_channel:
        try:
            await logs_channel.send(
                f"📋 Comando !menú usado por {ctx.author.display_name} en {ctx.channel.name}. Contenido enviado a {channel.mention}."
            )
        except discord.HTTPException as e:
            print(f"Error al enviar logs: {e}")
    else:
        print("⚠️ Error: El canal de Logs no se pudo encontrar.")

# Agregar el comando al bot
def setup(bot):
    bot.add_command(menú)