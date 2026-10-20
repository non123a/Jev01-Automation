
from datetime import datetime
from zoneinfo import ZoneInfo
import time
from rich import box
from rich.live import Live
from rich.table import Table
from rich.console import Console

from app.config import load_settings
from app.mt5.connection import MT5Connection
from app.market.mt5_provider import MT5ExnessProvider
from app.market.bar_builder import MultiTimeframeBarBuilder
from app.liquidity.multi_swing_detector import MultiTimeframeSwingDetector
from app.liquidity.liquidity_map import LiquidityMap
from app.liquidity.candle_sweep_engine import CandleSweepEngine


TIMEFRAMES = ("1M", "5M", "15M", "1H")
TIMEFRAME_HISTORY = {tf: 200 for tf in TIMEFRAMES}
NEW_YORK_TZ = ZoneInfo("America/New_York")

console = Console()


def format_time(timestamp):
    """Display New York time without timezone labels."""
    if timestamp is None:
        return "--:--:--"

    if timestamp.tzinfo is None:
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    return timestamp.astimezone(NEW_YORK_TZ).strftime(
        "%Y-%m-%d %H:%M:%S"
    )


def get_tick_price(tick):
    """
    Adapt this helper if MT5ExnessProvider returns a custom
    tick object with different field names.
    """
    def read(name):
        if isinstance(tick, dict):
            return tick.get(name)
        return getattr(tick, name, None)

    last = read("last")
    if last is not None and float(last) > 0:
        return float(last)

    bid = read("bid")
    ask = read("ask")

    if bid is not None and ask is not None:
        bid, ask = float(bid), float(ask)
        if bid > 0 and ask > 0:
            return (bid + ask) / 2

    for name in ("price", "close"):
        value = read(name)
        if value is not None and float(value) > 0:
            return float(value)

    return None


def level_value(level, name, default=None):
    if isinstance(level, dict):
        return level.get(name, default)
    return getattr(level, name, default)


def normalized_side(level):
    direction = str(level_value(level, "direction", "")).upper()

    if direction in ("HIGH", "LOW"):
        return direction

    return direction


def build_dashboard(
    symbol,
    current_price,
    price_time,
    latest_bars,
    liquidity_map,
    latest_event,
):
    root = Table.grid(expand=True)
    root.add_column(ratio=1)

    header = Table(box=box.SIMPLE, expand=True)
    header.add_column()
    header.add_column(justify="right")

    header.add_row(
        f"[bold cyan]JEV01-AUTOMATE[/bold cyan] | {symbol}",
        f"[green]LIVE[/green] | {format_time(price_time)}",
    )
    root.add_row(header)

    # --------------------------------------------------
    # LIVE PRICE
    # --------------------------------------------------
    price_table = Table(
        title="LIVE PRICE",
        box=box.ROUNDED,
        expand=True,
    )
    price_table.add_column("Snapshot time")
    price_table.add_column("Symbol")
    price_table.add_column("Price", justify="right")

    price_table.add_row(
        format_time(price_time),
        symbol,
        f"{current_price:.3f}" if current_price is not None else "Waiting...",
    )
    root.add_row(price_table)

    # # --------------------------------------------------
    # # LAST COMPLETED CANDLE PER TIMEFRAME
    # # --------------------------------------------------
    # bar_table = Table(
    #     title="LAST COMPLETED CANDLE",
    #     box=box.ROUNDED,
    #     expand=True,
    # )
    # bar_table.add_column("TF")
    # bar_table.add_column("Candle time")
    # bar_table.add_column("Open", justify="right")
    # bar_table.add_column("High", justify="right")
    # bar_table.add_column("Low", justify="right")
    # bar_table.add_column("Close", justify="right")

    # for tf in TIMEFRAMES:
    #     bar = latest_bars.get(tf)

    #     if bar is None:
    #         bar_table.add_row(tf, "--", "--", "--", "--", "--")
    #         continue

    #     bar_table.add_row(
    #         tf,
    #         format_time(bar.start),
    #         f"{bar.open:.3f}",
    #         f"{bar.high:.3f}",
    #         f"{bar.low:.3f}",
    #         f"{bar.close:.3f}",
    #     )

    # root.add_row(bar_table)

    # --------------------------------------------------
    # ACTIVE LIQUIDITY
    # --------------------------------------------------
    liquidity_table = Table(
        title="NEAREST ACTIVE LIQUIDITY",
        box=box.ROUNDED,
        expand=True,
    )
    liquidity_table.add_column("TF")
    liquidity_table.add_column("Active")
    liquidity_table.add_column("Nearest HIGH", justify="right")
    liquidity_table.add_column("High Candle (NY)")
    liquidity_table.add_column("Distance", justify="right")
    liquidity_table.add_column("Nearest LOW", justify="right")
    liquidity_table.add_column("Low Candle (NY)")
    liquidity_table.add_column("Distance", justify="right")

    all_levels = liquidity_map.active_levels()

    for tf in TIMEFRAMES:
        levels = [
            level for level in all_levels
            if level_value(level, "timeframe") == tf
        ]

        highs = [
            level for level in levels
            if normalized_side(level) == "HIGH"
        ]
        lows = [
            level for level in levels
            if normalized_side(level) == "LOW"
        ]

        # Nearest HIGH above price.
        highs_above = [
            level for level in highs
            if current_price is not None
            and float(level_value(level, "price")) > current_price
        ]
        nearest_high = min(
            highs_above,
            key=lambda level: float(level_value(level, "price")),
            default=None,
        )

        # Nearest LOW below price.
        lows_below = [
            level for level in lows
            if current_price is not None
            and float(level_value(level, "price")) < current_price
        ]
        nearest_low = max(
            lows_below,
            key=lambda level: float(level_value(level, "price")),
            default=None,
        )

        high_price = (
            float(level_value(nearest_high, "price"))
            if nearest_high is not None else None
        )
        low_price = (
            float(level_value(nearest_low, "price"))
            if nearest_low is not None else None
        )

        high_text = f"{high_price:.3f}" if high_price is not None else "--"
        low_text = f"{low_price:.3f}" if low_price is not None else "--"

        high_time = (
            nearest_high.candle_time.astimezone(NEW_YORK_TZ).strftime("%H:%M")
            if nearest_high is not None and nearest_high.candle_time is not None
            else "--"
        )

        low_time = (
            nearest_low.candle_time.astimezone(NEW_YORK_TZ).strftime("%H:%M")
            if nearest_low is not None and nearest_low.candle_time is not None
            else "--"
        )
        high_distance = (
            f"+{high_price - current_price:.3f}"
            if high_price is not None and current_price is not None
            else "--"
        )
        low_distance = (
            f"{current_price - low_price:.3f}"
            if low_price is not None and current_price is not None
            else "--"
        )

        # liquidity_table.add_row(
        #     tf,
        #     str(len(levels)),
        #     high_text,
        #     high_distance,
        #     low_text,
        #     low_distance,
        # )
        liquidity_table.add_row(
            tf,
            str(len(levels)),
            high_text,
            high_time,
            high_distance,
            low_text,
            low_time,
            low_distance,
        )
        # high_time = (
        #     format_time(nearest_high.candle_time)
        #     if nearest_high is not None and nearest_high.candle_time is not None
        #     else "--"
        # )

        # low_time = (
        #     format_time(nearest_low.candle_time)
        #     if nearest_low is not None and nearest_low.candle_time is not None
        #     else "--"
        # )

    root.add_row(liquidity_table)

    # --------------------------------------------------
    # MOST RECENT EVENT
    # --------------------------------------------------
    event_table = Table(
        title="LATEST LIQUIDITY EVENT",
        box=box.ROUNDED,
        expand=True,
    )
    event_table.add_column("Event")
    event_table.add_row(latest_event or "Waiting for a new event...")
    root.add_row(event_table)

    return root


def main():
    settings = load_settings()
    connection = MT5Connection(settings)

    provider = MT5ExnessProvider(settings, connection)
    bar_builder = MultiTimeframeBarBuilder()

    swing_detector = MultiTimeframeSwingDetector(strength=3)
    liquidity_map = LiquidityMap()

    candle_sweep_engine = CandleSweepEngine(
        lookback=10,
        strength_multiple=1.5,
    )

    latest_bars = {tf: None for tf in TIMEFRAMES}
    latest_event = "Historical warm-up in progress"
    current_price = None
    price_time = None

    live_timeframes_initialized = set()

    try:
        connection.connect()

        console.print(f"Account: {settings.mt5_login}")
        console.print(f"Symbol: {settings.mt5_symbol}")
        console.print("\nLoading historical bars...")

        # --------------------------------------------------
        # HISTORICAL WARM-UP
        # --------------------------------------------------
        for timeframe, count in TIMEFRAME_HISTORY.items():
            bars = provider.get_historical_bars(
                timeframe=timeframe,
                count=count,
            )

            console.print(
                f"{timeframe}: {len(bars)} completed bars loaded"
            )

            for bar in bars:
                latest_bars[timeframe] = bar

                swings = swing_detector.update(bar)

                for swing in swings:
                    liquidity_map.add_swing(swing)

                # Preserve the existing warm-up behavior.
                candle_sweep_engine.update(bar, [])

        console.print(
            f"Historical active liquidity: "
            f"{len(liquidity_map.active_levels())}"
        )
        console.print("Starting live dashboard. Press CTRL+C to stop.")

        # --------------------------------------------------
        # LIVE DASHBOARD
        # --------------------------------------------------
        last_dashboard_update = time.monotonic()
        with Live(
            build_dashboard(
                settings.mt5_symbol,
                current_price,
                price_time,
                latest_bars,
                liquidity_map,
                latest_event,
            ),
            console=console,
            refresh_per_second=1,
            screen=True,
        ) as live:

            for tick in provider.stream(interval_seconds=0.1):
                tick_price = get_tick_price(tick)

                if tick_price is not None:
                    current_price = tick_price
                    price_time = datetime.now(NEW_YORK_TZ)

                completed_bars = bar_builder.update(tick)

                for bar in completed_bars:
                    tf = bar.timeframe

                    # Do not process the first possibly partial live bar.
                    if tf not in live_timeframes_initialized:
                        live_timeframes_initialized.add(tf)
                        latest_event = (
                            f"Startup bar skipped | {tf} | "
                            f"{format_time(bar.start)}"
                        )
                        continue

                    latest_bars[tf] = bar

                    swings = swing_detector.update(bar)

                    for swing in swings:
                        liquidity_map.add_swing(swing)

                        latest_event = (
                            f"NEW LIQUIDITY | {swing.timeframe} | "
                            f"{swing.direction.upper()} | "
                            f"{swing.price:.3f} | "
                            f"{format_time(swing.timestamp)}"
                        )

                    sweeps = candle_sweep_engine.update(
                        bar,
                        liquidity_map.active_levels(),
                    )

                    for sweep in sweeps:
                        # Retain the existing sweep lifecycle.
                        liquidity_map.mark_swept(sweep.liquidity_id)

                        latest_event = (
                            f"CONFIRMED SWEEP | {sweep.timeframe} | "
                            f"{sweep.liquidity_direction.upper()} | "
                            f"level={sweep.liquidity_price:.3f} | "
                            f"type={sweep.confirmation_type} | "
                            f"confirmed={format_time(sweep.confirmed_at)}"
                        )

                # live.update(
                #     build_dashboard(
                #         settings.mt5_symbol,
                #         current_price,
                #         price_time,
                #         latest_bars,
                #         liquidity_map,
                #         latest_event,
                #     )
                # )
                now = time.monotonic()

                if now - last_dashboard_update >= 5:
                    live.update(
                        build_dashboard(
                            settings.mt5_symbol,
                            current_price,
                            price_time,
                            latest_bars,
                            liquidity_map,
                            latest_event,
                        )
                    )
                    last_dashboard_update = now

    except KeyboardInterrupt:
        console.print("\nStopped.")

        console.print("\nFINAL ACTIVE LIQUIDITY")
        for timeframe in TIMEFRAMES:
            levels = liquidity_map.levels_by_timeframe(timeframe)
            console.print(f"{timeframe}: {len(levels)} active levels")

    finally:
        connection.shutdown()


if __name__ == "__main__":
    main()
