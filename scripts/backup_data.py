#!/usr/bin/env python3
"""Manage compressed backup archives of untracked and .gitignore-excluded project data.

This script provides two primary functions:
1. compress: Archives all untracked and .gitignore-excluded data, models, reports,
   and generated images into a timestamped (or named) .zip file inside the outputs/backups folder.
2. decompress (restore): Extracts a specific (or latest) .zip archive from the outputs/backups folder,
   restores each file to its original project location, and validates that the file structure
   matches project expectations.
"""

from __future__ import annotations

import argparse
from datetime import datetime
import os
from pathlib import Path
import subprocess
import sys
import zipfile


def _find_repo_root(start_path: Path | None = None) -> Path:
    """Find repository root by looking for pyproject.toml or .git."""
    curr = (start_path or Path(__file__)).resolve()
    for parent in [curr] + list(curr.parents):
        if (parent / "pyproject.toml").exists() or (parent / ".git").exists():
            return parent
    return Path.cwd().resolve()


def _get_untracked_files(repo_root: Path, target_archive_path: Path | None = None) -> list[Path]:
    """Discover untracked and .gitignore-excluded files, filtering out transient caches/envs."""
    raw_rel_paths: list[str] = []

    # 1. Primary discovery via git if available
    git_dir = repo_root / ".git"
    if git_dir.exists():
        try:
            # Files ignored by .gitignore (data, models, outputs, reports)
            cmd_ignored = ["git", "ls-files", "-z", "--others", "--ignored", "--exclude-standard"]
            res_ignored = subprocess.run(cmd_ignored, cwd=repo_root, capture_output=True, check=True)
            raw_rel_paths.extend([f.decode("utf-8", "surrogateescape") for f in res_ignored.stdout.split(b"\0") if f])
        except (subprocess.SubprocessError, OSError):
            raw_rel_paths.clear()

    # 2. Fallback filesystem scan if git is unavailable or returned empty
    if not raw_rel_paths:
        data_roots = ["data", "models", "outputs", "reports"]
        valid_exts = {
            ".csv", ".json", ".parquet", ".png", ".jpg", ".jpeg", ".svg",
            ".pdf", ".pkl", ".joblib", ".tex",
        }
        for dr in data_roots:
            dir_path = repo_root / dr
            if dir_path.is_dir():
                for root, _, files in os.walk(dir_path):
                    for file in files:
                        p = Path(root) / file
                        if p.suffix.lower() in valid_exts and p.name != ".gitkeep":
                            raw_rel_paths.append(str(p.relative_to(repo_root)))

    # Transient and environment patterns to exclude from backup
    exclude_dir_names = {
        "__pycache__", ".venv", "venv", "env", "env.bak", "venv.bak",
        ".pytest_cache", ".ruff_cache", ".mypy_cache", ".hypothesis",
        ".cache", "build", "dist", ".ipynb_checkpoints", ".git", ".tox", ".nox",
    }
    exclude_file_exts = {".pyc", ".pyo", ".pyd"}
    exclude_filenames = {".DS_Store", "Thumbs.db"}
    allowed_top_dirs = {"data", "models", "outputs", "reports"}

    target_resolved = target_archive_path.resolve() if target_archive_path else None

    untracked_files: list[Path] = []
    for rel_str in set(raw_rel_paths):
        rel_path = Path(rel_str)
        parts = rel_path.parts
        parts_set = set(parts)

        # Must be in one of the data directories
        if not parts or parts[0] not in allowed_top_dirs:
            continue
        # Exclude development/environment caches
        if parts_set & exclude_dir_names:
            continue
        if any(part.endswith(".egg-info") for part in parts_set):
            continue
        if rel_path.suffix.lower() in exclude_file_exts or rel_path.name in exclude_filenames:
            continue
        # Exclude zip archives inside output/ or outputs/ to prevent recursion
        if (parts_set & {"output", "outputs"}) and rel_path.suffix.lower() == ".zip":
            continue

        abs_path = (repo_root / rel_path).resolve()
        if target_resolved and abs_path == target_resolved:
            continue

        if abs_path.is_file():
            untracked_files.append(rel_path)

    return sorted(untracked_files)


def _validate_structure(repo_root: Path) -> tuple[bool, list[str]]:
    """Validate that the restored project file structure matches expected components."""
    checks: list[str] = []
    success = True

    # 1. Raw CSI session recordings
    raw_dir = repo_root / "data/01_raw"
    raw_sessions = list(raw_dir.glob("*/*.csv")) if raw_dir.exists() else []
    if raw_sessions:
        checks.append(f"data/01_raw: Found {len(raw_sessions)} session recordings across campaigns")
    else:
        checks.append("data/01_raw: Missing or empty (no session CSV recordings found)")
        success = False

    # 2. Processed feature datasets and splits
    proc_dir = repo_root / "data/03_processed"
    splits_dir = proc_dir / "splits"
    has_features = (proc_dir / "features_ht40.parquet").exists() or (proc_dir / "features_ht40.csv").exists()
    has_splits = splits_dir.exists() and all(
        (splits_dir / f"{split}.parquet").exists() for split in ("train", "val", "test")
    )
    if has_features and has_splits:
        checks.append("data/03_processed: Canonical features dataset and train/val/test splits present")
    else:
        checks.append("data/03_processed: Missing canonical features dataset or splits (train/val/test.parquet)")
        success = False

    # 3. Trained model checkpoints and registry bundles
    models_dir = repo_root / "models"
    model_pickles = list(models_dir.glob("*.pkl")) if models_dir.exists() else []
    registry_dir = models_dir / "registry"
    has_registry = registry_dir.exists() and any(registry_dir.iterdir())
    if model_pickles and has_registry:
        checks.append(f"models: Found {len(model_pickles)} model checkpoints and pipeline registry bundles")
    else:
        checks.append("models: Missing trained model checkpoints (*.pkl) or registry bundles")
        success = False

    # 4. Generated analysis and diagnostic output figures
    outputs_dir = repo_root / "outputs"
    output_files = [f for f in outputs_dir.glob("*/*") if f.is_file() and f.suffix != ".gitkeep"] if outputs_dir.exists() else []
    if output_files:
        checks.append(f"outputs: Found {len(output_files)} generated figures and pipeline artifacts")
    else:
        checks.append("outputs: Missing generated figures and pipeline artifacts")
        success = False

    # 5. Thesis reports, evaluation logs, and LaTeX tables
    reports_dir = repo_root / "reports"
    report_files = [f for f in reports_dir.glob("*/*") if f.is_file()] if reports_dir.exists() else []
    if report_files:
        checks.append(f"reports: Found {len(report_files)} thesis figures, LaTeX tables, and evaluation logs")
    else:
        checks.append("reports: Missing thesis publication figures, tables, or evaluation logs")
        success = False

    return success, checks


def compress(
    archive_name: str | Path | None = None,
    output_dir: str | Path = "outputs/backups",
    repo_root: str | Path | None = None,
) -> Path:
    """Compress all untracked data and generated images into a single zip archive.

    Parameters
    ----------
    archive_name : str | Path | None
        Optional filename or full path for the zip archive. If None, generates a
        unique timestamped filename (e.g., 'backup_YYYYMMDD_HHMMSS.zip').
    output_dir : str | Path
        Directory where the archive will be saved (default: 'outputs/backups').
    repo_root : str | Path | None
        Root directory of the project repository.

    Returns
    -------
    Path
        Absolute path to the created zip archive.
    """
    root = _find_repo_root(Path(repo_root) if repo_root else None)
    out_dir = Path(output_dir) if Path(output_dir).is_absolute() else (root / output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    # Determine archive filename
    if archive_name:
        p_name = Path(archive_name)
        if p_name.is_absolute():
            archive_path = p_name
        elif len(p_name.parts) > 1:
            archive_path = root / p_name
        else:
            fname = p_name.name if p_name.suffix.lower() == ".zip" else f"{p_name.name}.zip"
            archive_path = out_dir / fname
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        archive_path = out_dir / f"backup_{timestamp}.zip"

    archive_path.parent.mkdir(parents=True, exist_ok=True)

    print("=" * 65)
    print("  COMPRESSING UNTRACKED PROJECT DATA")
    print(f"  Destination: {archive_path.relative_to(root) if archive_path.is_relative_to(root) else archive_path}")
    print("=" * 65)

    files_to_pack = _get_untracked_files(root, target_archive_path=archive_path)
    if not files_to_pack:
        print("[WARNING] No untracked data files found to compress.")
        return archive_path

    total_uncompressed_bytes = sum((root / f).stat().st_size for f in files_to_pack)

    print(f"Found {len(files_to_pack)} untracked data files ({total_uncompressed_bytes / (1024 * 1024):.1f} MB uncompressed).")
    print("Packing files into ZIP archive...")

    with zipfile.ZipFile(archive_path, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6, allowZip64=True) as zf:
        for idx, rel_path in enumerate(files_to_pack, 1):
            abs_path = root / rel_path
            zf.write(abs_path, arcname=rel_path.as_posix())
            if idx % 25 == 0 or idx == len(files_to_pack):
                print(f"  [{idx}/{len(files_to_pack)}] {rel_path}")

    compressed_bytes = archive_path.stat().st_size
    ratio = (1.0 - (compressed_bytes / max(1, total_uncompressed_bytes))) * 100.0

    print("\n" + "-" * 65)
    print("[SUCCESS] Archive created successfully:")
    print(f"  Path:             {archive_path}")
    print(f"  Files archived:   {len(files_to_pack)}")
    print(f"  Uncompressed size:{total_uncompressed_bytes / (1024 * 1024):.1f} MB")
    print(f"  Compressed size:  {compressed_bytes / (1024 * 1024):.1f} MB ({ratio:.1f}% space saving)")
    print("=" * 65)

    return archive_path


def decompress(
    archive_name: str | Path | None = None,
    output_dir: str | Path = "outputs/backups",
    repo_root: str | Path | None = None,
) -> tuple[bool, Path]:
    """Extract a specific (or latest) backup zip archive and validate the restored structure.

    Parameters
    ----------
    archive_name : str | Path | None
        Optional filename or path to the zip archive. If None, the most recent
        archive in the outputs/backups folder is selected automatically.
    output_dir : str | Path
        Directory containing the archives (default: 'outputs/backups').
    repo_root : str | Path | None
        Root directory of the project repository.

    Returns
    -------
    tuple[bool, Path]
        A tuple of (is_valid_structure, archive_path).
    """
    root = _find_repo_root(Path(repo_root) if repo_root else None)
    out_dir = Path(output_dir) if Path(output_dir).is_absolute() else (root / output_dir)

    # Resolve archive file
    archive_path: Path | None = None
    if archive_name:
        cand = Path(archive_name)
        candidates = [
            cand,
            root / cand,
            out_dir / cand,
            out_dir / (cand.name if cand.suffix.lower() == ".zip" else f"{cand.name}.zip"),
            root / "outputs" / cand.name,
            root / "outputs" / (cand.name if cand.suffix.lower() == ".zip" else f"{cand.name}.zip"),
        ]
        for c in candidates:
            if c.is_file():
                archive_path = c.resolve()
                break

        if not archive_path:
            raise FileNotFoundError(f"Archive file not found: {archive_name}")
    else:
        # Search for archives in output_dir, and fallback to outputs/
        search_dirs = [out_dir, root / "outputs"]
        found_archives: list[Path] = []
        for s_dir in search_dirs:
            if s_dir.is_dir():
                found_archives.extend(s_dir.glob("*.zip"))

        if not found_archives:
            raise FileNotFoundError(
                f"No backup archives found in {out_dir} (or {root / 'outputs'}). "
                "Specify an archive using --file or run compression first."
            )

        # Sort by modification time (most recent first)
        found_archives = sorted(set(found_archives), key=lambda p: p.stat().st_mtime, reverse=True)
        archive_path = found_archives[0]

        if len(found_archives) > 1:
            print(f"Found {len(found_archives)} archives in output folder. Selected latest:")
            for a in found_archives[:5]:
                marker = " -> [SELECTED]" if a == archive_path else ""
                mtime_str = datetime.fromtimestamp(a.stat().st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                print(f"   • {a.name} ({mtime_str}){marker}")

    print("=" * 65)
    print("  DECOMPRESSING AND RESTORING PROJECT DATA")
    print(f"  Archive:     {archive_path.name}")
    print(f"  Location:    {archive_path}")
    print(f"  Target Root: {root}")
    print("=" * 65)

    # 1. Integrity check
    with zipfile.ZipFile(archive_path, mode="r") as zf:
        corrupt = zf.testzip()
        if corrupt:
            raise ValueError(f"Corrupt file detected inside archive {archive_path.name}: {corrupt}")

        infolist = zf.infolist()
        print(f"Archive integrity verified: {len(infolist)} entries ready for extraction.")

        # 2. Path safety check (Zip Slip prevention)
        for member in infolist:
            p = Path(member.filename)
            if p.is_absolute() or ".." in p.parts:
                raise ValueError(f"Security error: Archive contains unsafe member path: {member.filename}")

        # 3. Extract files to original project structure
        extracted_count = 0
        for member in infolist:
            target_path = root / member.filename
            if member.is_dir():
                target_path.mkdir(parents=True, exist_ok=True)
            else:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(member) as source, open(target_path, "wb") as target:
                    target.write(source.read())
                extracted_count += 1

    print(f"\nExtracted {extracted_count} files into repository.")

    # 4. Validate restored structure matches project expectations
    print("\n" + "-" * 65)
    print("  VALIDATING RESTORED FILE STRUCTURE")
    print("-" * 65)
    is_valid, check_details = _validate_structure(root)

    for check in check_details:
        prefix = "  ✓ [OK]    " if not check.startswith(("Missing", "data/01_raw: Missing", "models: Missing", "outputs: Missing", "reports: Missing")) else "  ✗ [FAILED]"
        print(f"{prefix} {check}")

    print("-" * 65)
    if is_valid:
        print("[SUCCESS] Decompression complete. Restored file structure matches all expectations.")
    else:
        print("[WARNING] File structure validation found missing or incomplete components.")
    print("=" * 65)

    return is_valid, archive_path


# Alias decompress to restore
restore = decompress


def main() -> None:
    """CLI entrypoint supporting both subcommand and option flag invocations."""
    parser = argparse.ArgumentParser(
        description="Backup and restore untracked Wi-Fi CSI project data and generated assets."
    )
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Command: compress
    parser_comp = subparsers.add_parser("compress", help="Compress untracked/ignored data into a zip file")
    parser_comp.add_argument(
        "-f", "--file", dest="filename", type=str, default=None,
        help="Optional archive filename (default: timestamped 'backup_YYYYMMDD_HHMMSS.zip')"
    )
    parser_comp.add_argument(
        "-d", "--dir", "--output-dir", dest="output_dir", type=str, default="outputs/backups",
        help="Directory where archive will be saved (default: 'outputs/backups')"
    )

    # Command: decompress / restore
    parser_decomp = subparsers.add_parser("decompress", help="Extract and restore data from a zip archive")
    parser_decomp.add_argument(
        "-f", "--file", dest="filename", type=str, default=None,
        help="Specific archive filename or path to restore (default: latest archive)"
    )
    parser_decomp.add_argument(
        "-d", "--dir", "--output-dir", dest="output_dir", type=str, default="outputs/backups",
        help="Directory containing archives (default: 'outputs/backups')"
    )

    parser_restore = subparsers.add_parser("restore", help="Alias for decompress")
    parser_restore.add_argument(
        "-f", "--file", dest="filename", type=str, default=None,
        help="Specific archive filename or path to restore (default: latest archive)"
    )
    parser_restore.add_argument(
        "-d", "--dir", "--output-dir", dest="output_dir", type=str, default="outputs/backups",
        help="Directory containing archives (default: 'outputs/backups')"
    )

    # Support top-level flags as fallback
    parser.add_argument("-c", "--compress", action="store_true", help="Compress data files")
    parser.add_argument("-x", "-r", "--decompress", "--restore", dest="do_restore", action="store_true", help="Restore data files")
    parser.add_argument("-f", "--file", dest="flag_file", type=str, default=None, help="Archive filename")
    parser.add_argument("-d", "--dir", dest="flag_dir", type=str, default="outputs/backups", help="Output directory")

    args = parser.parse_args()

    command = args.command
    if not command:
        if args.compress:
            command = "compress"
        elif args.do_restore:
            command = "decompress"

    if command == "compress":
        fname = getattr(args, "filename", None) or args.flag_file
        odir = getattr(args, "output_dir", None) or args.flag_dir
        compress(archive_name=fname, output_dir=odir)
    elif command in ("decompress", "restore"):
        fname = getattr(args, "filename", None) or args.flag_file
        odir = getattr(args, "output_dir", None) or args.flag_dir
        ok, _ = decompress(archive_name=fname, output_dir=odir)
        if not ok:
            sys.exit(1)
    else:
        parser.print_help()
        sys.exit(0)


if __name__ == "__main__":
    main()
