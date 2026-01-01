import os
import asyncio
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command, CommandStart, ChatMemberUpdatedFilter
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, ChatMemberUpdated, ChatPermissions
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, Router, F
from aiogram.exceptions import TelegramBadRequest

from models import init_db, get_session, User, Project, Raid

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BOT_TOKEN = os.environ.get("BOT_TOKEN")

router = Router()

SCAM_KEYWORDS = ["airdrop", "presale", "whitelist", "investment", "guaranteed", "profit", "buy now"]

# Captcha logic
@router.chat_member(ChatMemberUpdatedFilter(member_status_changed=F.NEW_CHAT_MEMBER))
async def on_user_join(event: ChatMemberUpdated, bot: Bot):
    session = get_session()
    if not session:
        return

    project = session.query(Project).filter(Project.telegram_group_id == event.chat.id).first()
    if not project or not project.captcha_enabled:
        return

    user = event.new_chat_member.user
    
    # Restrict user until captcha is solved
    try:
        await bot.restrict_chat_member(
            chat_id=event.chat.id,
            user_id=user.id,
            permissions=ChatPermissions(can_send_messages=False)
        )
    except TelegramBadRequest:
        return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="I am not a bot", callback_data=f"captcha_solve_{user.id}")]
    ])

    await bot.send_message(
        chat_id=event.chat.id,
        text=f"Welcome {user.first_name}! Please solve the captcha to speak.",
        reply_markup=keyboard
    )

@router.callback_query(F.data.startswith("captcha_solve_"))
async def solve_captcha(callback: CallbackQuery, bot: Bot):
    user_id = int(callback.data.split("_")[-1])
    if callback.from_user.id != user_id:
        await callback.answer("This is not for you!", show_alert=True)
        return

    await bot.restrict_chat_member(
        chat_id=callback.message.chat.id,
        user_id=user_id,
        permissions=ChatPermissions(
            can_send_messages=True,
            can_send_media_messages=True,
            can_send_polls=True,
            can_send_other_messages=True,
            can_add_web_page_previews=True
        )
    )
    
    await callback.message.delete()
    await callback.answer("Verification successful!")

# Anti-spam and scam filter
@router.message(F.text)
async def message_filter(message: Message):
    if not message.chat.type in ["group", "supergroup"]:
        return

    session = get_session()
    if not session:
        return

    project = session.query(Project).filter(Project.telegram_group_id == message.chat.id).first()
    if not project or not project.scam_filter_enabled:
        return

    text = message.text.lower()
    if any(keyword in text for keyword in SCAM_KEYWORDS):
        try:
            await message.delete()
            await message.answer(f"Message from {message.from_user.first_name} removed: Potential scam content detected.")
        except TelegramBadRequest:
            pass


class ProjectSetup(StatesGroup):
    waiting_for_name = State()
    waiting_for_symbol = State()
    waiting_for_description = State()
    waiting_for_logo = State()
    waiting_for_website = State()
    waiting_for_twitter = State()

class RaidSetup(StatesGroup):
    waiting_for_tweet_url = State()
    waiting_for_description = State()


def get_or_create_user(telegram_id: int, username: str = None, first_name: str = None, last_name: str = None):
    session = get_session()
    if not session:
        return None
    
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        session.commit()
    return user


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = get_or_create_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name
    )
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Create New Project", callback_data="new_project")],
        [InlineKeyboardButton(text="My Projects", callback_data="my_projects")],
        [InlineKeyboardButton(text="Help", callback_data="help")]
    ])
    
    await message.answer(
        "Welcome to Eden Token Assistant!\n\n"
        "I help you prepare, organize, and launch meme coin projects on pump.fun "
        "in a secure, transparent, and user-controlled way.\n\n"
        "What would you like to do?",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "new_project")
async def start_new_project(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(
        "Let's create your new token project!\n\n"
        "Please enter your token name:"
    )
    await state.set_state(ProjectSetup.waiting_for_name)


@router.message(ProjectSetup.waiting_for_name)
async def process_name(message: Message, state: FSMContext):
    await state.update_data(token_name=message.text)
    await message.answer(
        f"Token name: {message.text}\n\n"
        "Now enter your token symbol (e.g., DOGE, PEPE):"
    )
    await state.set_state(ProjectSetup.waiting_for_symbol)


@router.message(ProjectSetup.waiting_for_symbol)
async def process_symbol(message: Message, state: FSMContext):
    symbol = message.text.upper()
    await state.update_data(token_symbol=symbol)
    await message.answer(
        f"Token symbol: {symbol}\n\n"
        "Now enter a description for your token (this will appear on pump.fun):"
    )
    await state.set_state(ProjectSetup.waiting_for_description)


@router.message(ProjectSetup.waiting_for_description)
async def process_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Logo", callback_data="skip_logo")]
    ])
    
    await message.answer(
        "Description saved!\n\n"
        "Now send your token logo image, or click 'Skip Logo' to continue without one:",
        reply_markup=keyboard
    )
    await state.set_state(ProjectSetup.waiting_for_logo)


@router.callback_query(F.data == "skip_logo")
async def skip_logo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(logo_url=None)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Website", callback_data="skip_website")]
    ])
    
    await callback.message.answer(
        "Enter your project website URL (optional):",
        reply_markup=keyboard
    )
    await state.set_state(ProjectSetup.waiting_for_website)


@router.message(ProjectSetup.waiting_for_logo)
async def process_logo(message: Message, state: FSMContext):
    if message.photo:
        photo = message.photo[-1]
        await state.update_data(logo_url=photo.file_id)
    else:
        await state.update_data(logo_url=None)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Website", callback_data="skip_website")]
    ])
    
    await message.answer(
        "Enter your project website URL (optional):",
        reply_markup=keyboard
    )
    await state.set_state(ProjectSetup.waiting_for_website)


@router.callback_query(F.data == "skip_website")
async def skip_website(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.update_data(website=None)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Twitter", callback_data="skip_twitter")]
    ])
    
    await callback.message.answer(
        "Enter your project Twitter handle (optional):",
        reply_markup=keyboard
    )
    await state.set_state(ProjectSetup.waiting_for_twitter)


@router.message(ProjectSetup.waiting_for_website)
async def process_website(message: Message, state: FSMContext):
    await state.update_data(website=message.text)
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Skip Twitter", callback_data="skip_twitter")]
    ])
    
    await message.answer(
        "Enter your project Twitter handle (optional):",
        reply_markup=keyboard
    )
    await state.set_state(ProjectSetup.waiting_for_twitter)


@router.callback_query(F.data == "skip_twitter")
async def skip_twitter(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await finish_project_setup(callback.message, state, callback.from_user.id)


@router.message(ProjectSetup.waiting_for_twitter)
async def process_twitter(message: Message, state: FSMContext):
    twitter = message.text.replace("@", "")
    await state.update_data(twitter=twitter)
    await finish_project_setup(message, state, message.from_user.id)


async def finish_project_setup(message: Message, state: FSMContext, telegram_id: int):
    data = await state.get_data()
    
    session = get_session()
    if session:
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            project = Project(
                owner_id=user.id,
                token_name=data.get("token_name"),
                token_symbol=data.get("token_symbol"),
                description=data.get("description"),
                logo_url=data.get("logo_url"),
                website=data.get("website"),
                twitter=data.get("twitter"),
                status="draft"
            )
            session.add(project)
            session.commit()
            
            pump_fun_desc = generate_pump_fun_description(project)
            project.pump_fun_description = pump_fun_desc
            session.commit()
    
    await state.clear()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="View Project", callback_data=f"view_project_{project.id if session else 0}")],
        [InlineKeyboardButton(text="Group Police Settings", callback_data=f"police_settings_{project.id if session else 0}")],
        [InlineKeyboardButton(text="Twitter Raid Manager", callback_data=f"raid_manager_{project.id if session else 0}")],
        [InlineKeyboardButton(text="Generate Launch Content", callback_data=f"generate_content_{project.id if session else 0}")],
        [InlineKeyboardButton(text="Launch on pump.fun", callback_data=f"launch_{project.id if session else 0}")],
        [InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")]
    ])
    
    await message.answer(
        f"Project Created!\n\n"
        f"Token: {data.get('token_name')} ({data.get('token_symbol')})\n"
        f"Description: {data.get('description', 'N/A')[:100]}...\n"
        f"Website: {data.get('website', 'Not set')}\n"
        f"Twitter: @{data.get('twitter', 'Not set')}\n\n"
        "What would you like to do next?",
        reply_markup=keyboard
    )


def generate_pump_fun_description(project: Project) -> str:
    parts = []
    if project.description:
        parts.append(project.description)
    
    socials = []
    if project.website:
        socials.append(f"Website: {project.website}")
    if project.twitter:
        socials.append(f"Twitter: @{project.twitter}")
    
    if socials:
        parts.append("\n".join(socials))
    
    return "\n\n".join(parts)


@router.callback_query(F.data == "my_projects")
async def show_my_projects(callback: CallbackQuery):
    await callback.answer()
    
    session = get_session()
    if not session:
        await callback.message.answer("Database not available. Please try again later.")
        return
    
    user = session.query(User).filter(User.telegram_id == callback.from_user.id).first()
    if not user:
        await callback.message.answer("You don't have any projects yet. Create one first!")
        return
    
    projects = session.query(Project).filter(Project.owner_id == user.id).all()
    
    if not projects:
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="Create New Project", callback_data="new_project")],
            [InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")]
        ])
        await callback.message.answer("You don't have any projects yet.", reply_markup=keyboard)
        return
    
    buttons = []
    for p in projects:
        buttons.append([InlineKeyboardButton(
            text=f"{p.token_name} ({p.token_symbol}) - {p.status}",
            callback_data=f"view_project_{p.id}"
        )])
    buttons.append([InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")])
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    await callback.message.answer("Your Projects:", reply_markup=keyboard)


@router.callback_query(F.data == "help")
async def show_help(callback: CallbackQuery):
    await callback.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")]
    ])
    
    await callback.message.answer(
        "Eden Token Assistant Help\n\n"
        "I help you launch meme coin projects on pump.fun safely:\n\n"
        "1. Create a project with token details\n"
        "2. Generate pump.fun-ready descriptions\n"
        "3. Create Telegram communities\n"
        "4. Get launch content templates\n"
        "5. Launch manually on pump.fun\n\n"
        "Security: I never request private keys or seed phrases. "
        "All blockchain actions are performed by you directly on pump.fun.\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/help - This help message",
        reply_markup=keyboard
    )


@router.callback_query(F.data == "main_menu")
async def main_menu(callback: CallbackQuery):
    await callback.answer()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Create New Project", callback_data="new_project")],
        [InlineKeyboardButton(text="My Projects", callback_data="my_projects")],
        [InlineKeyboardButton(text="Help", callback_data="help")]
    ])
    
    await callback.message.answer(
        "Eden Token Assistant\n\nWhat would you like to do?",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("view_project_"))
async def view_project(callback: CallbackQuery):
    await callback.answer()
    
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session:
        await callback.message.answer("Database not available.")
        return
    
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        await callback.message.answer("Project not found.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Generate Launch Content", callback_data=f"generate_content_{project_id}")],
        [InlineKeyboardButton(text="Launch on pump.fun", callback_data=f"launch_{project_id}")],
        [InlineKeyboardButton(text="Back to Projects", callback_data="my_projects")]
    ])
    
    await callback.message.answer(
        f"Project Details\n\n"
        f"Name: {project.token_name}\n"
        f"Symbol: {project.token_symbol}\n"
        f"Status: {project.status}\n"
        f"Description: {project.description or 'Not set'}\n"
        f"Website: {project.website or 'Not set'}\n"
        f"Twitter: @{project.twitter or 'Not set'}",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("generate_content_"))
async def generate_content(callback: CallbackQuery):
    await callback.answer()
    
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session:
        await callback.message.answer("Database not available.")
        return
    
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        await callback.message.answer("Project not found.")
        return
    
    shill_message = f"Check out ${project.token_symbol}! {project.description or 'The next big thing on pump.fun!'}"
    if project.twitter:
        shill_message += f" Follow us @{project.twitter}"
    
    announcement = f"Introducing {project.token_name} (${project.token_symbol})!\n\n{project.description or 'Coming soon to pump.fun!'}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Launch on pump.fun", callback_data=f"launch_{project_id}")],
        [InlineKeyboardButton(text="Back to Project", callback_data=f"view_project_{project_id}")]
    ])
    
    await callback.message.answer(
        f"Generated Content for {project.token_name}\n\n"
        f"Shill Message:\n{shill_message}\n\n"
        f"Announcement Template:\n{announcement}\n\n"
        f"pump.fun Description:\n{project.pump_fun_description or project.description}",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("launch_"))
async def launch_project(callback: CallbackQuery):
    await callback.answer()
    
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session:
        await callback.message.answer("Database not available.")
        return
    
    project = session.query(Project).filter(Project.id == project_id).first()
    if not project:
        await callback.message.answer("Project not found.")
        return
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Open pump.fun", url="https://pump.fun/create")],
        [InlineKeyboardButton(text="Mark as Launched", callback_data=f"mark_launched_{project_id}")],
        [InlineKeyboardButton(text="Back to Project", callback_data=f"view_project_{project_id}")]
    ])
    
    await callback.message.answer(
        f"Launch {project.token_name} on pump.fun\n\n"
        f"1. Click 'Open pump.fun' below\n"
        f"2. Connect your wallet\n"
        f"3. Enter token details:\n"
        f"   - Name: {project.token_name}\n"
        f"   - Symbol: {project.token_symbol}\n"
        f"   - Description: Copy from below\n"
        f"4. Upload your logo\n"
        f"5. Sign the transaction with your wallet\n\n"
        f"Description to copy:\n\n{project.pump_fun_description or project.description}\n\n"
        "Remember: Never share your private keys!",
        reply_markup=keyboard
    )


@router.callback_query(F.data.startswith("police_settings_"))
async def police_settings(callback: CallbackQuery):
    await callback.answer()
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    project = session.query(Project).get(project_id)
    if not project: return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"Captcha: {'✅' if project.captcha_enabled else '❌'}", callback_data=f"toggle_captcha_{project_id}")],
        [InlineKeyboardButton(text=f"Scam Filter: {'✅' if project.scam_filter_enabled else '❌'}", callback_data=f"toggle_scam_{project_id}")],
        [InlineKeyboardButton(text="Back to Project", callback_data=f"view_project_{project_id}")]
    ])
    await callback.message.answer(f"Group Police Settings for {project.token_name}:", reply_markup=keyboard)

@router.callback_query(F.data.startswith("raid_manager_"))
async def raid_manager(callback: CallbackQuery):
    await callback.answer()
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    project = session.query(Project).get(project_id)
    if not project: return

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="New Twitter Raid", callback_data=f"new_raid_{project_id}")],
        [InlineKeyboardButton(text="Active Raids", callback_data=f"active_raids_{project_id}")],
        [InlineKeyboardButton(text="Back to Project", callback_data=f"view_project_{project_id}")]
    ])
    await callback.message.answer(f"Twitter Raid Manager for {project.token_name}:\n\nStart a new raid or manage active ones.", reply_markup=keyboard)

@router.callback_query(F.data.startswith("new_raid_"))
async def start_new_raid(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    project_id = int(callback.data.split("_")[-1])
    await state.update_data(project_id=project_id)
    await callback.message.answer("Please send the Twitter/X tweet URL for the raid:")
    await state.set_state(RaidSetup.waiting_for_tweet_url)

@router.message(RaidSetup.waiting_for_tweet_url)
async def process_raid_url(message: Message, state: FSMContext):
    if "twitter.com" not in message.text and "x.com" not in message.text:
        await message.answer("Please provide a valid Twitter/X URL.")
        return
    await state.update_data(tweet_url=message.text)
    await message.answer("Enter a short instruction for the raid (e.g., 'Like and Retweet!'):")
    await state.set_state(RaidSetup.waiting_for_description)

@router.message(RaidSetup.waiting_for_description)
async def process_raid_desc(message: Message, state: FSMContext, bot: Bot):
    data = await state.get_data()
    project_id = data.get("project_id")
    tweet_url = data.get("tweet_url")
    desc = message.text
    
    session = get_session()
    if session:
        project = session.query(Project).get(project_id)
        if project:
            raid = Raid(project_id=project_id, tweet_url=tweet_url, description=desc)
            session.add(raid)
            session.commit()
            
            # Broadcast raid to group if exists
            if project.telegram_group_id:
                keyboard = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text="⚡️ GO RAID NOW", url=tweet_url)]
                ])
                await bot.send_message(
                    chat_id=project.telegram_group_id,
                    text=f"🚨 **NEW TWITTER RAID!** 🚨\n\n{desc}\n\nLet's show some strength! 💪",
                    reply_markup=keyboard,
                    parse_mode="Markdown"
                )
    
    await state.clear()
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back to Manager", callback_data=f"raid_manager_{project_id}")]
    ])
    await message.answer("Raid started and broadcasted to your community!", reply_markup=keyboard)

@router.callback_query(F.data.startswith("active_raids_"))
async def list_active_raids(callback: CallbackQuery):
    await callback.answer()
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    raids = session.query(Raid).filter(Raid.project_id == project_id, Raid.status == "active").all()
    
    if not raids:
        await callback.message.answer("No active raids found.")
        return

    text = "Active Twitter Raids:\n\n"
    buttons = []
    for r in raids:
        text += f"🔹 {r.description or 'Raid'} - {r.created_at.strftime('%Y-%m-%d %H:%M')}\n"
        buttons.append([InlineKeyboardButton(text="Complete Raid", callback_data=f"complete_raid_{r.id}")])
    
    buttons.append([InlineKeyboardButton(text="Back", callback_data=f"raid_manager_{project_id}")])
    await callback.message.answer(text, reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons))

@router.callback_query(F.data.startswith("complete_raid_"))
async def complete_raid(callback: CallbackQuery):
    raid_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    raid = session.query(Raid).get(raid_id)
    if raid:
        raid.status = "completed"
        session.commit()
        await callback.answer("Raid marked as completed!")
        await raid_manager(callback)
    else:
        await callback.answer("Raid not found.")

@router.callback_query(F.data.startswith("toggle_captcha_"))
async def toggle_captcha(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    project = session.query(Project).get(project_id)
    if project:
        project.captcha_enabled = not project.captcha_enabled
        session.commit()
    await police_settings(callback)

@router.callback_query(F.data.startswith("toggle_scam_"))
async def toggle_scam(callback: CallbackQuery):
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if not session: return
    project = session.query(Project).get(project_id)
    if project:
        project.scam_filter_enabled = not project.scam_filter_enabled
        session.commit()
    await police_settings(callback)
    await callback.answer("Project marked as launched!")
    
    project_id = int(callback.data.split("_")[-1])
    session = get_session()
    if session:
        project = session.query(Project).filter(Project.id == project_id).first()
        if project:
            project.status = "launched"
            session.commit()
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="View on DexScreener", url="https://dexscreener.com/solana")],
        [InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")]
    ])
    
    await callback.message.answer(
        "Congratulations! Your project has been marked as launched.\n\n"
        "Post-Launch Tips:\n"
        "- Share your token address with your community\n"
        "- Monitor on DexScreener\n"
        "- Keep your community engaged\n\n"
        "Good luck!",
        reply_markup=keyboard
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Back to Menu", callback_data="main_menu")]
    ])
    
    await message.answer(
        "Eden Token Assistant Help\n\n"
        "I help you launch meme coin projects on pump.fun safely:\n\n"
        "1. Create a project with token details\n"
        "2. Generate pump.fun-ready descriptions\n"
        "3. Create Telegram communities\n"
        "4. Get launch content templates\n"
        "5. Launch manually on pump.fun\n\n"
        "Security: I never request private keys or seed phrases. "
        "All blockchain actions are performed by you directly on pump.fun.\n\n"
        "Commands:\n"
        "/start - Main menu\n"
        "/help - This help message",
        reply_markup=keyboard
    )


async def run_bot():
    if not BOT_TOKEN:
        logger.error("BOT_TOKEN not set. Please set the BOT_TOKEN environment variable.")
        return
    
    init_db()
    
    bot = Bot(token=BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())
    dp.include_router(router)
    
    logger.info("Starting Eden Token Assistant bot...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(run_bot())
