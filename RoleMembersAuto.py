import asyncio
import discord
from discord.ext import commands, tasks
from discord import app_commands

TOKEN = "MTUzNzA2Nzk2MTYzMjgxNzE2Mg.G56wTi.CKJKgcDB4dQBMshkoGPHbfsqhY_w8BaGZWpzvw"

ROLE_NAME = "Member"
CHANNEL_NAME = "cxz"

CHECK_INTERVAL = 3
ROLE_DELAY = 0.35

intents = discord.Intents.default()
intents.members = True

bot = commands.Bot(
    command_prefix="!",
    intents=intents
)


def out(text):
    print(text, flush=True)


def find_role(guild):
    return discord.utils.get(
        guild.roles,
        name=ROLE_NAME
    )


def find_channel(guild):
    return discord.utils.get(
        guild.text_channels,
        name=CHANNEL_NAME
    )


def can_manage_role(guild, role):
    me = guild.me

    if me is None:
        return False

    if not me.guild_permissions.manage_roles:
        return False

    if role.is_default():
        return False

    return role < me.top_role


async def add_role(member):
    if member.bot:
        return False

    guild = member.guild
    role = find_role(guild)

    if role is None:
        out(
            f"[-] ROLE NOT FOUND | "
            f"{guild.name} | {ROLE_NAME}"
        )
        return False

    if role in member.roles:
        return False

    if not can_manage_role(guild, role):
        out(
            f"[-] CANNOT MANAGE ROLE | "
            f"{guild.name} | {ROLE_NAME}"
        )
        return False

    try:
        await member.add_roles(
            role,
            reason="Automatic Member Role"
        )

        out(
            f"[✓] ROLE ADDED | "
            f"{member.display_name} -> {ROLE_NAME}"
        )

        return True

    except discord.Forbidden:
        out(
            f"[-] ROLE FORBIDDEN | "
            f"{member.display_name}"
        )

    except discord.HTTPException as error:
        out(
            f"[-] ROLE API ERROR | "
            f"{type(error).__name__}: {error}"
        )

    except Exception as error:
        out(
            f"[-] ROLE ERROR | "
            f"{type(error).__name__}: {error}"
        )

    return False


async def send_cxz(guild, text):
    channel = find_channel(guild)

    if channel is None:
        out(
            f"[-] CHANNEL NOT FOUND | "
            f"{guild.name} | #{CHANNEL_NAME}"
        )
        return False

    me = guild.me

    if me is None:
        return False

    permissions = channel.permissions_for(me)

    if not permissions.view_channel:
        out(
            f"[-] NO VIEW PERMISSION | "
            f"{guild.name} | #{CHANNEL_NAME}"
        )
        return False

    if not permissions.send_messages:
        out(
            f"[-] NO SEND PERMISSION | "
            f"{guild.name} | #{CHANNEL_NAME}"
        )
        return False

    message = f"```{text}```"

    try:
        await channel.send(
            message,
            allowed_mentions=discord.AllowedMentions.none()
        )

        out(
            f"[✓] SENT | "
            f"#{CHANNEL_NAME} | {text}"
        )

        return True

    except discord.Forbidden:
        out(
            f"[-] MESSAGE FORBIDDEN | "
            f"{guild.name} | #{CHANNEL_NAME}"
        )

    except discord.HTTPException as error:
        out(
            f"[-] MESSAGE API ERROR | "
            f"{type(error).__name__}: {error}"
        )

    except Exception as error:
        out(
            f"[-] MESSAGE ERROR | "
            f"{type(error).__name__}: {error}"
        )

    return False


async def fetch_all_members(guild):
    try:
        members = [
            member
            async for member in guild.fetch_members(
                limit=None
            )
        ]

        return members

    except discord.Forbidden:
        out(
            f"[-] MEMBER FETCH FORBIDDEN | "
            f"{guild.name}"
        )

    except discord.HTTPException as error:
        out(
            f"[-] MEMBER FETCH API ERROR | "
            f"{guild.name} | {error}"
        )

    except Exception as error:
        out(
            f"[-] MEMBER FETCH ERROR | "
            f"{guild.name} | "
            f"{type(error).__name__}: {error}"
        )

    return []


async def check_guild(guild):
    role = find_role(guild)

    if role is None:
        await send_cxz(
            guild,
            f"[-] Không tìm thấy Role {ROLE_NAME}."
        )
        return 0, 0, 0, 0

    if not can_manage_role(guild, role):
        await send_cxz(
            guild,
            f"[-] Bot không thể quản lý Role {ROLE_NAME}."
        )
        return 0, 0, 0, 0

    members = await fetch_all_members(guild)

    if not members:
        return 0, 0, 0, 0

    checked = 0
    added = 0
    already = 0
    failed = 0

    for member in members:

        if member.bot:
            continue

        checked += 1

        name = member.display_name

        if role in member.roles:

            already += 1

            await send_cxz(
                guild,
                f"[{name}]: "
                f"Đã có Role {ROLE_NAME}<✓>"
            )

            continue

        if ROLE_DELAY > 0:
            await asyncio.sleep(ROLE_DELAY)

        success = await add_role(member)

        if success:
            added += 1

            await send_cxz(
                guild,
                f"[{name}]: "
                f"Đã trao Role {ROLE_NAME}<✓>"
            )

        else:
            failed += 1

            await send_cxz(
                guild,
                f"[{name}]: "
                f"Không thể trao Role {ROLE_NAME}<- >"
            )

    return checked, added, already, failed


async def perform_check():
    total_checked = 0
    total_added = 0
    total_already = 0
    total_failed = 0

    for guild in bot.guilds:

        out(
            f"[-] CHECKING | {guild.name}"
        )

        checked, added, already, failed = (
            await check_guild(guild)
        )

        total_checked += checked
        total_added += added
        total_already += already
        total_failed += failed

        out(
            f"[✓] DONE | "
            f"{guild.name} | "
            f"checked={checked} | "
            f"added={added} | "
            f"already={already} | "
            f"failed={failed}"
        )

    return (
        total_checked,
        total_added,
        total_already,
        total_failed
    )


@bot.event
async def on_ready():

    out("=" * 60)
    out(f"[✓] ONLINE | {bot.user}")
    out(f"[✓] BOT ID | {bot.user.id}")
    out(f"[✓] SERVERS | {len(bot.guilds)}")
    out("=" * 60)

    for guild in bot.guilds:

        try:
            bot.tree.copy_global_to(
                guild=guild
            )

            synced = await bot.tree.sync(
                guild=guild
            )

            out(
                f"[✓] COMMANDS SYNCED | "
                f"{guild.name} | "
                f"{len(synced)}"
            )

        except Exception as error:
            out(
                f"[-] COMMAND SYNC ERROR | "
                f"{guild.name} | "
                f"{type(error).__name__}: {error}"
            )

    for guild in bot.guilds:

        role = find_role(guild)
        channel = find_channel(guild)

        out(
            f"[-] SERVER CHECK | "
            f"{guild.name}"
        )

        if role is None:
            out(
                f"[-] ROLE NOT FOUND | "
                f"{ROLE_NAME}"
            )

        else:
            out(
                f"[✓] ROLE FOUND | "
                f"{ROLE_NAME} | "
                f"position={role.position}"
            )

            if can_manage_role(guild, role):
                out(
                    f"[✓] ROLE MANAGE OK | "
                    f"{ROLE_NAME}"
                )
            else:
                out(
                    f"[-] ROLE MANAGE BLOCKED | "
                    f"{ROLE_NAME}"
                )

        if channel is None:
            out(
                f"[-] CHANNEL NOT FOUND | "
                f"#{CHANNEL_NAME}"
            )

        else:
            me = guild.me

            if me is not None:

                permissions = channel.permissions_for(
                    me
                )

                out(
                    f"[✓] CHANNEL FOUND | "
                    f"#{CHANNEL_NAME}"
                )

                out(
                    f"[✓] VIEW={permissions.view_channel} | "
                    f"SEND={permissions.send_messages}"
                )

    if not auto_check.is_running():

        auto_check.start()

        out(
            f"[✓] AUTO CHECK STARTED | "
            f"{CHECK_INTERVAL}s"
        )

    out("=" * 60)


@bot.event
async def on_member_join(member):

    if member.bot:
        return

    out(
        f"[-] NEW MEMBER | "
        f"{member.display_name} | "
        f"{member.guild.name}"
    )

    role = find_role(member.guild)

    if role is None:
        return

    if role in member.roles:
        await send_cxz(
            member.guild,
            f"[{member.display_name}]: "
            f"Đã có Role {ROLE_NAME}<✓>"
        )
        return

    success = await add_role(member)

    if success:

        await send_cxz(
            member.guild,
            f"[{member.display_name}]: "
            f"Đã trao Role {ROLE_NAME}<✓>"
        )

    else:

        await send_cxz(
            member.guild,
            f"[{member.display_name}]: "
            f"Không thể trao Role {ROLE_NAME}<- >"
        )


@tasks.loop(seconds=CHECK_INTERVAL)
async def auto_check():

    out("=" * 60)
    out("[−] AUTO CHECK START")

    try:

        checked, added, already, failed = (
            await perform_check()
        )

        out(
            f"[✓] CHECK COMPLETE | "
            f"checked={checked} | "
            f"added={added} | "
            f"already={already} | "
            f"failed={failed}"
        )

    except asyncio.CancelledError:

        raise

    except Exception as error:

        out(
            f"[-] AUTO CHECK ERROR | "
            f"{type(error).__name__}: {error}"
        )

    out(
        f"[✓] NEXT CHECK | "
        f"{CHECK_INTERVAL}s"
    )

    out("=" * 60)


@auto_check.before_loop
async def before_auto_check():

    await bot.wait_until_ready()


@auto_check.error
async def auto_check_error(error):

    out(
        f"[-] AUTO CHECK LOOP ERROR | "
        f"{type(error).__name__}: {error}"
    )


@bot.tree.command(
    name="start",
    description="Bat auto-check Member"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def start_command(
    interaction: discord.Interaction
):

    if auto_check.is_running():

        await interaction.response.send_message(
            "```"
            "[✓] Auto-check đang chạy.\n"
            "[-] Chu kỳ: 10 giây."
            "```"
        )

        return

    auto_check.start()

    await interaction.response.send_message(
        "```"
        "[✓] AUTO CHECK STARTED\n"
        "[-] Đang quét toàn bộ Member.\n"
        "[-] Chu kỳ: 10 giây."
        "```"
    )

    out(
        f"[✓] /start | "
        f"{interaction.user}"
    )


@bot.tree.command(
    name="stop",
    description="Tat auto-check Member"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def stop_command(
    interaction: discord.Interaction
):

    if not auto_check.is_running():

        await interaction.response.send_message(
            "```"
            "[-] Auto-check đang tắt."
            "```"
        )

        return

    auto_check.cancel()

    await interaction.response.send_message(
        "```"
        "[✓] AUTO CHECK STOPPED"
        "```"
    )

    out(
        f"[-] /stop | "
        f"{interaction.user}"
    )


@bot.tree.command(
    name="check",
    description="Quet Member ngay lap tuc"
)
@app_commands.checks.has_permissions(
    manage_guild=True
)
async def check_command(
    interaction: discord.Interaction
):

    await interaction.response.send_message(
        "```"
        "[-] CHECK STARTED"
        "```"
    )

    try:

        checked, added, already, failed = (
            await perform_check()
        )

        await interaction.edit_original_response(
            content=(
                "```"
                "[✓] CHECK COMPLETE\n"
                f"[-] Checked: {checked}\n"
                f"[✓] Added: {added}\n"
                f"[-] Already: {already}\n"
                f"[-] Failed: {failed}"
                "```"
            )
        )

        out(
            f"[✓] /check | "
            f"{interaction.user} | "
            f"checked={checked} | "
            f"added={added} | "
            f"failed={failed}"
        )

    except Exception as error:

        out(
            f"[-] /check ERROR | "
            f"{type(error).__name__}: {error}"
        )

        try:

            await interaction.edit_original_response(
                content=(
                    "```"
                    "[-] CHECK ERROR\n"
                    f"{type(error).__name__}: {error}"
                    "```"
                )
            )

        except Exception:
            pass


@start_command.error
@stop_command.error
@check_command.error
async def command_error(
    interaction,
    error
):

    if isinstance(
        error,
        app_commands.errors.MissingPermissions
    ):

        message = (
            "```"
            "[-] Cần quyền Manage Server."
            "```"
        )

    else:

        message = (
            "```"
            "[-] COMMAND ERROR\n"
            f"{type(error).__name__}: {error}"
            "```"
        )

    try:

        if interaction.response.is_done():

            await interaction.followup.send(
                message
            )

        else:

            await interaction.response.send_message(
                message
            )

    except Exception as error:

        out(
            f"[-] COMMAND RESPONSE ERROR | "
            f"{type(error).__name__}: {error}"
        )


@bot.event
async def on_error(
    event,
    *args,
    **kwargs
):

    out(
        f"[-] EVENT ERROR | "
        f"{event}"
    )


def main():

    out("=" * 60)
    out("[✓] STARTING DISCORD BOT")
    out(f"[-] ROLE | {ROLE_NAME}")
    out(f"[-] CHANNEL | #{CHANNEL_NAME}")
    out(f"[-] CHECK INTERVAL | {CHECK_INTERVAL}s")
    out(f"[-] ROLE DELAY | {ROLE_DELAY}s")
    out("=" * 60)

    if (
        not TOKEN
        or TOKEN == "DAN_TOKEN_BOT_VAO_DAY"
    ):

        out(
            "[-] TOKEN CHUA DUOC DAT"
        )

        return

    try:

        bot.run(TOKEN)

    except discord.LoginFailure:

        out(
            "[-] LOGIN FAILED | "
            "TOKEN KHONG HOP LE"
        )

    except discord.PrivilegedIntentsRequired:

        out(
            "[-] PRIVILEGED INTENT ERROR | "
            "Bat Server Members Intent"
        )

    except discord.HTTPException as error:

        out(
            f"[-] DISCORD HTTP ERROR | "
            f"{type(error).__name__}: {error}"
        )

    except KeyboardInterrupt:

        out(
            "[✓] BOT STOPPED BY USER"
        )

    except Exception as error:

        out(
            f"[-] BOT STOPPED | "
            f"{type(error).__name__}: {error}"
        )


if __name__ == "__main__":
    main()