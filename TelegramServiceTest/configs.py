import os


class SpeakerConfigs:
    url: str = os.getenv("API_SPEAKER_URL")


SPEAKER_CONFIGS = SpeakerConfigs()


class BotConfigs:
    token: str = os.getenv("BOT_TOKEN")


BOT_CONFIGS = BotConfigs()
