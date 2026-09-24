#!/usr/bin/env python3
"""Real-time Wi-Fi CSI Presence Detection live monitor."""

import argparse
import shutil
import sys
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from wifi_csi.acquisition.realtime import (
    RealtimeCSIInference,
    format_duration,
    make_bar,
    make_bipolar_gauge,
)

# ANSI Colors and Formatting
RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"

# Foreground Colors
FG_RED = "\033[31m"
FG_GREEN = "\033[32m"
FG_YELLOW = "\033[33m"
FG_BLUE = "\033[34m"
FG_MAGENTA = "\033[35m"
FG_CYAN = "\033[36m"
FG_WHITE = "\033[37m"
FG_GRAY = "\033[90m"

# Bright Foreground Colors
FG_BRIGHT_RED = "\033[91m"
FG_BRIGHT_GREEN = "\033[92m"
FG_BRIGHT_YELLOW = "\033[93m"
FG_BRIGHT_CYAN = "\033[96m"
FG_BRIGHT_WHITE = "\033[97m"

# Background Colors
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_DARK = "\033[100m"

# Terminal Control
CURSOR_HOME = "\033[H"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"
CLEAR_LINE = "\033[K"
CLEAR_SCREEN = "\033[2J"

# Constants
MAX_HISTORY = 10  # Number of recent predictions to display in the timeline


class TerminalDashboard:

    """Renders a live, flicker-free terminal dashboard for CSI presence detection."""

    def __init__(
        self,
        engine: RealtimeCSIInference,
        refresh_rate_hz: float = 4.0,
        plain_mode: bool = False,
    ):
        self.engine = engine
        self.refresh_interval = 1.0 / max(0.5, refresh_rate_hz)
        self.plain_mode = plain_mode or (not sys.stdout.isatty())
        self.history: deque[dict[str, Any]] = deque(maxlen=MAX_HISTORY)
        self.start_time = time.time()
        self._first_render = True

    def run(self) -> None:
        """Main execution loop displaying predictions live."""
        if not self.plain_mode:
            sys.stdout.write(CURSOR_HIDE)
            sys.stdout.write(CLEAR_SCREEN + CURSOR_HOME)
            sys.stdout.flush()

        try:
            self.engine.start()
            while True:
                res = self.engine.predict_latest()
                if res.get("status") == "ready":
                    self.history.appendleft(res)

                if self.plain_mode:
                    self._render_plain(res)
                else:
                    self._render_interactive(res)

                time.sleep(self.refresh_interval)

        except KeyboardInterrupt:
            pass
        finally:
            self._cleanup()

    def _render_plain(self, res: dict[str, Any]) -> None:
        """Simple line-by-line output for scripts, pipes, or non-tty environments."""
        now_str = datetime.now(timezone.utc).astimezone().strftime("%Y-%m-%d %H:%M:%S")
        if res.get("status") == "buffering":
            count = res.get("sample_count", 0)
            target = res.get("target_samples", 0)
            span = res.get("time_span", 0.0)
            rate = res.get("packet_rate_hz", 0.0)
            mode = self.engine.window_mode.upper()
            print(f"[{now_str}] BUFFERING ({mode}): {count}/{target} packets ({span:.1f}/2.0s, {rate:4.1f} Hz)")
        else:
            label = res["label"].upper()
            p_occ = res["prob_occupied"] * 100.0
            p_emp = res["prob_empty"] * 100.0
            rssi = res.get("rssi")
            rate = res.get("packet_rate_hz", 0.0)
            pkts = res.get("sample_count", 0)
            span = res.get("actual_span_s", self.engine.window_seconds)
            mode = res.get("window_mode", self.engine.window_mode).upper()
            print(
                f"[{now_str}] {label:8s} | Score: P(Occ)={p_occ:5.1f}% P(Emp)={p_emp:5.1f}% | "
                f"Window: {self.engine.window_seconds:.1f}s ({pkts} pkts, {span:.2f}s span, {mode}) | "
                f"RSSI: {rssi if rssi is not None else '--'} dBm | Rate: {rate:4.1f} Hz"
            )

    def _render_interactive(self, res: dict[str, Any], show_primary_status: bool = False) -> None:
        """Render high-contrast, visually appealing live TUI in the terminal."""
        term_width = shutil.get_terminal_size((80, 24)).columns
        W = min(78, max(68, term_width - 2))
        inner_w = W - 2

        elapsed_str = format_duration(time.time() - self.start_time)
        status = res.get("status", "unknown")

        rate_hz = res.get("packet_rate_hz", 0.0)
        rssi = res.get("rssi")
        noise = res.get("noise_floor")
        snr = res.get("snr_db")
        pkts = res.get("sample_count", 0)
        actual_span = res.get("actual_span_s", res.get("time_span", 0.0))
        mode_str = self.engine.window_mode.upper()

        lines: list[str] = []

        # ── Header ──────────────────────────────────────────────────────────
        lines.append(f"{FG_CYAN}╔{'═' * inner_w}╗{RESET}")
        header_title = "WI-FI CSI REAL-TIME PRESENCE DETECTION"
        lines.append(
            f"{FG_CYAN}║{BOLD}{FG_BRIGHT_WHITE}{header_title:^{inner_w}}{RESET}{FG_CYAN}║{RESET}"
        )
        model_info = f"Model: {self.engine.model_name.upper()}  │  Window: {self.engine.window_seconds:.1f}s ({mode_str})  │  Port: {self.engine.port}"
        lines.append(
            f"{FG_CYAN}║{DIM}{FG_WHITE}{model_info:^{inner_w}}{RESET}{FG_CYAN}║{RESET}"
        )
        lines.append(f"{FG_CYAN}╠{'═' * inner_w}╣{RESET}")

        # ── Primary Status Banner ───────────────────────────────────────────
        lines.append(f"{FG_CYAN}║{' ' * inner_w}║{RESET}")
        active_eval = res if status == "ready" else res.get("last_result")

        if active_eval is None and status == "buffering":
            buf_str = f"INITIALIZING 2.0s BUFFER ({pkts}/{res.get('target_samples', self.engine.min_samples)} samples, {actual_span:.1f}/2.0s)"
            lines.append(
                f"{FG_CYAN}║{BOLD}{FG_BRIGHT_YELLOW}   ┌{'─' * (inner_w - 6)}┐ {RESET}{FG_CYAN}║{RESET}"
            )
            lines.append(
                f"{FG_CYAN}║{BOLD}{FG_BRIGHT_YELLOW}   │{buf_str:^{inner_w - 6}}│ {RESET}{FG_CYAN}║{RESET}"
            )
            prog_bar = make_bar(res.get("progress_ratio", 0.0), width=inner_w - 30)
            prog_str = f"Accumulating 2.0s: [{prog_bar}]"
            lines.append(
                f"{FG_CYAN}║{DIM}{FG_YELLOW}   │{prog_str:^{inner_w - 6}}│ {RESET}{FG_CYAN}║{RESET}"
            )
            lines.append(
                f"{FG_CYAN}║{BOLD}{FG_BRIGHT_YELLOW}   └{'─' * (inner_w - 6)}┘ {RESET}{FG_CYAN}║{RESET}"
            )
        else:
            is_occupied = active_eval["prediction"] == 1
            if is_occupied:
                tag = "STATUS: OCCUPIED  [PRESENCE DETECTED]"
                color = FG_BRIGHT_RED
                border_color = FG_RED
            else:
                tag = "STATUS: EMPTY  [NO PRESENCE DETECTED]"
                color = FG_BRIGHT_GREEN
                border_color = FG_GREEN

            lines.append(
                f"{FG_CYAN}║ {border_color}┌{'─' * (inner_w - 6)}┐{RESET}   {FG_CYAN}║{RESET}"
            )
            lines.append(
                f"{FG_CYAN}║ {border_color}│{BOLD}{color}{tag:^{inner_w - 6}}{RESET}{border_color}│{RESET}   {FG_CYAN}║{RESET}"
            )
            eval_pkts = active_eval.get("sample_count", pkts)
            eval_span = active_eval.get("actual_span_s", 2.0)
            sub_tag = (
                f"Confidence: {active_eval['confidence'] * 100.0:5.1f}%  │  "
                f"Window: {active_eval['window_seconds']:.1f}s ({eval_pkts} pkts, {eval_span:.2f}s span, {mode_str})"
            )
            lines.append(
                f"{FG_CYAN}║ {border_color}│{DIM}{FG_WHITE}{sub_tag:^{inner_w - 6}}{RESET}{border_color}│{RESET}   {FG_CYAN}║{RESET}"
            )
            lines.append(
                f"{FG_CYAN}║ {border_color}└{'─' * (inner_w - 6)}┘{RESET}   {FG_CYAN}║{RESET}"
            )

        lines.append(f"{FG_CYAN}║{' ' * inner_w}║{RESET}")
        lines.append(f"{FG_CYAN}╠{'─' * inner_w}╣{RESET}")

        # ── Probability Gauge Section ───────────────────────────────────────
        lines.append(
            f"{FG_CYAN}║  {BOLD}{FG_BRIGHT_WHITE}PREDICTION PROBABILITY SCORES:{' ' * (inner_w - 32)}║{RESET}"
        )
        bar_w = 34
        if active_eval is not None:
            p_occ = active_eval["prob_occupied"]
            p_emp = active_eval["prob_empty"]

            # Empty Bar
            emp_bar = make_bar(p_emp, width=bar_w)
            emp_color = FG_BRIGHT_GREEN if p_emp >= 0.5 else FG_GRAY
            emp_line = f"  Empty    : {p_emp * 100.0:5.1f}%  [{emp_color}{emp_bar}{RESET}]"
            padding_emp = inner_w - len(emp_line) + len(emp_color) + len(RESET)
            lines.append(f"{FG_CYAN}║{emp_line}{' ' * max(0, padding_emp)}{FG_CYAN}║{RESET}")

            # Occupied Bar
            occ_bar = make_bar(p_occ, width=bar_w)
            occ_color = FG_BRIGHT_RED if p_occ >= 0.5 else FG_GRAY
            occ_line = f"  Occupied : {p_occ * 100.0:5.1f}%  [{occ_color}{occ_bar}{RESET}]"
            padding_occ = inner_w - len(occ_line) + len(occ_color) + len(RESET)
            lines.append(f"{FG_CYAN}║{occ_line}{' ' * max(0, padding_occ)}{FG_CYAN}║{RESET}")

            # Bipolar Balance Gauge
            bipolar_bar = make_bipolar_gauge(p_occ, width=bar_w)
            bipolar_line = f"  Balance  : EMPTY   [{FG_CYAN}{bipolar_bar}{RESET}]  OCCUPIED"
            padding_bi = inner_w - len(bipolar_line) + len(FG_CYAN) + len(RESET)
            lines.append(f"{FG_CYAN}║{bipolar_line}{' ' * max(0, padding_bi)}{FG_CYAN}║{RESET}")
        else:
            empty_bar = "░" * bar_w
            lines.append(
                f"{FG_CYAN}║  Empty    :   --.-%  [{FG_GRAY}{empty_bar}{RESET}]{' ' * (inner_w - 58)}║{RESET}"
            )
            lines.append(
                f"{FG_CYAN}║  Occupied :   --.-%  [{FG_GRAY}{empty_bar}{RESET}]{' ' * (inner_w - 58)}║{RESET}"
            )

        lines.append(f"{FG_CYAN}╠{'─' * inner_w}╣{RESET}")

        # ── Telemetry & Signal Health ────────────────────────────────────────
        lines.append(
            f"{FG_CYAN}║  {BOLD}{FG_BRIGHT_WHITE}TELEMETRY & HARDWARE HEALTH:{' ' * (inner_w - 30)}║{RESET}"
        )
        rate_color = FG_BRIGHT_GREEN if rate_hz >= 25.0 else (FG_YELLOW if rate_hz > 5.0 else FG_RED)
        rssi_str = f"{rssi:.0f} dBm" if rssi is not None else "--"
        noise_str = f"{noise:.0f} dBm" if noise is not None else "--"
        snr_str = f"+{snr:.0f} dB" if snr is not None else "--"
        disturb_val = active_eval.get("disturbance", 0.0) if active_eval else 0.0
        disturb_str = f"{disturb_val:.4f}" if active_eval else "--"

        t_line1 = f"  Packet Rate : {rate_color}{rate_hz:5.1f} Hz{RESET} (Nominal 29.0)   │ RSSI : {rssi_str:8s}"
        pad1 = inner_w - len(t_line1) + len(rate_color) + len(RESET)
        lines.append(f"{FG_CYAN}║{t_line1}{' ' * max(0, pad1)}{FG_CYAN}║{RESET}")

        t_line2 = f"  Window Logic: {self.engine.window_seconds:.1f}s ({mode_str})             │ Noise: {noise_str:8s} (SNR: {snr_str})"
        pad2 = inner_w - len(t_line2)
        lines.append(f"{FG_CYAN}║{t_line2}{' ' * max(0, pad2)}{FG_CYAN}║{RESET}")

        t_line3 = f"  CSI Disturbance (Mean Var): {disturb_str:8s}     │ Window Span : {actual_span:.2f}s ({pkts} pkts)"
        pad3 = inner_w - len(t_line3)
        lines.append(f"{FG_CYAN}║{t_line3}{' ' * max(0, pad3)}{FG_CYAN}║{RESET}")
        lines.append(f"{FG_CYAN}╠{'─' * inner_w}╣{RESET}")


        # ── Recent Predictions Log (Timeline) ────────────────────────────────
        lines.append(
            f"{FG_CYAN}║ {BOLD}{FG_BRIGHT_WHITE}RECENT INFERENCE LOG (Last {len(self.history)} events):{' ' * (inner_w - 38)}║{RESET}"
        )
        if not self.history:
            lines.append(
                f"{FG_CYAN}║  {DIM}{FG_GRAY}No predictions generated yet...{' ' * (inner_w - 33)}{RESET}{FG_CYAN}║{RESET}"
            )
        else:
            for item in list(self.history)[:MAX_HISTORY]:
                t_event = (
                    datetime.fromtimestamp(item["timestamp"], tz=timezone.utc)
                    .astimezone()
                    .strftime("%H:%M:%S")
                )
                pred_label = item["label"].upper()

                p_c = item["prob_occupied"] * 100.0
                p_e = item["prob_empty"] * 100.0
                tag_col = FG_BRIGHT_RED if pred_label == "OCCUPIED" else FG_BRIGHT_GREEN
                rssi_ev = f"{item.get('rssi', '--'):>3.0f} dBm" if item.get("rssi") is not None else "  -- dBm"
                row = (
                    f"  {DIM}{t_event}{RESET}  [{tag_col}{pred_label:^8s}{RESET}] "
                    f"P(Occ)={p_c:5.1f}%  P(Emp)={p_e:5.1f}% │ {rssi_ev} │ {item['sample_count']} pkts"
                )
                pad_r = inner_w - len(row) + (len(tag_col) + len(RESET) + len(DIM) + len(RESET))
                lines.append(f"{FG_CYAN}║{row}{' ' * max(0, pad_r)}{FG_CYAN}║{RESET}")

        lines.append(f"{FG_CYAN}╠{'═' * inner_w}╣{RESET}")

        # ── Footer / Run Stats ───────────────────────────────────────────────
        total_inf = max(1, self.engine.total_inferences)
        occ_pct = (self.engine.occupied_count / total_inf) * 100.0 if self.engine.total_inferences else 0.0
        emp_pct = (self.engine.empty_count / total_inf) * 100.0 if self.engine.total_inferences else 0.0

        footer = (
            f"Elapsed: {elapsed_str} │ Inferences: {self.engine.total_inferences} │ "
            f"Occ: {occ_pct:4.1f}% │ Emp: {emp_pct:4.1f}%"
        )
        lines.append(f"{FG_CYAN}║{DIM}{FG_WHITE}{footer:^{inner_w}}{RESET}{FG_CYAN}║{RESET}")
        lines.append(f"{FG_CYAN}╚{'═' * inner_w}╝{RESET}")
        lines.append(f"{DIM}Press [Ctrl+C] to stop live acquisition cleanly.{CLEAR_LINE}{RESET}")

        # In-place overwrite using cursor home
        frame_text = CURSOR_HOME + "\n".join(f"{line}{CLEAR_LINE}" for line in lines)
        sys.stdout.write(frame_text)
        sys.stdout.flush()

    def _cleanup(self) -> None:
        """Gracefully restore terminal settings and print summary report."""
        self.engine.stop()
        if not self.plain_mode:
            sys.stdout.write(CURSOR_SHOW)
            sys.stdout.write("\n\n")
            sys.stdout.flush()

        duration = time.time() - self.start_time
        total_inf = self.engine.total_inferences
        print(f"{BOLD}{FG_CYAN}═══════════════════════════════════════════════════════════════{RESET}")
        print(f"{BOLD}  WI-FI CSI REAL-TIME PRESENCE SESSION SUMMARY{RESET}")
        print(f"{BOLD}{FG_CYAN}═══════════════════════════════════════════════════════════════{RESET}")
        print(f"  Duration           : {format_duration(duration)} ({duration:.1f} s)")
        print(f"  Model Used         : {self.engine.model_name.upper()} (Optimal pipeline)")
        print(f"  Serial Port        : {self.engine.port} @ {self.engine.baudrate} bps")
        print(f"  Packets Received   : {self.engine.total_packets_received:,}")
        print(f"  Average Rate       : {(self.engine.total_packets_received / max(0.1, duration)):.1f} Hz")
        print(f"  Total Inferences   : {total_inf:,}")
        if total_inf > 0:
            occ_ratio = (self.engine.occupied_count / total_inf) * 100.0
            emp_ratio = (self.engine.empty_count / total_inf) * 100.0
            print(
                f"  Empty Predictions  : {self.engine.empty_count:5d} ({emp_ratio:5.1f}%)"
            )
            print(
                f"  Occupied Predictions: {self.engine.occupied_count:5d} ({occ_ratio:5.1f}%)"
            )
        print(f"{BOLD}{FG_CYAN}═══════════════════════════════════════════════════════════════{RESET}\n")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Real-time Wi-Fi CSI Presence Detection live monitor.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--port",
        type=str,
        default="auto",
        help="Serial port device (e.g. /dev/ttyUSB0, /dev/ttyACM0, or 'auto')",
    )
    parser.add_argument(
        "--baud",
        type=int,
        default=921600,
        help="Serial communication baudrate",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model bundle name to use (default: best model from evaluation_report.json)",
    )
    parser.add_argument(
        "--window",
        type=float,
        default=2.0,
        help="Time window in seconds for feature extraction",
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=4.0,
        help="Display update frequency in Hz",
    )
    parser.add_argument(
        "--threshold",
        type=float,
        default=0.5,
        help="Decision threshold for occupied classification (0.0 - 1.0)",
    )
    parser.add_argument(
        "--mode",
        type=str,
        default="sliding",
        choices=["sliding", "tumbling"],
        help="Window evaluation mode: 'sliding' (continuous 2.0s rolling window) or 'tumbling' (discrete non-overlapping 2.0s windows matching offline training)",
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        help="Disable interactive terminal dashboard and stream plain logs",
    )

    args = parser.parse_args()

    # Locate repo root
    repo_root = Path(__file__).resolve().parent.parent

    try:
        engine = RealtimeCSIInference(
            port=None if args.port == "auto" else args.port,
            baudrate=args.baud,
            model_name= args.model,
            window_seconds=args.window,
            window_mode=args.mode,
            threshold=args.threshold,
            repo_root=repo_root,
        )
        dashboard = TerminalDashboard(
            engine=engine,
            refresh_rate_hz=args.rate,
            plain_mode=args.plain,
        )
    except Exception as e:  # noqa: BLE001
        print(f"\n{BOLD}{FG_RED}[ERROR] Failed to initialize real-time engine:{RESET} {e}")
        sys.exit(1)



    dashboard.run()


if __name__ == "__main__":
    main()
