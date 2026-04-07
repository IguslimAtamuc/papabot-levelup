import discord
from discord.ext import commands
from discord import app_commands
import json
import os
from datetime import datetime

TOKEN = os.environ.get('BOT_TOKEN')

# ID-uri canalelor LEVEL UP
RAPORT_TASK_CHANNEL_ID = 1491125710725714010
RAPOARTE_STAFF_CHANNEL_ID = 1491126203826081812

PUNCTE_FILE = 'puncte.json'

def load_puncte():
    if not os.path.exists(PUNCTE_FILE):
        return {}
    with open(PUNCTE_FILE, 'r') as f:
        return json.load(f)

def save_puncte(data):
    with open(PUNCTE_FILE, 'w') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def get_grad(puncte):
    if puncte >= 500:
        return '🌟 Legendar'
    elif puncte >= 300:
        return '💎 Conte'
    elif puncte >= 210:
        return '🏰 Baron'
    elif puncte >= 140:
        return '⚔️ Cavaler'
    elif puncte >= 70:
        return '👑 Nobil'
    else:
        return '⚪ Neutru'

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} este online!')
    try:
        synced = await bot.tree.sync()
        print(f'✅ Sincronizat {len(synced)} comenzi slash.')
    except Exception as e:
        print(f'Eroare: {e}')

@bot.event
async def on_message(message):
    if message.author.bot:
        return
    if message.channel.id == RAPORT_TASK_CHANNEL_ID:
        member = message.author
        now = datetime.now()
        data_ora = now.strftime('%d %B %Y — %H:%M')
        puncte_data = load_puncte()
        user_id = str(member.id)
        if user_id not in puncte_data:
            puncte_data[user_id] = {'nume': member.display_name, 'puncte': 0, 'taskuri_total': 0, 'ultima_activitate': ''}
        puncte_data[user_id]['puncte'] += 10
        puncte_data[user_id]['taskuri_total'] += 1
        puncte_data[user_id]['ultima_activitate'] = now.strftime('%Y-%m-%d %H:%M')
        puncte_data[user_id]['nume'] = member.display_name
        save_puncte(puncte_data)
        puncte_curente = puncte_data[user_id]['puncte']
        grad_curent = get_grad(puncte_curente)
        await message.add_reaction('✅')
        staff_channel = bot.get_channel(RAPOARTE_STAFF_CHANNEL_ID)
        if staff_channel:
            embed = discord.Embed(title='📋 TASK NOU RAPORTAT', color=discord.Color.green())
            embed.add_field(name='👤 Membru', value=f'{member.mention} ({member.display_name})', inline=True)
            embed.add_field(name='📅 Data & Ora', value=data_ora, inline=True)
            embed.add_field(name='💎 Puncte', value=f'**{puncte_curente}** puncte', inline=True)
            embed.add_field(name='🏆 Grad', value=grad_curent, inline=True)
            embed.add_field(name='📊 Total Taskuri', value=str(puncte_data[user_id]['taskuri_total']), inline=True)
            embed.add_field(name='🔗 Mesaj', value=f'[Click aici]({message.jump_url})', inline=True)
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.set_footer(text='PAPAbot — LEVEL UP Task Tracker')
            embed.timestamp = now
            await staff_channel.send(embed=embed)
        confirm = discord.Embed(title='✅ Raport inregistrat!', description=f'Ai primit **+10 puncte**!\n\n💎 **Total: {puncte_curente} puncte** → {grad_curent}', color=discord.Color.green())
        confirm.set_footer(text='Staff-ul va verifica in 24h')
        await message.reply(embed=confirm, delete_after=30)
    await bot.process_commands(message)

@bot.tree.command(name='puncte', description='Vezi cate puncte ai')
async def puncte_cmd(interaction: discord.Interaction, membru: discord.Member = None):
    target = membru or interaction.user
    puncte_data = load_puncte()
    user_id = str(target.id)
    if user_id not in puncte_data:
        await interaction.response.send_message(f'❌ {target.display_name} nu are niciun task raportat!', ephemeral=True)
        return
    p = puncte_data[user_id]['puncte']
    taskuri = puncte_data[user_id]['taskuri_total']
    grad = get_grad(p)
    embed = discord.Embed(title=f'📊 Statistici — {target.display_name}', color=discord.Color.gold())
    embed.add_field(name='💎 Puncte', value=f'**{p}**', inline=True)
    embed.add_field(name='🏆 Grad', value=grad, inline=True)
    embed.add_field(name='📋 Taskuri', value=str(taskuri), inline=True)
    if p < 70: embed.add_field(name='⬆️ Pana la Nobil', value=f'{70-p} puncte', inline=False)
    elif p < 140: embed.add_field(name='⬆️ Pana la Cavaler', value=f'{140-p} puncte', inline=False)
    elif p < 210: embed.add_field(name='⬆️ Pana la Baron', value=f'{210-p} puncte', inline=False)
    elif p < 300: embed.add_field(name='⬆️ Pana la Conte', value=f'{300-p} puncte', inline=False)
    elif p < 500: embed.add_field(name='⬆️ Pana la Legendar', value=f'{500-p} puncte', inline=False)
    else: embed.add_field(name='👑 Rang Maxim!', value='Esti Legendar!', inline=False)
    embed.set_thumbnail(url=target.display_avatar.url)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='top', description='Clasament top 10 membri')
async def top_cmd(interaction: discord.Interaction):
    puncte_data = load_puncte()
    if not puncte_data:
        await interaction.response.send_message('❌ Nu exista niciun task raportat!', ephemeral=True)
        return
    sorted_members = sorted(puncte_data.items(), key=lambda x: x[1]['puncte'], reverse=True)[:10]
    medals = ['🥇','🥈','🥉','4️⃣','5️⃣','6️⃣','7️⃣','8️⃣','9️⃣','🔟']
    embed = discord.Embed(title='🏆 TOP 10 — LEVEL UP', color=discord.Color.gold())
    desc = ''
    for i, (uid, data) in enumerate(sorted_members):
        grad = get_grad(data['puncte'])
        desc += f"{medals[i]} **{data['nume']}** — {data['puncte']} puncte | {grad}\n"
    embed.description = desc
    embed.set_footer(text=f"Actualizat: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='adauga_puncte', description='[STAFF] Adauga puncte unui membru')
@app_commands.checks.has_any_role('Developer', 'Admin', 'GM', 'Helper')
async def adauga_puncte(interaction: discord.Interaction, membru: discord.Member, puncte: int, motiv: str = 'Acordat de staff'):
    puncte_data = load_puncte()
    user_id = str(membru.id)
    if user_id not in puncte_data:
        puncte_data[user_id] = {'nume': membru.display_name, 'puncte': 0, 'taskuri_total': 0, 'ultima_activitate': datetime.now().strftime('%Y-%m-%d %H:%M')}
    puncte_data[user_id]['puncte'] += puncte
    puncte_data[user_id]['nume'] = membru.display_name
    save_puncte(puncte_data)
    total = puncte_data[user_id]['puncte']
    grad = get_grad(total)
    embed = discord.Embed(title='✅ Puncte adaugate!', color=discord.Color.green())
    embed.add_field(name='👤 Membru', value=membru.mention, inline=True)
    embed.add_field(name='➕ Adaugate', value=f'+{puncte}', inline=True)
    embed.add_field(name='💎 Total', value=f'{total} puncte | {grad}', inline=True)
    embed.add_field(name='📝 Motiv', value=motiv, inline=False)
    await interaction.response.send_message(embed=embed)

@bot.tree.command(name='scade_puncte', description='[STAFF] Scade puncte unui membru')
@app_commands.checks.has_any_role('Developer', 'Admin', 'GM', 'Helper')
async def scade_puncte(interaction: discord.Interaction, membru: discord.Member, puncte: int, motiv: str = 'Retrogradare'):
    puncte_data = load_puncte()
    user_id = str(membru.id)
    if user_id not in puncte_data:
        await interaction.response.send_message('❌ Membrul nu are puncte!', ephemeral=True)
        return
    puncte_data[user_id]['puncte'] = max(0, puncte_data[user_id]['puncte'] - puncte)
    save_puncte(puncte_data)
    total = puncte_data[user_id]['puncte']
    grad = get_grad(total)
    embed = discord.Embed(title='⬇️ Puncte scazute!', color=discord.Color.red())
    embed.add_field(name='👤 Membru', value=membru.mention, inline=True)
    embed.add_field(name='➖ Scazute', value=f'-{puncte}', inline=True)
    embed.add_field(name='💎 Total', value=f'{total} puncte | {grad}', inline=True)
    embed.add_field(name='📝 Motiv', value=motiv, inline=False)
    await interaction.response.send_message(embed=embed)

bot.run(TOKEN)
