import os
import importlib.util


# Dynamically import the module to ensure tests run from repo root
spec = importlib.util.spec_from_file_location('scrape_transcripts', os.path.join(os.path.dirname(__file__), '..', 'scrape_transcripts.py'))
scrape_transcripts = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scrape_transcripts)


def test_fetch_transcript_for_video_monkeypatched(monkeypatch):
    # Monkeypatch the YouTubeTranscriptApi instance to return an object similar to FetchedTranscript
    class FakeSnippet:
        def __init__(self, text, start, duration):
            self.text = text
            self.start = start
            self.duration = duration

    class FakeFetchedTranscript:
        def __init__(self):
            self._snippets = [FakeSnippet('hello', 0, 1), FakeSnippet('world', 1, 1)]

        def to_raw_data(self):
            return [{'text': s.text, 'start': s.start, 'duration': s.duration} for s in self._snippets]

    class FakeApi:
        def fetch(self, video_id, languages=None):
            return FakeFetchedTranscript()

    monkeypatch.setattr(scrape_transcripts, 'YouTubeTranscriptApi', FakeApi)

    res = scrape_transcripts.fetch_transcript_for_video('FAKEID')
    assert res['status'] == 'fetched'
    assert isinstance(res['raw'], list)
    assert res['raw'][0]['text'] == 'hello'
    assert res['raw'][1]['text'] == 'world'
    assert res['error'] is None
