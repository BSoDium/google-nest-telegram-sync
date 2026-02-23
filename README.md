
# Google Nest camera clips - Telegram channel sync

This project is a fork of [@TamirMa's repository](https://github.com/TamirMa/nest-telegram-sync), implementing support for python 3.13, fixing some scheduling bugs, as well as exposing the timezone as a configuration option.

## Features

- Get list of **Google Home devices through HomeGraph**
- Retrieve recent **Google Nest events**
- Download **full-quality Google Nest video clips**
- Send those clips to a Telegram channel


## Usage:

- Install the required dependencies:
  ```bash
    pip install -r requirements.txt
  ```

- Get a Google "Master Token", using the [ha-google-home_get-token](https://hub.docker.com/r/breph/ha-google-home_get-token) docker image.

  ```bash
    docker run --rm -it breph/ha-google-home_get-token
  ```
> [!TIP]  
> The image will prompt you to provide an app password, which you can retrieve by creating a new app on your [Google account app passwords page](https://myaccount.google.com/apppasswords).

> [!WARNING]  
> The app password is NOT your Google account's password. It is a unique password generated for the app you are creating.

- Create a .env file with the following contents:

  ```dotenv
  GOOGLE_MASTER_TOKEN="aas_..."
  GOOGLE_USERNAME="youremailaddress@gmail.com"
  TELEGRAM_BOT_TOKEN="token..."
  TELEGRAM_CHANNEL_ID="-100..."
  TIMEZONE="US/Central"
  ```

> [!NOTE]
> To retrieve your telegram bot token, create your telegram bot using [@BotFather](https://t.me/botfather).
> 
> If the channel you want to sync the videos to is private, use [@username_to_id_bot](https://t.me/username_to_id_bot) to get the channel's ID. Public channels expose their id in the URL, making this step unnecessary.
> 
> All available timezones can be found [in this gist by heyalexej](https://gist.github.com/heyalexej/8bf688fd67d7199be4a1682b3eec7568)
  

- Finally, run:

  ```bash
    python3 main.py
  ```

## Credits:

- [original repository](https://github.com/TamirMa/nest-telegram-sync) from which this project is forked
- [glocaltokens](https://github.com/leikoilja/glocaltokens) for the Google Home Graph API
- [ha-google-home_get-token](https://hub.docker.com/r/breph/ha-google-home_get-token) for the Google Master Token retrieval process
- [python-telegram-bot](https://python-telegram-bot.org/) for the Telegram API
