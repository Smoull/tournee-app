import pytest

from app.icons import icon
from tools.vendor_assets import ICONS


@pytest.mark.parametrize("name", ICONS)
def test_every_vendored_icon_renders_in_palette_color(name):
    svg = str(icon(name, "size-5 text-accent"))
    assert svg.startswith('<svg class="size-5 text-accent" aria-hidden="true" focusable="false" ')
    assert 'fill="currentColor"' in svg


def test_unknown_icon_fails_fast():
    with pytest.raises(ValueError, match="cloud-snow"):
        icon("cloud-snow")



def test_icon_is_available_in_templates(settings, repository):
    from fastapi.templating import Jinja2Templates

    from app.factory import create_app

    app = create_app(settings, repository)
    templates: Jinja2Templates = app.state.templates
    rendered = templates.env.from_string('{{ icon("map-pin", "size-4") }}').render()
    assert rendered.startswith('<svg class="size-4"')
