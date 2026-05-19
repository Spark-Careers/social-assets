"""Windows toast notification on weekly-bundle completion."""

from __future__ import annotations

from pathlib import Path

try:
    from winotify import Notification, audio
    _AVAILABLE = True
except ImportError:
    _AVAILABLE = False


def notify_success(week_label: str, bundle_dir: Path,
                    csv_count: int, png_count: int) -> None:
    if not _AVAILABLE:
        print(f"[notify] (winotify unavailable) Bundle for {week_label} ready at {bundle_dir}")
        return
    n = Notification(
        app_id="Spark Careers",
        title=f"Spark Careers {week_label} bundle ready",
        msg=f"{png_count} visuals, {csv_count} CSVs in {bundle_dir.name}. "
            f"Open Buffer and bulk-upload the 3 final CSVs.",
        duration="long",
    )
    n.add_actions(label="Open folder", launch=str(bundle_dir))
    n.set_audio(audio.Default, loop=False)
    n.show()


def notify_failure(week_label: str, error_summary: str, log_path: Path | None = None) -> None:
    if not _AVAILABLE:
        print(f"[notify] (winotify unavailable) FAILED to build {week_label}: {error_summary}")
        return
    n = Notification(
        app_id="Spark Careers",
        title=f"Spark Careers {week_label} build FAILED",
        msg=error_summary[:200],
        duration="long",
    )
    if log_path is not None:
        n.add_actions(label="Open log", launch=str(log_path))
    n.set_audio(audio.IM, loop=False)
    n.show()
