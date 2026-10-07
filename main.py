from app.config import load_settings
from app.mt5.connection import MT5Connection
from app.market.mt5_provider import MT5ExnessProvider
from app.market.bar_builder import MultiTimeframeBarBuilder
from app.liquidity.multi_swing_detector import MultiTimeframeSwingDetector
from app.liquidity.liquidity_map import LiquidityMap

from app.liquidity.sweep_detector import SweepDetector
TIMEFRAMES = {
    "1M": 200,
    "5M": 200,
    "15M": 200,
    "1H": 200,
}


def main():

    settings = load_settings()

    connection = MT5Connection(settings)

    provider = MT5ExnessProvider(
        settings,
        connection,
    )

    bar_builder = MultiTimeframeBarBuilder()

    swing_detector = MultiTimeframeSwingDetector(
        strength=2
    )

    liquidity_map = LiquidityMap()
    sweep_detector = SweepDetector(
        tolerance=0.001
    )
    print("=" * 60)
    print("JEV01-AUTOMATE LIQUIDITY MAP")
    print("=" * 60)

    try:

        connection.connect()

        print(
            f"Account : {settings.mt5_login}"
        )

        print(
            f"Symbol  : {settings.mt5_symbol}"
        )

        # --------------------------------------------------
        # HISTORICAL WARM-UP
        # --------------------------------------------------

        print()
        print("Loading historical bars...")

        for timeframe, count in TIMEFRAMES.items():

            bars = provider.get_historical_bars(
                timeframe=timeframe,
                count=count,
            )

            print(
                f"{timeframe}: "
                f"{len(bars)} completed bars loaded"
            )

            for bar in bars:

                swings = swing_detector.update(
                    bar
                )

                for swing in swings:

                    liquidity_map.add_swing(
                        swing
                    )

        print()
        print(
            "Historical liquidity levels:"
        )

        for timeframe in TIMEFRAMES:

            levels = (
                liquidity_map
                .levels_by_timeframe(timeframe)
            )

            print(
                f"  {timeframe}: "
                f"{len(levels)} active levels"
            )

        print()
        print(
            f"Total active liquidity: "
            f"{len(liquidity_map.active_levels())}"
        )

        print()
        print("Starting live stream...")
        print("Press CTRL+C to stop.")
        print()

        # --------------------------------------------------
        # LIVE
        # --------------------------------------------------

        for tick in provider.stream(
            interval_seconds=0.1
        ):
            sweeps = sweep_detector.update(
                tick,
                liquidity_map
            )

            for sweep in sweeps:

                print(
                    f"LIQUIDITY SWEPT | "
                    f"{sweep.liquidity_timeframe} | "
                    f"{sweep.liquidity_direction.upper()} | "
                    f"level={sweep.liquidity_price:.3f} | "
                    f"sweep={sweep.sweep_price:.3f} | "
                    f"distance={sweep.distance_from_level:.3f}"
                )

            completed_bars = (
                bar_builder.update(tick)
            )

            for bar in completed_bars:

                swings = swing_detector.update(
                    bar
                )

                for swing in swings:

                    liquidity_map.add_swing(
                        swing
                    )

                    print(
                        f"NEW LIQUIDITY | "
                        f"{swing.timeframe} | "
                        f"{swing.direction.upper()} | "
                        f"{swing.price:.3f} | "
                        f"{swing.timestamp.isoformat()}"
                    )
        
    except KeyboardInterrupt:

        print()
        print("Stopped.")

        print()
        print("FINAL LIQUIDITY MAP")

        for timeframe in TIMEFRAMES:

            levels = (
                liquidity_map
                .levels_by_timeframe(timeframe)
            )

            print(
                f"{timeframe}: "
                f"{len(levels)} active levels"
            )

    finally:

        connection.shutdown()


if __name__ == "__main__":
    main()