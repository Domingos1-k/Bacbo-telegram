# BacBo Telegram Betting Bot

This repository contains a Python-based betting bot for the Bac Bo game that monitors game results, sends Telegram notifications, and uses specific betting strategies to automate bets. The bot integrates with Telegram to provide real-time alerts and updates, including scoreboard details and bet outcomes.

## Features

-   **Automated Bet Execution:** Uses custom strategies to identify betting patterns and automatically places bets accordingly.
-   **Telegram Integration:** Sends notifications, bet instructions, and updates to a specified Telegram channel.
-   **Daily Restart:** The bot is scheduled to restart daily to maintain stability.
-   **Custom Betting Strategies:** You can define your own patterns and betting behaviors.
-   **Scoreboard Tracking:** Tracks wins, losses, and calculates assertivity (win rate).
-   **Docker Support:** Easily deployable using Docker.

## Prerequisites

-   Python 3.10
-   Google Chrome & Chromedriver
-   Selenium
-   A Telegram bot token and channel ID
-   Docker (optional for containerized deployment)

## Installation

1. **Clone the repository:**

    ```sh
    git clone https://github.com/yourusername/telegram-betting-bot.git
    cd telegram-betting-bot
    ```

2. **Set up environment variables:**
   Create a `.env` file in the root directory with the following content (you can use the `.env-example` file as a reference):

    ```env
    TELEGRAM_BOT_TOKEN=7863883528:AAHGnhnA8NXqr5cdxX6HJazpyJbPIVjceQM
    TELEGRAM_CHANNEL_ID=-1002524967888
    WIN_STICKER_ID=your_win_sticker_id
    LOSS_STICKER_ID=your_loss_sticker_id
    CLOSE_STICKER_ID=your_close_sticker_id
    OPEN_STICKER_ID=your_open_sticker_id
    LOGIN_USERNAME=your_login_username
    LOGIN_PASSWORD=your_login_password
    ```

    Replace the placeholders with your actual Telegram bot token, channel ID, stickers, and login credentials.

3. **Install dependencies:**
   Make sure you have `pip` installed, then run:

    ```sh
    pip install -r requirements.txt
    ```

4. **Install Google Chrome and Chromedriver:**
   This bot uses Selenium, which requires Chrome and Chromedriver:

    - Chrome: [Download here](https://www.google.com/chrome/)
    - Chromedriver: Make sure it matches the installed Chrome version. [Download here](https://sites.google.com/chromium.org/driver/)

5. **Run the bot:**
    ```sh
    python main.py
    ```

## Running with Docker

1. **Build the Docker image:**

    ```sh
    docker build -t telegram-betting-bot .
    ```

2. **Run the Docker container:**
    ```sh
    docker run -d --env-file .env --name betting-bot telegram-betting-bot
    ```

## Configuration

### Betting Strategies

The bot uses customizable betting strategies defined in the `strategies` variable. Each strategy consists of:

-   **Pattern:** The sequence to match before placing a bet.
-   **Bet:** The action to take if the pattern is matched.

For example:

```python
strategies = [
    {'pattern': ['P', 'P', 'P'], 'bet': 'B'},
    {'pattern': ['B', 'B', 'B'], 'bet': 'P'}, 
    {'pattern': ['P', 'B', 'P', 'B', 'P', 'B'], 'bet': 'B'},
    {'pattern': ['B', 'P', 'B', 'P,' 'B', 'P'], 'bet': 'P'}
  
]
```

-   `'P'` and `'B'` represent different bet options.

### Scoreboard Tracking

The bot tracks the number of wins, losses, and calculates the assertivity rate (win rate). The scoreboard is displayed after each bet, and updates are sent to the Telegram channel.

### Daily Restart

To ensure the bot runs smoothly, it automatically restarts daily at a predefined time. You can modify the restart time in the `schedule_restart` function in `main.py`.

## Usage

-   The bot will continuously monitor the Bac Bo game results and apply the betting strategy as defined.
-   Alerts are sent to the specified Telegram channel, including bet instructions, win/loss notifications, and scoreboard updates.
-   Stickers are sent for different events (e.g., start, win, loss) if configured.

## Important Notes

-   **Gambling Disclaimer:** This bot is intended for educational purposes only. Betting involves risks, and the bot does not guarantee winning results.
-   **Telegram API Limits:** Make sure not to exceed Telegram's rate limits to avoid being blocked.
-   **Use Responsibly:** Automating bets can lead to significant financial loss. Use at your own risk.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Contributing

Feel free to open issues or submit pull requests if you have any improvements or suggestions for the bot.
