import os
import discord
from discord.ext import commands, tasks
import aiosqlite
from datetime import datetime, timedelta

intents = discord.Intents.default()
intents.messages = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    async with aiosqlite.connect('events.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT
            )
        ''')
        await db.execute('''
            CREATE TABLE IF NOT EXISTS registrations (
                id INTEGER PRIMARY KEY,
                event_id INTEGER,
                user_id INTEGER,
                role TEXT,
                FOREIGN KEY (event_id) REFERENCES events (id)
            )
        ''')
        await db.commit()
    print(f'Bot connecté en tant que {bot.user}')
    send_reminders.start()

@bot.command(name='create_event')
async def create_event(ctx, name: str, date: str, *, description: str = ''):
    async with aiosqlite.connect('events.db') as db:
        await db.execute('''
            INSERT INTO events (name, date, description)
            VALUES (?, ?, ?)
        ''', (name, date, description))
        await db.commit()
    await ctx.send(f'Événement "{name}" créé pour le {date}.')

@bot.command(name='create_guild_event')
async def create_guild_event(ctx, name: str, date: str, hour: str, *, description: str = ''):
    event_time = f'{date} {hour}'
    event_datetime = datetime.strptime(event_time, '%Y-%m-%d %H:%M:%S')

    guild = ctx.guild
    created_event = await guild.create_scheduled_event(
        name=name,
        start_time=event_datetime,
        end_time=event_datetime + timedelta(hours=2),  # Assuming the event lasts 2 hours
        description=description,
        location="In-game"
    )

    async with aiosqlite.connect('events.db') as db:
        await db.execute('''
            INSERT INTO events (name, date, description)
            VALUES (?, ?, ?)
        ''', (name, event_datetime.strftime('%Y-%m-%d %H:%M:%S'), description))
        await db.commit()

    await ctx.send(f'Événement "{name}" créé pour le {event_datetime} sur Discord.')

@bot.command(name='list_events')
async def list_events(ctx):
    async with aiosqlite.connect('events.db') as db:
        async with db.execute('SELECT id, name, date, description FROM events') as cursor:
            events = await cursor.fetchall()
    if events:
        response = '\n'.join([f'**{name}** - {date}\n{description}\nEvent ID: {event_id}' for event_id, name, date, description in events])
    else:
        response = 'Aucun événement prévu.'
    await ctx.send(response)

@bot.command(name='delete_event')
async def delete_event(ctx, event_id: int):
    async with aiosqlite.connect('events.db') as db:
        await db.execute('DELETE FROM events WHERE id = ?', (event_id,))
        await db.execute('DELETE FROM registrations WHERE event_id = ?', (event_id,))
        await db.commit()
    await ctx.send(f'Événement avec l\'ID "{event_id}" supprimé.')

@bot.command(name='register')
async def register(ctx, event_id: int, role: str):
    user_id = ctx.author.id
    async with aiosqlite.connect('events.db') as db:
        await db.execute('''
            INSERT INTO registrations (event_id, user_id, role)
            VALUES (?, ?, ?)
        ''', (event_id, user_id, role))
        await db.commit()
    await ctx.send(f'{ctx.author.display_name} s\'est inscrit à l\'événement {event_id} en tant que {role}.')

@bot.command(name='list_registrations')
async def list_registrations(ctx, event_id: int):
    async with aiosqlite.connect('events.db') as db:
        async with db.execute('SELECT user_id, role FROM registrations WHERE event_id = ?', (event_id,)) as cursor:
            registrations = await cursor.fetchall()
    if registrations:
        response = '\n'.join([f'<@{user_id}> - {role}' for user_id, role in registrations])
    else:
        response = 'Aucune inscription pour cet événement.'
    await ctx.send(response)

@tasks.loop(minutes=60)
async def send_reminders():
    now = datetime.utcnow()
    reminder_time = now + timedelta(hours=1)
    async with aiosqlite.connect('events.db') as db:
        async with db.execute('SELECT id, name, date FROM events') as cursor:
            events = await cursor.fetchall()
    for event_id, name, date_str in events:
        event_date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        if now < event_date <= reminder_time:
            async with aiosqlite.connect('events.db') as db:
                async with db.execute('SELECT user_id FROM registrations WHERE event_id = ?', (event_id,)) as cursor:
                    registrations = await cursor.fetchall()
            for user_id, in registrations:
                user = await bot.fetch_user(user_id)
                await user.send(f'Reminder: L\'événement "{name}" commence dans moins d\'une heure.')

# Lire le token depuis les variables d'environnement
token = os.getenv('DISCORD_TOKEN')
bot.run(token)
