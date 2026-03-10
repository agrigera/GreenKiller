"""End-to-end workflow integration tests for CorridorKey.

These tests exercise the full pipeline from ClipEntry asset discovery through
run_inference output file creation.  The neural network engine is mocked so
no model weights or GPU are required.

Why integration-test run_inference?
  Unit tests cover individual math functions.  This file verifies that the
  orchestration layer (reading frames from disk, calling the engine, writing
  output files to the right directories) works end-to-end on realistic
  directory structures.
"""

from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

import numpy as np

# Must be set before importing cv2 so OpenEXR codec is enabled in this process.
os.environ.setdefault("OPENCV_IO_ENABLE_OPENEXR", "1")
import cv2

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fake_result(h: int = 4, w: int = 4) -> dict:
    """Return a minimal but valid process_frame result dict sized to (h, w)."""
    return {
        "alpha": np.full((h, w, 1), 0.8, dtype=np.float32),
        "fg": np.full((h, w, 3), 0.6, dtype=np.float32),
        "comp": np.full((h, w, 3), 0.5, dtype=np.float32),
        "processed": np.full((h, w, 4), 0.4, dtype=np.float32),
    }


# ---------------------------------------------------------------------------
# End-to-end: ClipEntry discovery → run_inference → files on disk
# ---------------------------------------------------------------------------


class TestE2EInferenceWorkflow:
    """End-to-end: ClipEntry discovery → run_inference → output files on disk.

    Uses the ``tmp_clip_dir`` fixture (shot_a: 2 frames, shot_b: 1 frame /
    no alpha) and a mocked engine.  Verifies directory creation, frame I/O,
    and file writing without a real engine or checkpoint.
    """

    def test_output_directories_created(self, tmp_clip_dir, monkeypatch):
        """run_inference creates Output/{FG,Matte,Comp,Processed} for each clip."""
        from clip_manager import ClipEntry, run_inference

        entry = ClipEntry("shot_a", str(tmp_clip_dir / "shot_a"))
        entry.find_assets()

        # Supply blank answers to all interactive prompts inside run_inference
        monkeypatch.setattr("builtins.input", lambda prompt="": "")

        mock_engine = MagicMock()
        mock_engine.process_frame.return_value = _fake_result()

        with patch("CorridorKeyModule.backend.create_engine", return_value=mock_engine):
            run_inference([entry], device="cpu")

        out_root = tmp_clip_dir / "shot_a" / "Output"
        assert (out_root / "FG").is_dir()
        assert (out_root / "Matte").is_dir()
        assert (out_root / "Comp").is_dir()
        assert (out_root / "Processed").is_dir()

    def test_output_files_written_per_frame(self, tmp_clip_dir, monkeypatch):
        """run_inference writes exactly one output file per input frame.

        shot_a has 2 input frames and 2 alpha frames, so each output
        subdirectory should contain exactly 2 files after inference.
        """
        from clip_manager import ClipEntry, run_inference

        entry = ClipEntry("shot_a", str(tmp_clip_dir / "shot_a"))
        entry.find_assets()

        monkeypatch.setattr("builtins.input", lambda prompt="": "")

        mock_engine = MagicMock()
        mock_engine.process_frame.return_value = _fake_result()

        with patch("CorridorKeyModule.backend.create_engine", return_value=mock_engine):
            run_inference([entry], device="cpu")

        out_root = tmp_clip_dir / "shot_a" / "Output"
        # shot_a has 2 frames → 2 files per output directory
        assert len(list((out_root / "FG").glob("*.exr"))) == 2
        assert len(list((out_root / "Matte").glob("*.exr"))) == 2
        assert len(list((out_root / "Comp").glob("*.png"))) == 2
        assert len(list((out_root / "Processed").glob("*.exr"))) == 2

    def test_clip_without_alpha_skipped(self, tmp_clip_dir, monkeypatch):
        """Clips missing an alpha asset are silently skipped by run_inference.

        shot_b has Input but an empty AlphaHint, so it has no alpha_asset.
        run_inference should process zero frames and create no Output directory.
        """
        from clip_manager import ClipEntry, run_inference

        entry = ClipEntry("shot_b", str(tmp_clip_dir / "shot_b"))
        entry.find_assets()
        assert entry.alpha_asset is None  # precondition

        monkeypatch.setattr("builtins.input", lambda prompt="": "")

        mock_engine = MagicMock()
        mock_engine.process_frame.return_value = _fake_result()

        with patch("CorridorKeyModule.backend.create_engine", return_value=mock_engine):
            run_inference([entry], device="cpu")

        # No engine calls — clip was filtered out before inference
        mock_engine.process_frame.assert_not_called()
        assert not (tmp_clip_dir / "shot_b" / "Output").exists()

    def test_exr_input_respects_user_gamma_setting(self, tmp_path):
        """EXR reads must honor InferenceSettings.input_is_linear.

        For EXR input sequences, run_inference should request gamma correction
        only when user selected sRGB input (input_is_linear=False).
        """
        from clip_manager import ClipEntry, InferenceSettings, run_inference

        shot = tmp_path / "shot_exr"
        (shot / "Input").mkdir(parents=True)
        (shot / "AlphaHint").mkdir(parents=True)
        (shot / "VideoMamaMaskHint").mkdir(parents=True)

        # File existence is discovered by extension; actual pixel read is mocked.
        (shot / "Input" / "frame_0000.exr").write_bytes(b"dummy")

        tiny_mask = np.zeros((4, 4), dtype=np.uint8)
        tiny_mask[1:3, 1:3] = 255
        cv2.imwrite(str(shot / "AlphaHint" / "frame_0000.png"), tiny_mask)

        entry = ClipEntry("shot_exr", str(shot))
        entry.find_assets()

        fake_img = np.full((4, 4, 3), 0.5, dtype=np.float32)
        mock_engine = MagicMock()
        mock_engine.process_frame.return_value = _fake_result()

        with patch("CorridorKeyModule.backend.create_engine", return_value=mock_engine):
            with patch("clip_manager.read_image_frame", return_value=fake_img) as mock_read:
                run_inference([entry], device="cpu", settings=InferenceSettings(input_is_linear=False))
                assert mock_read.call_count == 1
                assert mock_read.call_args.kwargs["gamma_correct_exr"] is True

        # Re-run with user saying input is linear: gamma correction must be off.
        with patch("CorridorKeyModule.backend.create_engine", return_value=mock_engine):
            with patch("clip_manager.read_image_frame", return_value=fake_img) as mock_read:
                run_inference([entry], device="cpu", settings=InferenceSettings(input_is_linear=True))
                assert mock_read.call_count == 1
                assert mock_read.call_args.kwargs["gamma_correct_exr"] is False
