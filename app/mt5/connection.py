from __future__ import annotations

from pathlib import Path

import MetaTrader5 as mt5

from app.config import Settings


class MT5Connection:
    def __init__(self, settings: Settings):
        self.settings = settings

    def connect(self) -> None:
        terminal_path = Path(self.settings.mt5_path).resolve()
        expected_directory = terminal_path.parent

        if not mt5.initialize(path=str(terminal_path)):
            raise RuntimeError(
                f"MT5 initialization failed: {mt5.last_error()}"
            )

        terminal = mt5.terminal_info()

        if terminal is None:
            self.shutdown()
            raise RuntimeError("Unable to read MT5 terminal information.")

        actual_directory = Path(terminal.path).resolve()

        if actual_directory != expected_directory:
            self.shutdown()
            raise RuntimeError(
                "MT5 terminal path mismatch.\n"
                f"Expected directory: {expected_directory}\n"
                f"Actual directory:   {actual_directory}"
            )

        if not mt5.login(
            self.settings.mt5_login,
            password=self.settings.mt5_password,
            server=self.settings.mt5_server,
        ):
            error = mt5.last_error()
            self.shutdown()
            raise RuntimeError(f"MT5 login failed: {error}")

        account = mt5.account_info()

        if account is None:
            self.shutdown()
            raise RuntimeError("Unable to read MT5 account information.")

        if int(account.login) != self.settings.mt5_login:
            self.shutdown()
            raise RuntimeError(
                f"Account mismatch. "
                f"Expected {self.settings.mt5_login}, "
                f"got {account.login}."
            )

        if account.server != self.settings.mt5_server:
            self.shutdown()
            raise RuntimeError(
                f"Server mismatch. "
                f"Expected {self.settings.mt5_server}, "
                f"got {account.server}."
            )

        if not mt5.symbol_select(
            self.settings.mt5_symbol,
            True,
        ):
            self.shutdown()
            raise RuntimeError(
                f"Unable to select symbol {self.settings.mt5_symbol}."
            )

    def terminal_info(self):
        return mt5.terminal_info()

    def account_info(self):
        return mt5.account_info()

    def symbol_info(self):
        return mt5.symbol_info(self.settings.mt5_symbol)

    def shutdown(self) -> None:
        mt5.shutdown()