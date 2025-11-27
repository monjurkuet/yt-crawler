import os
import tempfile
import importlib.util


# Dynamically import the module to ensure tests run from repo root
spec = importlib.util.spec_from_file_location('scrape_channels', os.path.join(os.path.dirname(__file__), '..', 'scrape_channels.py'))
scrape_channels = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrape_channels)


def test_parse_channel_file(tmp_path):
    content = """
    # comment line should be ignored
    UCFOO1

    UCBAR2
    # another comment
    """

    file_path = tmp_path / 'channels.txt'
    file_path.write_text(content)

    channels = scrape_channels.parse_channel_file(str(file_path))
    assert channels == ['UCFOO1', 'UCBAR2']
