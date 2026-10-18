import base64
import hashlib
import io
import tarfile

import pytest

from tools.vendor_assets import ICONS, IntegrityError, read_member, verify_integrity


def sha512_integrity(data: bytes) -> str:
    return "sha512-" + base64.b64encode(hashlib.sha512(data).digest()).decode()


def make_tgz(files: dict[str, bytes]) -> bytes:
    buffer = io.BytesIO()
    with tarfile.open(fileobj=buffer, mode="w:gz") as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(f"package/{name}")
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return buffer.getvalue()


def test_matching_integrity_passes():
    verify_integrity(b"motion", sha512_integrity(b"motion"))


def test_tampered_archive_is_refused():
    with pytest.raises(IntegrityError):
        verify_integrity(b"motion modifie", sha512_integrity(b"motion"))


def test_non_sha512_integrity_is_refused():
    with pytest.raises(IntegrityError):
        verify_integrity(b"motion", "sha1-abc")


def test_read_member_returns_file_content_without_extracting_to_disk():
    archive = make_tgz({"dist/motion.js": b"window.Motion={}"})
    assert read_member(archive, "dist/motion.js") == b"window.Motion={}"


def test_read_member_missing_file_fails():
    with pytest.raises(KeyError):
        read_member(make_tgz({"a.js": b""}), "dist/motion.js")


def test_icon_list_is_closed_and_unique():
    assert len(ICONS) == len(set(ICONS)) == 18
