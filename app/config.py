from dataclasses import dataclass
import os

from dotenv import load_dotenv


load_dotenv()


@dataclass(frozen=True)
class Settings:
    mt5_path: str
    mt5_login: int
    mt5_password: str
    mt5_server: str
    mt5_symbol: str
    mt5_magic: int
    environment: str


def load_settings() -> Settings:
    required = [
        "MT5_PATH",
        "MT5_LOGIN",
        "MT5_PASSWORD",
        "MT5_SERVER",
    ]

    missing = [name for name in required if not os.getenv(name)]

    if missing:
        raise RuntimeError(
            f"Missing required environment variables: {', '.join(missing)}"
        )

    return Settings(
        mt5_path=os.environ["MT5_PATH"],
        mt5_login=int(os.environ["MT5_LOGIN"]),
        mt5_password=os.environ["MT5_PASSWORD"],
        mt5_server=os.environ["MT5_SERVER"],
        mt5_symbol=os.getenv("MT5_SYMBOL", "XAUUSD"),
        mt5_magic=int(os.getenv("MT5_MAGIC", "701001")),
        environment=os.getenv("JEV01_ENV", "development"),
    )