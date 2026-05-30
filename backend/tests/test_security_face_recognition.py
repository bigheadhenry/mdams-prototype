"""Security tests for face recognition pickle deserialization.

Covers audit issue:
  C-4: pickle.load enables RCE via tampered index files
"""

import json

import pytest

from app.services.local_face_recognition import _load_embeddings_safe, LocalFaceRecognitionError

pytestmark = [pytest.mark.unit, pytest.mark.contract]


class TestLoadEmbeddingsSafe:
    """Verify _load_embeddings_safe rejects pickle and accepts safe formats."""

    def test_rejects_pickle_file(self, tmp_path):
        """C-4: .pkl file should raise LocalFaceRecognitionError."""
        pkl_path = tmp_path / "embeddings.pkl"
        pkl_path.write_bytes(b"fake pickle data")
        with pytest.raises(LocalFaceRecognitionError, match="Unsafe embeddings format"):
            _load_embeddings_safe(pkl_path)

    def test_accepts_json_format(self, tmp_path):
        """C-4: .json file should be loaded correctly."""
        json_path = tmp_path / "embeddings.json"
        data = {"face_1": [0.1, 0.2, 0.3], "face_2": [0.4, 0.5, 0.6]}
        json_path.write_text(json.dumps(data), encoding="utf-8")
        result = _load_embeddings_safe(json_path)
        assert "face_1" in result
        assert result["face_1"] == [0.1, 0.2, 0.3]

    def test_accepts_npz_format(self, tmp_path):
        """C-4: .npz file should be loaded correctly."""
        npz_path = tmp_path / "embeddings.npz"
        try:
            import numpy as np
            np.savez_compressed(str(npz_path), face_1=np.array([0.1, 0.2, 0.3]))
            result = _load_embeddings_safe(npz_path)
            assert "face_1" in result
        except ImportError:
            pytest.skip("numpy not available")

    def test_rejects_unknown_binary_format(self, tmp_path):
        """C-4: Unknown binary file should raise error."""
        bin_path = tmp_path / "embeddings.bin"
        bin_path.write_bytes(b"\x00\x01\x02\x03")
        with pytest.raises(LocalFaceRecognitionError, match="Unsafe embeddings format"):
            _load_embeddings_safe(bin_path)

    def test_tampered_npz_rejected(self, tmp_path):
        """C-4: Corrupted .npz file should raise an error (not execute code)."""
        npz_path = tmp_path / "embeddings.npz"
        npz_path.write_bytes(b"NOT_A_VALID_NPZ_FILE")
        with pytest.raises(Exception):
            _load_embeddings_safe(npz_path)

    def test_json_fallback_for_unknown_extension(self, tmp_path):
        """C-4: Unknown extension but valid JSON should still load."""
        path = tmp_path / "embeddings.dat"
        data = {"face_1": [0.1, 0.2]}
        path.write_text(json.dumps(data), encoding="utf-8")
        result = _load_embeddings_safe(path)
        assert "face_1" in result
