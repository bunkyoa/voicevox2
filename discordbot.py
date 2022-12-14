import asyncio
from datetime import datetime

import discord
from discord.ext import commands
import os
import traceback
import re
# import emoji
import json
import psycopg2
import roma2kana

prefix = os.getenv('DISCORD_BOT_PREFIX', default='π¦')
token = os.environ['DISCORD_BOT_TOKEN']
voicevox_key = os.environ['VOICEVOX_KEY']
client = commands.Bot(command_prefix=prefix)
with open('emoji_ja.json', encoding='utf-8') as file:
    emoji_dataset = json.load(file)
database_url = os.environ.get('DATABASE_URL')

SQLpath = os.environ["DATABASE_URL"]
db = psycopg2.connect(SQLpath)  # sqlγ«ζ₯ηΆ
cur = db.cursor()  # γͺγγζδ½γγζγ«δ½Ώγγγ€

romaji2katakana, romaji2hiragana, kana2romaji = roma2kana.make_romaji_convertor()


@client.event
async def on_ready():
    presence = f'{prefix}hγ§γγ«γγεη§'
    await client.change_presence(activity=discord.Game(name=presence))
    print("Ready")


@client.event
async def on_guild_join(guild):
    presence = f'{prefix}hγ§γγ«γγεη§'
    await client.change_presence(activity=discord.Game(name=presence))


@client.event
async def on_guild_remove(guild):
    presence = f'{prefix}hγ§γγ«γγεη§'
    await client.change_presence(activity=discord.Game(name=presence))


@client.command()
async def join(ctx):
    if ctx.message.guild:
        if ctx.author.voice is None:
            await ctx.send('γγ€γΉγγ£γ³γγ«γ«ζ₯ηΆγγ¦γγεΌγ³εΊγγ¦γγ γγγ')
        else:
            if ctx.guild.voice_client:
                if ctx.author.voice.channel == ctx.guild.voice_client.channel:
                    await ctx.send('ζ₯ηΆζΈγΏγ§γγ')
                else:
                    await ctx.voice_client.disconnect()
                    await asyncio.sleep(0.5)
                    await ctx.author.voice.channel.connect()
            else:
                await ctx.author.voice.channel.connect()


@client.command()
async def leave(ctx):
    if ctx.message.guild:
        if ctx.voice_client is None:
            await ctx.send('γγ€γΉγγ£γ³γγ«γ«ζ₯ηΆγγ¦γγΎγγγ')
        else:
            await ctx.voice_client.disconnect()


@client.command(aliases=["da"])
async def dict_add(ctx, *args):
    if len(args) < 2:
        await ctx.send(f'γ{prefix}dict_add(da) εθͺ γγΏγγͺγγ§ε₯εγγ¦γγ γγγ')
    else:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                guild_id = ctx.guild.id
                word = args[0]
                kana = args[1]
                sql = 'INSERT INTO dictionary (guildId, word, kana) VALUES (%s,%s,%s) ON CONFLICT (guildId, word) DO UPDATE SET kana = EXCLUDED.kana'
                value = (guild_id, word, kana)
                cur.execute(sql, value)
                await ctx.send(f'θΎζΈη»ι²γγΎγγοΌ{word}β{kana}\n')


@client.command(aliases=["dr"])
async def dict_remove(ctx, arg):
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            guild_id = ctx.guild.id
            word = arg

            sql = 'SELECT * FROM dictionary WHERE guildId = %s and word = %s'
            value = (guild_id, word)
            cur.execute(sql, value)
            rows = cur.fetchall()

            if len(rows) == 0:
                await ctx.send(f'θΎζΈη»ι²γγγ¦γγΎγγοΌ{word}')
            else:
                sql = 'DELETE FROM dictionary WHERE guildId = %s and word = %s'
                cur.execute(sql, value)
                await ctx.send(f'θΎζΈει€γγΎγγοΌ{word}')


@client.command(aliases=["dc"])
async def dict_check(ctx):
    with psycopg2.connect(database_url) as conn:
        with conn.cursor() as cur:
            sql = 'SELECT * FROM dictionary WHERE guildId = %s'
            value = (ctx.guild.id,)
            cur.execute(sql, value)
            rows = cur.fetchall()
            text = 'θΎζΈδΈθ¦§\n'
            if len(rows) == 0:
                text += 'γͺγ'
            else:
                for row in rows:
                    text += f'{row[1]}β{row[2]}\n'
            await ctx.send(text)


@client.event
async def on_message(message):
    try:
        if message.guild.voice_client:
            if not message.author.bot and message.channel.id == 772438848444694529:
                if not message.content.startswith(prefix) and not message.content.startswith("!") and not message.content.startswith("https://gyazo.com/"):
                    text = message.content

                    # Replace dictionary
                    with psycopg2.connect(database_url) as conn:
                        with conn.cursor() as cur:
                            sql = 'SELECT * FROM dictionary WHERE guildId = %s'
                            value = (message.guild.id,)
                            cur.execute(sql, value)
                            rows = cur.fetchall()
                            for row in rows:
                                word = row[1]
                                kana = row[2]
                                text = text.replace(word, kana)

                    # Replace new line
                    text = text.replace('\n', 'γ')

                    # Replace mention to user
                    pattern = r'<@!?(\d+)>'
                    match = re.findall(pattern, text)
                    for user_id in match:
                        user = await client.fetch_user(user_id)
                        user_name = f'γ{user.name}γ'
                        text = re.sub(rf'<@!?{user_id}>', user_name, text)

                    # Replace mention to role
                    pattern = r'<@&(\d+)>'
                    match = re.findall(pattern, text)
                    for role_id in match:
                        role = message.guild.get_role(int(role_id))
                        role_name = f'γ{role.name}γ'
                        text = re.sub(f'<@&{role_id}>', role_name, text)

                    # Replace Unicode emoji
                    text = re.sub(r'[\U0000FE00-\U0000FE0F]', '', text)
                    text = re.sub(r'[\U0001F3FB-\U0001F3FF]', '', text)
                    # for char in text:
                    #     if char in emoji.UNICODE_EMOJI['en'] and char in emoji_dataset:
                    #         text = text.replace(char, emoji_dataset[char]['short_name'])

                    # Replace Discord emoji
                    pattern = r'<:([a-zA-Z0-9_]+):\d+>'
                    match = re.findall(pattern, text)
                    for emoji_name in match:
                        emoji_read_name = emoji_name.replace('_', ' ')
                        text = re.sub(rf'<:{emoji_name}:\d+>', f'γ{emoji_read_name}γ', text)

                    # Replace URL
                    pattern = r'https://tenor.com/view/[\w/:%#\$&\?\(\)~\.=\+\-]+'
                    text = re.sub(pattern, 'η»ε', text)
                    pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+(\.jpg|\.jpeg|\.gif|\.png|\.bmp)'
                    text = re.sub(pattern, 'γη»ε', text)
                    pattern = r'https?://[\w/:%#\$&\?\(\)~\.=\+\-]+'
                    text = re.sub(pattern, 'γγ¦γΌγ’γΌγ«γ¨γ«ηη₯', text)

                    # Replace spoiler
                    pattern = r'\|{2}.+?\|{2}'
                    text = re.sub(pattern, 'δΌγε­', text)

                    # Replace laughing expression
                    if text[-1:] == 'w' or text[-1:] == 'W' or text[-1:] == 'ο½' or text[-1:] == 'W':
                        while text[-2:-1] == 'w' or text[-2:-1] == 'W' or text[-2:-1] == 'ο½' or text[-2:-1] == 'W':
                            text = text[:-1]
                        text = text[:-1] + 'γγ―γ©'

                    # Add attachment presence
                    for attachment in message.attachments:
                        if attachment.filename.endswith((".jpg", ".jpeg", ".gif", ".png", ".bmp")):
                            text += 'γη»ε'
                        else:
                            text += 'γζ·»δ»γγ‘γ€γ«'

                    # Replace roma 2 kana when start string is "!"
                    text = romaji2hiragana(text)

                    with psycopg2.connect(database_url) as conn:
                        with conn.cursor() as cur:
                            sql = f'SELECT * FROM voice_setting WHERE discord_id = {message.author.id}'
                            cur.execute(sql)
                            result = cur.fetchone()
                            voicevox_speaker = result[1]

                    mp3url = f'https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1'
                    while message.guild.voice_client.is_playing():
                        await asyncio.sleep(0.5)
                    source = await discord.FFmpegOpusAudio.from_probe(mp3url)
                    message.guild.voice_client.play(source)
        await client.process_commands(message)
    except Exception as e:
        orig_error = getattr(e, "original", e)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        error_message = f'```{error_msg}```'
        ch = client.get_channel(628807266753183754)
        d = datetime.now()  # ηΎε¨ζε»γ?εεΎ
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
        embed.set_footer(text=f'channel:on_check_time_loop\ntime:{time}\nuser:None')
        await ch.send(embed=embed)


@client.event
async def on_voice_state_update(member, before, after):
    try:
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                sql = f'SELECT * FROM voice_setting WHERE discord_id = {member.id}'
                cur.execute(sql)
                result = cur.fetchone()
                voicevox_speaker = result[1]
        if before.channel is None:
            if member.id == client.user.id:
                presence = f'{prefix}γγ«γ | {len(client.voice_clients)}/{len(client.guilds)}γ΅γΌγγΌ'
                await client.change_presence(activity=discord.Game(name=presence))
            else:
                if member.guild.voice_client is None:
                    await asyncio.sleep(0.5)
                    await after.channel.connect()
                else:
                    if member.guild.voice_client.channel is after.channel:
                        text = member.name + 'γγγε₯ε?€γγΎγγ'
                        # Replace dictionary
                        with psycopg2.connect(database_url) as conn:
                            with conn.cursor() as cur:
                                sql = 'SELECT * FROM dictionary WHERE guildId = %s'
                                value = (member.guild.id,)
                                cur.execute(sql, value)
                                rows = cur.fetchall()
                                for row in rows:
                                    word = row[1]
                                    kana = row[2]
                                    text = text.replace(word, kana)
                        mp3url = f'https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1'
                        while member.guild.voice_client.is_playing():
                            await asyncio.sleep(0.5)
                        source = await discord.FFmpegOpusAudio.from_probe(mp3url)
                        member.guild.voice_client.play(source)
        elif after.channel is None:
            if member.id == client.user.id:
                presence = f'{prefix}γγ«γ | {len(client.voice_clients)}/{len(client.guilds)}γ΅γΌγγΌ'
                await client.change_presence(activity=discord.Game(name=presence))
            else:
                if member.guild.voice_client:
                    if member.guild.voice_client.channel is before.channel:
                        mem_check = member.guild.voice_client.channel.members
                        for i in mem_check:
                            if i.bot:
                                mem_check.pop(i)
                        if len(mem_check) <= 1:
                            await asyncio.sleep(0.5)
                            await member.guild.voice_client.disconnect()
                        else:
                            text = member.name + 'γγγιε?€γγΎγγ'
                            # Replace dictionary
                            with psycopg2.connect(database_url) as conn:
                                with conn.cursor() as cur:
                                    sql = 'SELECT * FROM dictionary WHERE guildId = %s'
                                    value = (member.guild.id,)
                                    cur.execute(sql, value)
                                    rows = cur.fetchall()
                                    for row in rows:
                                        word = row[1]
                                        kana = row[2]
                                        text = text.replace(word, kana)
                            mp3url = f'https://api.su-shiki.com/v2/voicevox/audio/?text={text}&key={voicevox_key}&speaker={voicevox_speaker}&intonationScale=1'
                            while member.guild.voice_client.is_playing():
                                await asyncio.sleep(0.5)
                            source = await discord.FFmpegOpusAudio.from_probe(mp3url)
                            member.guild.voice_client.play(source)
        elif before.channel != after.channel:
            if member.guild.voice_client:
                if member.guild.voice_client.channel is before.channel:
                    if len(member.guild.voice_client.channel.members) == 1 or member.voice.self_mute:
                        await asyncio.sleep(0.5)
                        await member.guild.voice_client.disconnect()
                        await asyncio.sleep(0.5)
                        await after.channel.connect()
    except Exception as e:
        orig_error = getattr(e, "original", e)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        error_message = f'```{error_msg}```'
        ch = client.get_channel(628807266753183754)
        d = datetime.now()  # ηΎε¨ζε»γ?εεΎ
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
        embed.set_footer(text=f'channel:on_check_time_loop\ntime:{time}\nuser:None')
        await ch.send(embed=embed)


@client.event
async def on_command_error(ctx, error):
    orig_error = getattr(error, 'original', error)
    error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
    if "CommandNotFound" in error_msg:
        pass
    else:
        await ctx.send(error_msg)


@client.command(aliases=["s"])
async def settings(ctx):
    try:
        def check(m):
            if m.author.bot:
                return
            return m.channel == ctx.channel and m.author == ctx.author

        def edit_embed(target_embed, title, description):
            embed = target_embed.embeds[0]
            embed.description = description
            embed.title = title
            return embed

        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                sql = f'SELECT * FROM voice_setting WHERE discord_id = {ctx.author.id}'
                cur.execute(sql)
                result = cur.fetchone()
                voicevox_speaker = result[1]
        show_embed_description = f"γγͺγγ?ηΎε¨γ?θ¨­ε?γ―γε£°ηͺε·{voicevox_speaker}γ§γγ\n\nδ»₯δΈγγε£°γηͺε·γ§ζε?γγ¦γγ γγγ\n\n" \
                                 f"0: εε½γγγ γγΎγγΎ\n\
                                    1: γγγ γγ γγΎγγΎ\n\
                                    2: εε½γγγ γγΌγγ«\n\
                                    3: γγγ γγ γγΌγγ«\n\
                                    4: εε½γγγ γ»γ―γ·γΌ\n\
                                    5: γγγ γγ γ»γ―γ·γΌ\n\
                                    6: εε½γγγ γγ³γγ³\n\
                                    7: γγγ γγ γγ³γγ³\n\
                                    8: ζ₯ζ₯ι¨γ€γγ γγΌγγ«\n\
                                    9: ζ³’ι³γͺγ γγΌγγ«\n\
                                    10: ι¨ζ΄γ―γ γγΌγγ«\n\
                                    11: ηιζ­¦ε? γγΌγγ«\n\
                                    12: η½δΈθε€ͺι γγΌγγ«\n\
                                    13: ιε±±ιΎζ γγΌγγ«\n\
                                    14: ε₯ι³΄γ²γΎγ γγΌγγ«"
        embed = discord.Embed(
            description=show_embed_description,
            color=0x61c1a9)
        show_embed = await ctx.send(embed=embed)
        user_select_input = await client.wait_for("message", check=check)
        user_select_input = str(user_select_input.content).lower()
        try:
            if 0 <= int(user_select_input) <= 14:
                pass
            else:
                await show_embed.edit(embed=edit_embed(show_embed, "Error", "0ο½14γ?ζ΄ζ°ε€γ§ε₯εγγ¦δΈγγγ"))
                return
        except:
            await show_embed.edit(embed=edit_embed(show_embed, "Error", "0ο½14γ?ζ΄ζ°ε€γ§ε₯εγγ¦δΈγγγ"))
            return
        with psycopg2.connect(database_url) as conn:
            with conn.cursor() as cur:
                sql = f'UPDATE voice_setting SET voice_setting = {int(user_select_input)} WHERE discord_id = {ctx.author.id}'
                cur.execute(sql)
        await show_embed.edit(embed=edit_embed(show_embed, "Success", f"ζ΄ζ°ε?δΊγ\nηΎε¨γ?ε£°θ¨­ε?: {user_select_input}\n\n\
                                                                        0: εε½γγγ γγΎγγΎ\n\
                                                                        1: γγγ γγ γγΎγγΎ\n\
                                                                        2: εε½γγγ γγΌγγ«\n\
                                                                        3: γγγ γγ γγΌγγ«\n\
                                                                        4: εε½γγγ γ»γ―γ·γΌ\n\
                                                                        5: γγγ γγ γ»γ―γ·γΌ\n\
                                                                        6: εε½γγγ γγ³γγ³\n\
                                                                        7: γγγ γγ γγ³γγ³\n\
                                                                        8: ζ₯ζ₯ι¨γ€γγ γγΌγγ«\n\
                                                                        9: ζ³’ι³γͺγ γγΌγγ«\n\
                                                                        10: ι¨ζ΄γ―γ γγΌγγ«\n\
                                                                        11: ηιζ­¦ε? γγΌγγ«\n\
                                                                        12: η½δΈθε€ͺι γγΌγγ«\n\
                                                                        13: ιε±±ιΎζ γγΌγγ«\n\
                                                                        14: ε₯ι³΄γ²γΎγ γγΌγγ«"))
    except Exception as e:
        orig_error = getattr(e, "original", e)
        error_msg = ''.join(traceback.TracebackException.from_exception(orig_error).format())
        error_message = f'```{error_msg}```'
        ch = client.get_channel(628807266753183754)
        d = datetime.now()  # ηΎε¨ζε»γ?εεΎ
        time = d.strftime("%Y/%m/%d %H:%M:%S")
        embed = discord.Embed(title='Error_log', description=error_message, color=0xf04747)
        embed.set_footer(text=f'channel:on_check_time_loop\ntime:{time}\nuser:None')
        await ch.send(embed=embed)


@client.command()
async def h(ctx):
    message = f'''βββ{client.user.name}γ?δ½ΏγζΉβββ
    {prefix}joinοΌγγ€γΉγγ£γ³γγ«γ«ζ₯ηΆγγΎγγ
    {prefix}leaveοΌγγ€γΉγγ£γ³γγ«γγεζ­γγΎγγ
    {prefix}dict_check(dc)οΌθΎζΈγ«η»ι²γγγ¦γγεθͺγη’ΊθͺγγΎγγ
    {prefix}dict_add(da) εθͺ γγΏγγͺοΌθΎζΈγ«[εθͺ]γ[γγΏγγͺ]γ¨γγ¦θΏ½ε γγΎγγ
    {prefix}dict_remove(dr) εθͺοΌθΎζΈγγ[εθͺ]γ?γγΏγγͺγει€γγΎγγ
    {prefix}settings(s) ε£°γ?η¨?ι‘γη»ι²γ§γγΎγγ'''
    await ctx.send(message)


client.run(token)
