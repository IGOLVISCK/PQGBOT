import random
import discord
import yt_dlp # é uma biblioteca Python baseada no youtube-dl PARA TOCAR MUSICAS DO YOUTUBE
import asyncio
from discord.utils import get
from discord import app_commands
from discord.ext import commands, tasks

intents = discord.Intents.all() #ARMAZENA AS PERMISSOES QUE O BOT TERA NA VARIAVEL INTENTS
bot = commands.Bot(".", intents=intents)
intents.members = True # # Importante para acessar e modificar cargos de membros
intents.message_content = True

@bot.event
async def on_ready(): #Função sera iniciada quando o bot estiver pronto
    await bot.tree.sync() #PARA PODER USAR SLASH COMMANDS
    print("BOT INICIALIZADO COM SUCESSO") #resultado da função
    
#MENSAGEM DE BOAS-VINDAS
@bot.event
async def on_member_join(membro:discord.Member): 
     # Pegando o servidor (guild) onde o membro entrou
    guild = membro.guild

    # Procurando o canal pelo nome
    canal = discord.utils.get(guild.text_channels, name="bem-vindo")

    if canal:
        bemvindo_embed = discord.Embed()
        bemvindo_embed.title = "SEJA BEM-VINDO"
        bemvindo_embed.description = f"O usuário {membro.mention} entrou no servidor!"
        await canal.send(embed=bemvindo_embed)
    else:
        print("Canal não encontrado.")

#MENSAGEM DE ADEUS
@bot.event
async def on_member_remove(membro:discord.Member):
      # Pegando o servidor (guild) onde o membro entrou
    guild = membro.guild

    # Procurando o canal pelo nome
    canal = discord.utils.get(guild.text_channels, name="até-logo")

    if canal:
        bemvindo_embed = discord.Embed()
        bemvindo_embed.title = "ATÉ LOGO, ESPERO QUE VOLTE"
        bemvindo_embed.description = f"O usuário {membro.mention} deixou o servidor!"
        await canal.send(embed=bemvindo_embed)
    else:
        print("Canal não encontrado.")

#EMBEDS
@bot.command()
async def enviar_embed(ctx:commands.Context):
    minha_embed = discord.Embed()
    minha_embed.title = "TITULO DA EMBED"
    minha_embed.description = "DESCRIÇÃO DA EMBED"
    await ctx.reply(embed=minha_embed, ephemeral=True)

##########ADICIONANDO CARGOS##############
@bot.command()
@commands.has_permissions(manage_roles=True) #Exige que o autor do comando tenha permissão para dar cargos
async def darcargo(ctx, membro: discord.Member, *, nome_cargo):
    canal = get(ctx.guild.text_channels, name="administrativo")
    #PROCURA O CARGO COM O NOME FORNECIDO PELO USUÁRIO
    cargo = discord.utils.get(ctx.guild.roles, name = nome_cargo) #procurando um cargo no servidor(ctx.guild) que tenha o nome igual ao valor da variavel nome_cargo

    #Se o cargo não existir, envia uma mensagem de erro
    if not cargo:
        await canal.send(f"Cargo '{nome_cargo}' NÃO ENCONTRADO.")
        return
    
    try:
        #TENTA ADICIONAR O CARGO AO MEMBRO MENCIONADO
        await membro.add_roles(cargo)
        #CONFIRMA QUE O CARGO FOI ADICIONADO COM SUCESSO
        await canal.send(f"✅ O ADM {ctx.author.mention} DEU O CARGO **{nome_cargo}** PARA {membro.mention}.")

    except discord.Forbidden:
        #Se o bot não tiver permissão para add cargo (ou o cargo for maior que o dele)
        await ctx.send("❌ NÃO TENHO PERMISSÃO PARA ATRIBUIR O CARGO")

    except Exception as e:
        #se outro erro acontecer, mostra o erro
        await canal.send(f"❌ Ocorreu um erro: {e}")

#SE O USUÁRIO AO TIVER PERMISSAO PARA DAR CARGOS
@darcargo.error
async def dar_cargo_error(ctx, error):
    canal = get(ctx.guild.text_channels, name="administrativo")
    if isinstance(error, commands.MissingPermissions):
        await canal.send("❌ Você não tem permissão para usar este comando!")
    else:
        await canal.send(f"❌ Erro desconhecido: {error}")

##########REMOVENDO CARGOS##############
@bot.command()
@commands.has_permissions(manage_roles=True)
async def removecargo(ctx, membro: discord.Member, *, nome_cargo):
    canal = get(ctx.guild.text_channels, name="administrativo")
    cargo = discord.utils.get(ctx.guild.roles, name = nome_cargo)

    if not cargo:
        await canal.send(f"CARGO '{nome_cargo}' NÃO ENCONTRADO")
        return
    
    try:
        await membro.remove_roles(cargo)
        await canal.send(f"👎 O ADM {ctx.author.mention} RETIROU O CARGO **{nome_cargo} DE {membro.mention}")

    except discord.Forbidden:
        await canal.send("❌ NÃO TENHO PERMISSÃO PARA RETIRAR O CARGO")
    except Exception as e:
        await canal.send(f"❌ Ocorreu um erro: {e}")

@removecargo.error
async def remove_cargo_error(ctx, error):
    canal = get(ctx.guild.text_channels, name="administrativo")
    if isinstance(error, commands.MissingPermissions):
        await canal.send("❌ Você não tem permissão para usar este comando!")
    else:
        await canal.send(f"❌ Erro desconhecido: {error}")


#SLASH COMANDOS | COMANDOS DE BARRA
@bot.tree.command()
async def ola(interact:discord.Interaction):
    await interact.response.send_message(f"Olá, {interact.user.name}!", ephemeral=True) #EPHEMERAL FAZ COM QUE SOMENTE A PESSOA QUE CHAMOU O COMANDO CONSEGUE VER A RESPOSTA

@bot.tree.command()
async def flip(interact:discord.Interaction):
    flip_list = ['CARA', 'COROA']
    flip_sorteio = random.sample(flip_list, 1)[0] #[0] pega só o resultado
    await interact.response.send_message(f"🪙FLIP: {flip_sorteio}")

#COMANDO CLEAR
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, quantidade: int = 10):
    if quantidade > 100:
        await ctx.send('Voce só pode apagar até 100 mensagens por vez.')
        return

    await ctx.channel.purge(limit=quantidade+1) #+1 para apagar o proprio comando
    confirm = await ctx.send(f"✅ {quantidade} mensagens apagadas")
    await confirm.delete(delay=3)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("❌ Você não tem permissão para usar este comando!")

###############TOCANDO MUSICAS DO YOUTUBE#################
# --- Baixar áudio do YouTube ---
def get_audio_source(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': False,
        'noplaylist': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]

        audio_url = info['url']
        title = info.get('title', 'Música Desconhecida')

        source = discord.FFmpegPCMAudio(audio_url)
        return source, title


# --- Entrar no canal de voz ---
@bot.command()
async def entrar(ctx):
    canal = get(ctx.guild.text_channels, name="musicas")
    if ctx.author.voice:
        canal = ctx.author.voice.channel
        await canal.connect()
    else:
        await canal.send("Você precisa estar em um canal de voz.")

# --- Sair do canal de voz ---
@bot.command()
async def sair(ctx):
    canal = get(ctx.guild.text_channels, name="musicas")
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    else:
        await canal.send("❌ Não estou em nenhum canal.")

# --- Tocar música ---
@bot.command()
async def play(ctx, *, url):
    guild_id = ctx.guild.id
    canal = get(ctx.guild.text_channels, name="musicas")

    if not ctx.voice_client:
        if ctx.author.voice:
            await ctx.author.voice.channel.connect()
        else:
            return await canal.send("❌ Você precisa estar em um canal de voz.")

    # Inicializa a fila se ainda não existir
    if guild_id not in queues:
        queues[guild_id] = []

    # Adiciona à fila
    queues[guild_id].append(url)
    await canal.send(f"🎶 Música adicionada à fila: `{url}`")

    # Se não estiver tocando nada, inicia a reprodução
    if not ctx.voice_client.is_playing() and not ctx.voice_client.is_paused():
        await play_next(ctx)
# Fila de músicas por servidor
queues = {}

def get_audio_source(url):
    ydl_opts = {
        'format': 'bestaudio/best',
        'quiet': True,
        'extract_flat': False,
        'noplaylist': True,
        'default_search': 'ytsearch',
        'source_address': '0.0.0.0',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
    }

    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=False)
        if 'entries' in info:
            info = info['entries'][0]

        audio_url = info['url']
        title = info.get('title', 'Música Desconhecida')

        source = discord.FFmpegPCMAudio(audio_url)
        return source, title


async def play_next(ctx):
    guild_id = ctx.guild.id
    canal = get(ctx.guild.text_channels, name="musicas")

    if guild_id not in queues or not queues[guild_id]:
        await canal.send("A fila acabou. Saindo do canal.")
        await ctx.voice_client.disconnect()
        return

    url = queues[guild_id].pop(0)
    source, title = get_audio_source(url)

    def after_playing(error):
        fut = asyncio.run_coroutine_threadsafe(play_next(ctx), bot.loop)
        try:
            fut.result()
        except Exception as e:
            print(f"Erro ao tocar próxima música: {e}")

    ctx.voice_client.play(source, after=after_playing)
    await canal.send(f"▶️ Tocando agora: **{title}**")


#STOP PARA MUSICA
@bot.command()
async def stop(ctx):
    canal = get(ctx.guild.text_channels, name="musicas")
    guild_id = ctx.guild.id

    if ctx.voice_client:
        ctx.voice_client.stop()  # Para imediatamente
        queues[guild_id] = []  # Limpa a fila
        await canal.send("⏹️ Música parada e fila limpa.")
    else:
        await canal.send("Não estou tocando nada.")

#SKIP PULA MUSICA
@bot.command()
async def skip(ctx):
    canal = get(ctx.guild.text_channels, name="musicas")

    if ctx.voice_client and ctx.voice_client.is_playing():
        await canal.send("⏭️ Pulando música...")
        ctx.voice_client.stop()  # Isso aciona o after e chama play_next
    else:
        await canal.send("Nenhuma música está tocando no momento.")
############FIM DAS MUSICAS#############

#CRIANDO CARGOS
@bot.command()
@commands.has_permissions(manage_roles=True)  # Verifica se o usuário tem permissão
async def criarcargo(ctx, *, nome_do_cargo):
    canal = get(ctx.guild.text_channels, name="administrativo")
    guild = ctx.guild

    # Verifica se já existe um cargo com esse nome
    cargo_existente = discord.utils.get(guild.roles, name=nome_do_cargo)
    if cargo_existente:
        return await canal.send(f"⚠️ O cargo `{nome_do_cargo}` já existe!")

    try:
        novo_cargo = await guild.create_role(name=nome_do_cargo)
        await canal.send(f"✅ O ADM {ctx.author.mention} DCRIOU O CARGO {nome_do_cargo}")
    except discord.Forbidden:
        await canal.send("❌ Não tenho permissão para criar cargos.")
    except Exception as e:
        await canal.send(f"❌ Ocorreu um erro ao criar o cargo: `{e}`")
#DELETANDO CARGOS
@bot.command()
@commands.has_permissions(manage_roles=True)
async def apagarcargo(ctx, *, nome_do_cargo):
    canal = get(ctx.guild.text_channels, name="administrativo")
    guild = ctx.guild
    cargo = discord.utils.get(guild.roles, name=nome_do_cargo)

    if not cargo:
        return await canal.send(f"❌ O cargo `{nome_do_cargo}` não foi encontrado.")

    try:
        await cargo.delete()
        await canal.send(f"🗑️ O ADM {ctx.author.mention} DELETOU O CARGO {nome_do_cargo}")
    except discord.Forbidden:
        await canal.send("❌ Não tenho permissão para deletar esse cargo.")
    except Exception as e:
        await canal.send(f"❌ Erro ao deletar o cargo: `{e}`")

#BANINDO
@bot.command()
@commands.has_permissions(ban_members=True)
async def banir(ctx, membro: discord.Member, *, motivo=None):
    canal = get(ctx.guild.text_channels, name="administrativo")
    try:
        await membro.ban(reason=motivo)
        await canal.send(f"🔨 Usuário `{membro}` foi banido por {ctx.author.mention}. Motivo: `{motivo or 'Não especificado'}`")
    except discord.Forbidden:
        await canal.send("❌ Não tenho permissão para banir esse usuário.")
    except Exception as e:
        await canal.send(f"❌ Ocorreu um erro ao banir: `{e}`")

#TIRANDO BAN
@bot.command()
@commands.has_permissions(ban_members=True)
async def desbanir(ctx, *, usuario_nome_tag):
    canal = get(ctx.guild.text_channels, name="administrativo")
    if "#" not in usuario_nome_tag:
        return await canal.send("❌ Formato inválido. Use: `.desbanir Nome#1234`")

    partes = usuario_nome_tag.split("#")

    if len(partes) != 2:
        return await canal.send("❌ Formato incorreto. Use exatamente: `.desbanir Nome#1234`")

    nome, tag = partes

    banidos = await ctx.guild.bans()
    for ban in banidos:
        usuario = ban.user
        if usuario.name == nome and usuario.discriminator == tag:
            await ctx.guild.unban(usuario)
            return await canal.send(f"✅ Usuário `{usuario}` foi desbanido por {ctx.author.mention}o!")

    await canal.send("❌ Usuário não encontrado na lista de banidos.")

#EXPULSANDO
@bot.command()
@commands.has_permissions(kick_members=True)
async def expulsar(ctx, membro: discord.Member, *, motivo=None):
    canal = get(ctx.guild.text_channels, name="administrativo")
    try:
        await membro.kick(reason=motivo)
        await canal.send(f"👢 Usuário `{membro}` foi expulso por {ctx.author.mention}. Motivo: `{motivo or 'Não especificado'}`")
    except discord.Forbidden:
        await canal.send("❌ Não tenho permissão para expulsar esse usuário.")
    except Exception as e:
        await canal.send(f"❌ Ocorreu um erro ao expulsar: `{e}`")



#COMANDO CONFIGURAR, PARA CONFIGURAR OS CANAIS DE TEXTOS DO SERVIDOR
@bot.command()
@commands.has_permissions(manage_channels=True)
async def configurar(ctx):
    guild = ctx.guild

    # Permissões
    todos = guild.default_role
    admin_role = discord.utils.get(guild.roles, permissions=discord.Permissions(administrator=True))

    overwrites_admin = {
        todos: discord.PermissionOverwrite(view_channel=False),
        admin_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    overwrites_publico = {
        todos: discord.PermissionOverwrite(view_channel=True, send_messages=True)
    }

    overwrites_leitura_apenas = {
        todos: discord.PermissionOverwrite(view_channel=True, send_messages=False)
    }

    canais = [
        ("administrativo", overwrites_admin, "🔒 Canal privado para admins."),
        ("musicas", overwrites_publico, "🎵 Canal para comandos musicais."),
        ("bem-vindo", overwrites_leitura_apenas, "👋 Canal de boas-vindas."),
        ("até-logo", overwrites_leitura_apenas, "📤 Canal de despedidas.")
    ]

    for nome, perm, descricao in canais:
        existente = discord.utils.get(guild.text_channels, name=nome)
        if existente:
            await ctx.send(f"ℹ️ O canal `{nome}` já existe.")
        else:
            await guild.create_text_channel(name=nome, overwrites=perm)
            await ctx.send(f"✅ Canal `{nome}` criado. {descricao}")



bot.run("MTM5MTE1MzIzMTQxMjg1NDc4NA.GsYh1U.ECqJc4RshCKLlKX-uhp6lmFX2Hb4m2rHKTryfU")