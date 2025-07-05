import discord
from discord.ext import commands
import configparser
import os
from datetime import datetime

# ─── โหลด config.ini ───
config = configparser.ConfigParser()
config.read("config.ini")

category_id = int(config["Ticket"]["category_id"])
staff_role_id = int(config["Ticket"]["staff_role_id"])
token = str(config["token"]["token"])

# ─── ตั้งค่า Intents ───
intents = discord.Intents.all()
bot = commands.Bot(command_prefix=">", intents=intents)

# ─── Path เก็บ Ticket และ Log ───
counter_file = "ticket_counter.txt"
log_folder = "ticket_logs"

if not os.path.exists(log_folder):
    os.makedirs(log_folder)

# ─── อ่านเลข Ticket ล่าสุด ───
def get_next_ticket_number():
    if not os.path.exists(counter_file):
        with open(counter_file, "w") as f:
            f.write("1")
        return 1

    with open(counter_file, "r") as f:
        num = int(f.read().strip())

    with open(counter_file, "w") as f:
        f.write(str(num + 1))

    return num

# ─── บันทึก Log แต่ละ Ticket ───
def log_ticket(ticket_number, message):
    log_path = os.path.join(log_folder, f"ticket-{ticket_number}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(log_path, "a", encoding="utf-8") as f:
        f.write(f"[{timestamp}] {message}\n")

@bot.event
async def on_ready():
    print(f'✅ Logged in as {bot.user}')

@bot.command()
async def sendticket(ctx):
    view = TicketButton()
    await ctx.send("🎫 กดปุ่มด้านล่างเพื่อเปิด Ticket", view=view)

class TicketButton(discord.ui.View):
    @discord.ui.button(label="🎫 เปิด Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        category = discord.utils.get(guild.categories, id=category_id)
        staff_role = guild.get_role(staff_role_id)

        if not category or not staff_role:
            await interaction.response.send_message("❌ ไม่พบหมวดหมู่หรือ Role ที่ตั้งค่าไว้ใน config.ini", ephemeral=True)
            return

        ticket_number = get_next_ticket_number()

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        ticket_channel = await guild.create_text_channel(
            name=f"ticket-{ticket_number}",
            overwrites=overwrites,
            category=category,
            reason=f"Ticket #{ticket_number} จาก {interaction.user}"
        )

        log_ticket(ticket_number, f"{interaction.user} เปิด Ticket #{ticket_number} (user ID: {interaction.user.id})")

        await ticket_channel.send(f"{interaction.user.mention} ทีมงานจะติดต่อคุณในไม่ช้า")
        await interaction.response.send_message(f"✅ Ticket #{ticket_number} ถูกสร้างแล้ว: {ticket_channel.mention}", ephemeral=True)

@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.name.startswith("ticket-"):
        try:
            ticket_number = int(message.channel.name.split("-")[1])
        except (IndexError, ValueError):
            ticket_number = None

        if ticket_number:
            if message.attachments:
                files = ", ".join(att.filename for att in message.attachments)
                log_msg = f"{message.author} ({message.author.id}): [ไฟล์แนบ] {files}"
            else:
                log_msg = f"{message.author} ({message.author.id}): {message.content}"

            log_ticket(ticket_number, log_msg)

    await bot.process_commands(message)

bot.run(token)
