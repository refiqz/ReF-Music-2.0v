import discord
from discord.ext import commands
import os
import asyncio
import yt_dlp
from dotenv import load_dotenv
import urllib.parse, urllib.request, re

# تحميل الرمز من ملف .env
load_dotenv()
TOKEN = os.getenv('discord_token')

# إعداد النوايا (Intents)
intents = discord.Intents.default()
intents.message_content = True
client = commands.Bot(command_prefix="r", intents=intents)

# قوائم الانتظار والعملاء الصوتيين
queues = {}
voice_clients = {}

# إعداد خيارات YouTube و FFmpeg
youtube_base_url = 'https://www.youtube.com/'
youtube_results_url = youtube_base_url + 'results?'
youtube_watch_url = youtube_base_url + 'watch?v='

# تحسين خيارات yt-dlp
yt_dl_options = {
    "format": "bestaudio[ext=m4a]/bestaudio",  # اختيار تنسيقات صوتية محددة
    "noplaylist": True,  # تجنب تنزيل قوائم التشغيل
    "quiet": True,  # تقليل الرسائل غير الضرورية
    "no_warnings": True  # إخفاء التحذيرات
}
ytdl = yt_dlp.YoutubeDL(yt_dl_options)

ffmpeg_options = {
    'before_options':
    '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5',
    'options': '-vn'
}


# حدث بدء التشغيل
@client.event
async def on_ready():
    print(f'{client.user} D O N E - by ref')
    # تعيين حالة البوت إلى "Listening" مع النشاط "REF"
    await client.change_presence(activity=discord.Activity(
        type=discord.ActivityType.listening, name="REF"))


# تشغيل الأغنية التالية
async def play_next(ctx):
    if ctx.guild.id in queues and queues[ctx.guild.id]:
        link = queues[ctx.guild.id].pop(0)
        await play(ctx, link=link)
    else:
        await ctx.send("The queue is empty!")


# دالة تشغيل الأغنية
@client.command(name="p")
async def play(ctx, *, link):
    try:
        # التحقق من أن المستخدم في قناة صوتية
        if not ctx.author.voice:
            await ctx.send(
                "You need to be in a voice channel to use this command!")
            return

        # الانضمام إلى القناة الصوتية
        if ctx.guild.id not in voice_clients:
            voice_client = await ctx.author.voice.channel.connect()
            voice_clients[ctx.guild.id] = voice_client
            await ctx.send(f"Joined {ctx.author.voice.channel.name}!")
        else:
            voice_client = voice_clients[ctx.guild.id]

        # البحث عن الفيديو إذا لم يكن الرابط مباشرًا
        if youtube_base_url not in link:
            query_string = urllib.parse.urlencode({'search_query': link})
            content = urllib.request.urlopen(youtube_results_url +
                                             query_string)
            search_results = re.findall(r'/watch\?v=(.{11})',
                                        content.read().decode())
            link = youtube_watch_url + search_results[0]

        # تنزيل المعلومات الخاصة بالفيديو
        loop = asyncio.get_event_loop()
        data = await loop.run_in_executor(
            None, lambda: ytdl.extract_info(link, download=False))
        song = data['url']
        print(f"Playing audio from: {song}")

        # التحقق من أن الرابط صالح
        if not song:
            await ctx.send("Could not retrieve the audio stream.")
            return

        # تشغيل الصوت باستخدام البث المباشر
        player = discord.FFmpegOpusAudio(song, **ffmpeg_options)
        voice_client.play(player,
                          after=lambda e: asyncio.run_coroutine_threadsafe(
                              play_next(ctx), client.loop))

        await ctx.send(f"Now playing: {data['title']}")
    except Exception as e:
        print(f"Error: {e}")
        await ctx.send("An error occurred while trying to play the song.")


# أوامر إضافية (مثل pause, resume, stop, queue)
@client.command(name="pause")
async def pause(ctx):
    try:
        voice_clients[ctx.guild.id].pause()
    except Exception as e:
        print(e)


@client.command(name="resume")
async def resume(ctx):
    try:
        voice_clients[ctx.guild.id].resume()
    except Exception as e:
        print(e)


@client.command(name="s")
async def stop(ctx):
    try:
        voice_clients[ctx.guild.id].stop()
        await voice_clients[ctx.guild.id].disconnect()
        del voice_clients[ctx.guild.id]
    except Exception as e:
        print(e)


@client.command(name="queue")
async def queue(ctx, *, url):
    if ctx.guild.id not in queues:
        queues[ctx.guild.id] = []
    queues[ctx.guild.id].append(url)
    await ctx.send("Added to queue!")


# تشغيل البوت
client.run(TOKEN)
