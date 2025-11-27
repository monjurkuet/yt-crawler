import os
import importlib.util


# Dynamically import the module to ensure tests run from repo root
spec = importlib.util.spec_from_file_location('transcript_repository', os.path.join(os.path.dirname(__file__), '..', 'database', 'transcript_repository.py'))
transcript_repository = importlib.util.module_from_spec(spec)
spec.loader.exec_module(transcript_repository)


def test_transcript_repository_has_expected_methods():
    cls = getattr(transcript_repository, 'TranscriptRepository', None)
    assert cls is not None
    # Just ensure the key methods exist (no DB calls performed in this test)
    for method_name in ('create_table', 'upsert_transcript', 'get_transcript', 'get_videos_without_transcripts'):
        assert hasattr(cls, method_name), f"Missing method {method_name}"
