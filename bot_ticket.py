import discord
from discord.ext import commands
import configparser
import os

# ─── โหลด config.ini ───
config = configparser.ConfigParser()
config.read("config.ini")

category_id = int(config["Ticket"]["category_id"])
staff_role_id = int(config["Ticket"]["staff_role_id"])
token = str(config["token"]["token"])

counter_file = "ticket_counter.txt"

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


class TicketButton(discord.ui.View):



    @discord.ui.button(label="🎫 เปิด Ticket", style=discord.ButtonStyle.green)
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild

        # โหลดหมวดหมู่และ Role
        category = discord.utils.get(guild.categories, id=category_id)
        staff_role = guild.get_role(staff_role_id)

        if not category or not staff_role:
            await interaction.response.send_message("❌ ไม่พบหมวดหมู่หรือ Role ที่ตั้งค่าไว้ใน config.ini", ephemeral=True)
            return

        ticket_number = get_next_ticket_number()

        # ตั้งค่า Permission
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

        await ticket_channel.send(f"{interaction.user.mention} ทีมงานจะติดต่อคุณในไม่ช้า")
        await interaction.response.send_message(f"✅ Ticket #{ticket_number} ถูกสร้างแล้ว: {ticket_channel.mention}", ephemeral=True)