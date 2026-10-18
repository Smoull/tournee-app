import base64
import hashlib
import io
import tarfile
import urllib.request
from pathlib import Path

LANDING_DIR = Path(__file__).parent.parent
MOTION_DIR = LANDING_DIR / "static" / "js" / "vendor"
ICONS_DIR = LANDING_DIR / "app" / "static_src" / "icons"

# Versions figées ; empreintes copiées depuis le registre npm (champ dist.integrity).
MOTION = (
    "https://registry.npmjs.org/motion/-/motion-13.4.6.tgz",
    "sha512-zDXi6lIdyhda6wZlTsv9QgT2ed6UExAfRegtl/akQmZb5iaeLlArXr9Gmo/hx3iTx2y4R7tmdb9k9koFQmV+NQ==",
)
PHOSPHOR = (
    "https://registry.npmjs.org/@phosphor-icons/core/-/core-2.1.1.tgz",
    "sha512-v4ARvrip4qBCImOE5rmPUylOEK4iiED9ZyKjcvzuezqMaiRASCHKcRIuvvxL/twvLpkfnEODCOJp5dM4eZilxQ==",
)
ICONS = (
    "x-circle",
    "user-minus",
    "user",
    "download-simple",
    "plus-circle",
    "lightning",
    "chat-text",
    "printer",
    "hand-heart",
    "shield-check",
    "clock-countdown",
    "calendar-check",
    "map-pin",
    "arrow-counter-clockwise",
    "cloud-rain",
    "gas-pump",
    "watch",
    "calendar-x",
)


class IntegrityError(RuntimeError):
    pass


def verify_integrity(data: bytes, integrity: str) -> None:
    algorithm, _, expected = integrity.partition("-")
    if algorithm != "sha512":
        raise IntegrityError(f"algorithme d'empreinte non supporté : {algorithm}")
    actual = base64.b64encode(hashlib.sha512(data).digest()).decode()
    if actual != expected:
        raise IntegrityError("empreinte sha512 différente de celle publiée par le registre")


def read_member(archive: bytes, member: str) -> bytes:
    # Lecture en mémoire : rien n'est extrait sur le disque (pas de risque de chemin malveillant).
    with tarfile.open(fileobj=io.BytesIO(archive), mode="r:gz") as tar:
        extracted = tar.extractfile(f"package/{member}")
        if extracted is None:
            raise KeyError(member)
        return extracted.read()


def _download(url: str, integrity: str) -> bytes:
    with urllib.request.urlopen(url, timeout=30) as response:
        data = response.read()
    verify_integrity(data, integrity)
    return data


def vendor() -> None:
    motion = _download(*MOTION)
    MOTION_DIR.mkdir(parents=True, exist_ok=True)
    (MOTION_DIR / "motion.js").write_bytes(read_member(motion, "dist/motion.js"))
    (MOTION_DIR / "motion-LICENSE.md").write_bytes(read_member(motion, "LICENSE.md"))

    phosphor = _download(*PHOSPHOR)
    ICONS_DIR.mkdir(parents=True, exist_ok=True)
    (ICONS_DIR / "LICENSE").write_bytes(read_member(phosphor, "LICENSE"))
    for name in ICONS:
        (ICONS_DIR / f"{name}.svg").write_bytes(read_member(phosphor, f"assets/regular/{name}.svg"))


if __name__ == "__main__":
    vendor()
