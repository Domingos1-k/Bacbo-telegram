import os
import asyncio
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from webdriver_manager.chrome import ChromeDriverManager
from dotenv import load_dotenv
from telegram import Bot
from telegram.error import TelegramError
from concurrent.futures import ThreadPoolExecutor
import traceback
import random
import datetime
import sys

# Load environment variables from .env file
load_dotenv()

# Retrieve environment variables
TELEGRAM_BOT_TOKEN = os.getenv('7863883528:AAHGnhnA8NXqr5cdxX6HJazpyJbPIVjceQM')
TELEGRAM_CHANNEL_ID = os.getenv('-1002524967888')
WIN_STICKER_ID = os.getenv('WIN_STICKER_ID')
LOSS_STICKER_ID = os.getenv('LOSS_STICKER_ID')  
CLOSE_STICKER_ID = os.getenv('CLOSE_STICKER_ID')  
OPEN_STICKER_ID = os.getenv('OPEN_STICKER_ID') 
LOGIN_USERNAME = os.getenv('LOGIN_USERNAME')
LOGIN_PASSWORD = os.getenv('LOGIN_PASSWORD')

# Ensure all necessary environment variables are set
if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHANNEL_ID or not LOGIN_USERNAME or not LOGIN_PASSWORD:
    raise ValueError("7863883528:AAHGnhnA8NXqr5cdxX6HJazpyJbPIVjceQM, -1002524967888, LOGIN_USERNAME, and LOGIN_PASSWORD must be set in the .env file.")

# Initialize Telegram bot
bot = Bot(token=TELEGRAM_BOT_TOKEN)

# Define Telegram link messages for registration and scoreboard
LINK_MESSAGE_ENTRY_BUTTON = ('Register here', 'https://example.com/register')
LINK_MESSAGE_SCOREBOARD_BUTTON = ('Enter website', 'https://example.com/website')

# Define colors for each bet type
BET_COLORS = {
    'P': '🔵',
    'B': '🔴',
    'T': '🟡'
}

# Define bet messages
BET_MESSAGES = {
    'P': "🚨 ENTRY CONFIRMED\n🌹 BET ON COLOR ({color})\n🎯 PROTECT IN TIE ({tie_color})",
    'B': "🚨 ENTRY CONFIRMED\n🌹 BET ON COLOR ({color})\n🎯 PROTECT IN TIE ({tie_color})"
}

# Define message for gale attempt
GALE_MESSAGE = "📉 GALE ATTEMPT {attempt}"

# Define message for preparing an entry
PREPARE_MESSAGE = "🚠 PREPARE FOR POTENTIAL ENTRY"

# Tie color symbol
TIE_COLOR = BET_COLORS['T']

# Maximum number of gale attempts
MAX_GALES = 0

def get_bet_message(bet_type):
    # Generate bet message based on bet type
    color = BET_COLORS.get(bet_type, '❔')
    message_template = BET_MESSAGES.get(bet_type, "Bet type not recognized.")
    return message_template.format(color=color, tie_color=TIE_COLOR)

def get_gale_message(gale_count, bet_type):
    # Generate gale attempt message
    color = BET_COLORS.get(bet_type, '❔')
    return GALE_MESSAGE.format(attempt=gale_count, color=color)

class Scoreboard:
    def __init__(self):
        # Initialize scoreboard counters
        self.wins = 0
        self.losses = 0
        self.consecutive_wins = 0
        self.total_attempts = 0

    def record_win(self):
        # Record a win
        self.wins += 1
        self.consecutive_wins += 1
        self.total_attempts += 1

    def record_loss(self):
        # Record a loss
        self.losses += 1
        self.total_attempts += 1
        self.consecutive_wins = 0

    def calculate_assertivity_rate(self):
        # Calculate assertivity rate (win rate)
        if self.total_attempts == 0:
            return 0.0
        return round((self.wins / self.total_attempts) * 100, 2)

    def generate_scoreboard_message(self):
        # Generate scoreboard message
        return (
            f"📜 SCOREBOARD\n"
            f"🟢 Wins: {self.wins} 🔴 Losses: {self.losses}\n"
            f"🌄 Consecutive Wins: {self.consecutive_wins}\n"
            f"🎯 Assertivity Rate: {self.calculate_assertivity_rate()}100%"
        )

scoreboard = Scoreboard()

from telegram import InlineKeyboardButton, InlineKeyboardMarkup

async def send_telegram_message(message=None, is_win=False, is_loss=False, buttons=None):
    # Send a message or sticker to the Telegram channel
    try:
        if is_win and WIN_STICKER_ID:
            print("Sending win sticker...")
            await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=WIN_STICKER_ID)
        elif is_loss and LOSS_STICKER_ID:
            print("Sending loss sticker...")
            await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=LOSS_STICKER_ID)
        elif message:
            if buttons:
                reply_markup = InlineKeyboardMarkup([[InlineKeyboardButton(text, url=url) for text, url in buttons]])
                sent_message = await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message, reply_markup=reply_markup)
            else:
                sent_message = await bot.send_message(chat_id=TELEGRAM_CHANNEL_ID, text=message)
            print(f"Message sent: {message}")
            return sent_message.message_id
    except TelegramError as e:
        print(f"❌ Failed to send message: {e}")

class BettingStrategy:
    def __init__(self, strategies, max_gales=MAX_GALES):
        # Initialize betting strategy parameters
        self.strategies = strategies
        self.max_gales = max_gales
        self.is_entry_allowed = True
        self.is_green = False
        self.is_gale_active = False
        self.is_red = False
        self.current_strategy = None
        self.current_bet = None
        self.gale_count = 0
        self.prepare_message_sent = False
        self.prepare_message_id = None
        self.gale_message_ids = []
        self.wait_after_gale = False
        self.stop_requested = False

    async def execute_strategy(self, results_list):
        # Execute betting strategy based on results
        if self.stop_requested:
            return

        if self.wait_after_gale:
            self.wait_after_gale = False
            return

        if self.is_entry_allowed:
            for strategy in self.strategies:
                pattern = strategy['pattern']
                bet = strategy['bet']
                if results_list[-(len(pattern) - 1):] == pattern[:len(pattern) - 1] and not self.prepare_message_sent:
                    prepare_message = PREPARE_MESSAGE
                    self.prepare_message_id = await send_telegram_message(prepare_message)
                    self.prepare_message_sent = True
                if results_list[-len(pattern):] == pattern and self.prepare_message_sent:
                    if self.prepare_message_id:
                        try:
                            await bot.delete_message(chat_id=TELEGRAM_CHANNEL_ID, message_id=self.prepare_message_id)
                        except TelegramError as e:
                            print(f"❌ Failed to delete prepare message: {e}")
                    message = get_bet_message(bet)
                    await send_telegram_message(message, buttons=[LINK_MESSAGE_ENTRY_BUTTON])
                    self.is_entry_allowed = False
                    self.is_green = True
                    self.is_gale_active = True
                    self.current_strategy = strategy
                    self.current_bet = bet
                    self.prepare_message_sent = False
                    self.prepare_message_id = None
                    break
            return

        if not self.current_strategy:
            if self.prepare_message_sent and self.prepare_message_id:
                try:
                    await bot.delete_message(chat_id=TELEGRAM_CHANNEL_ID, message_id=self.prepare_message_id)
                except TelegramError as e:
                    print(f"❌ Failed to delete prepare message: {e}")
                self.prepare_message_sent = False
                self.prepare_message_id = None
            return

        if results_list[-1] == self.current_bet and self.is_green:
            scoreboard.record_win()
            await send_telegram_message(is_win=True)
            await send_telegram_message(scoreboard.generate_scoreboard_message(), buttons=[LINK_MESSAGE_SCOREBOARD_BUTTON])
            await self.delete_gale_messages()
            await self.reset_state(wait_after_gale=True)
            return

        if results_list[-1] == 'T' and self.is_green:
            scoreboard.record_win()
            await send_telegram_message(is_win=True)
            await send_telegram_message(scoreboard.generate_scoreboard_message(), buttons=[LINK_MESSAGE_SCOREBOARD_BUTTON])
            await self.delete_gale_messages()
            await self.reset_state(wait_after_gale=True)
            return

        if results_list[-1] != self.current_bet and self.is_green and self.is_gale_active:
            self.gale_count += 1
            message = get_gale_message(self.gale_count, self.current_bet)
            gale_message_id = await send_telegram_message(message)
            if gale_message_id:
                self.gale_message_ids.append(gale_message_id)
            if self.gale_count >= self.max_gales:
                self.is_gale_active = False
                self.is_red = True
            return

        if self.is_red:
            scoreboard.record_loss()
            await send_telegram_message(is_loss=True)
            await send_telegram_message(scoreboard.generate_scoreboard_message(), buttons=[LINK_MESSAGE_SCOREBOARD_BUTTON])
            await self.delete_gale_messages()
            await self.reset_state(wait_after_gale=True)
            return

    async def delete_gale_messages(self):
        # Delete all gale-related messages
        for message_id in self.gale_message_ids:
            try:
                await bot.delete_message(chat_id=TELEGRAM_CHANNEL_ID, message_id=message_id)
            except TelegramError as e:
                print(f"❌ Failed to delete gale message with ID {message_id}: {e}")
        self.gale_message_ids.clear()

    async def reset_state(self, wait_after_gale=False):
        # Reset state variables for the next betting cycle
        self.is_entry_allowed = True
        self.is_green = False
        self.is_gale_active = False
        self.is_red = False
        self.current_strategy = None
        self.current_bet = None
        self.gale_count = 0
        self.prepare_message_sent = False
        self.prepare_message_id = None
        self.gale_message_ids.clear()
        self.wait_after_gale = wait_after_gale

    async def request_stop(self):
        # Request to stop the bot after current cycle
        self.stop_requested = True

def sync_fetch_results(driver, main_window):
    # Synchronously fetch results using Selenium
    try:
        driver.switch_to.window(main_window)

        iframe_paths = [
            '/html/body/div[2]/div[1]/div[3]/div/div/div/div[2]/div[2]/div/iframe',
            '/html/body/iframe',
            '/html/body/div[5]/div[2]/iframe'
        ]

        for path in iframe_paths:
            try:
                iframe = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, path)))
                driver.switch_to.frame(iframe)
                body_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, 'body')))
                webdriver.ActionChains(driver).move_to_element_with_offset(
                    body_element, random.randint(1, 10), random.randint(1, 10)
                ).click().perform()
            except TimeoutException:
                continue

        target_xpath = '/html/body/div[4]/div/div/div[2]/div[6]/div/div[1]/div/div/div'
        result_element = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, target_xpath)))

        results_text = result_element.text
        results = results_text.split()[::-1][:3][::-1]
        return {"results": results}

    except NoSuchElementException as e:
        message = f"❌ Element not found: {e}\n{traceback.format_exc()}"
        print(message)
        return {"error": message}
    except TimeoutException as e:
        message = f"❌ Timeout while waiting for an element: {e}\n{traceback.format_exc()}"
        print(message)
        return {"error": message}
    except Exception as e:
        message = f"❌ General error occurred: {e}\n{traceback.format_exc()}"
        print(message)
        return {"error": message}
    finally:
        driver.switch_to.default_content()

async def async_fetch_results(executor, driver, main_window):
    # Asynchronously fetch results using a thread executor
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(executor, sync_fetch_results, driver, main_window)

async def schedule_restart():
    # Schedule a daily restart at a specific time
    while True:
        now = datetime.datetime.now()
        target_time = now.replace(hour=0, minute=0, second=0, microsecond=0)
        if now >= target_time:
            target_time += datetime.timedelta(days=1)

        sleep_duration = (target_time - now).total_seconds()
        await asyncio.sleep(sleep_duration)

        print("Restarting bot...")
        await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=CLOSE_STICKER_ID)
        os.execv(sys.executable, ['python'] + sys.argv)

async def main():
    # Main function to start the bot
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--mute-audio')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    driver.implicitly_wait(10)

    try:
        driver.get('https://www.bettilt504.com/pt/game/bac-bo/real')
        try:
            login_modal = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CLASS_NAME, 'modal-content')))
            username_field = login_modal.find_element(By.XPATH, '//input[@type="text" or @name="username"]')
            password_field = login_modal.find_element(By.XPATH, '//input[@type="password" or @name="password"]')
            username_field.send_keys(LOGIN_USERNAME)
            password_field.send_keys(LOGIN_PASSWORD)
            login_button = login_modal.find_element(By.XPATH, '//button[contains(@class, "styles__Button") and @type="submit"]')
            login_button.click()
            WebDriverWait(driver, 30).until(EC.invisibility_of_element((By.CLASS_NAME, 'modal-dialog')))
        except TimeoutException:
            pass
        
        main_window = driver.window_handles[0]

        # Define betting strategies
        strategies = [
            {'pattern': ['P', 'P', 'P'], 'bet': 'B'},
            {'pattern': ['B', 'B', 'B'], 'bet': 'P'},
            {'pattern': ['B', 'B', 'P'], 'bet': 'P'},
            {'pattern': ['P', 'P', 'B'], 'bet': 'B'},
        ]

        betting_strategy = BettingStrategy(strategies=strategies, max_gales=MAX_GALES)
        
        await bot.send_sticker(chat_id=TELEGRAM_CHANNEL_ID, sticker=OPEN_STICKER_ID)

        prev_results = []
        
        executor = ThreadPoolExecutor(max_workers=1)
        betting_strategy.can_check_patterns = False
        initial_results_required = 3

        # Run bot loop and schedule restart concurrently
        await asyncio.gather(
            run_bot_loop(executor, driver, main_window, betting_strategy, initial_results_required, prev_results),
            schedule_restart()
        )

    except KeyboardInterrupt:
        pass
    except Exception as e:
        message = f"❌ An unexpected error occurred: {e}"
        print(message)
    finally:
        driver.quit()

async def run_bot_loop(executor, driver, main_window, betting_strategy, initial_results_required, prev_results):
    # Main loop to monitor results and execute bets
    while True:
        result = await async_fetch_results(executor, driver, main_window)

        if "error" in result:
            await asyncio.sleep(5)
            continue

        results_list = result.get("results", [])

        if not results_list:
            await asyncio.sleep(5)
            continue

        if results_list != prev_results:
            prev_results = results_list

            if len(prev_results) >= initial_results_required:
                betting_strategy.can_check_patterns = True

            if betting_strategy.can_check_patterns:
                await betting_strategy.execute_strategy(results_list)

        if betting_strategy.stop_requested:
            break

        await asyncio.sleep(5)

if __name__ == "__main__":
    asyncio.run(main())
