import pytest

from app.settings import Settings, SettingsError, load_settings

VALID = 'LEAD_STORE = "memory"\nCALCOM_URL = "https://cal.com/example/15min"\nCONTACT_EMAIL = "contact@example.com"\n'


def test_loads_valid_settings(tmp_path):
    path = tmp_path / "secret.toml"
    path.write_text(VALID)

    assert load_settings(path) == Settings(
        lead_store="memory",
        calcom_url="https://cal.com/example/15min",
        contact_email="contact@example.com",
    )


def test_missing_file_fails_with_hint(tmp_path):
    with pytest.raises(SettingsError, match="secret.toml.example"):
        load_settings(tmp_path / "secret.toml")


@pytest.mark.parametrize("key", ["LEAD_STORE", "CALCOM_URL", "CONTACT_EMAIL"])
def test_missing_or_empty_key_fails(tmp_path, key):
    path = tmp_path / "secret.toml"
    path.write_text(VALID.replace(f'{key} = "', f'{key} = "" #'))

    with pytest.raises(SettingsError, match=key):
        load_settings(path)


def test_unsupported_lead_store_fails(tmp_path):
    path = tmp_path / "secret.toml"
    path.write_text(VALID.replace('"memory"', '"supabase"'))

    with pytest.raises(SettingsError, match="supabase"):
        load_settings(path)
