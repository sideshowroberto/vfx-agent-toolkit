"""Retrieve existing YouTube captions; dependency: youtube-transcript-api==1.2.4."""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse


def video_id(value):
    value = value.strip()
    if re.fullmatch(r'[A-Za-z0-9_-]{11}', value):
        return value
    url = urlparse(value if '://' in value else 'https://' + value)
    if url.scheme not in ('http', 'https'):
        raise ValueError('Expected a YouTube URL or 11-character video ID')
    host = (url.hostname or '').lower()
    pieces = url.path.strip('/').split('/')
    candidate = None
    if host in ('youtu.be', 'www.youtu.be') and len(pieces) == 1:
        candidate = pieces[0]
    elif host in ('youtube.com', 'www.youtube.com', 'm.youtube.com', 'music.youtube.com'):
        if url.path == '/watch':
            candidate = parse_qs(url.query).get('v', [''])[0]
        elif len(pieces) == 2 and pieces[0] in ('shorts', 'embed', 'live'):
            candidate = pieces[1]
    if not candidate or not re.fullmatch(r'[A-Za-z0-9_-]{11}', candidate):
        raise ValueError('Expected a supported YouTube URL or 11-character video ID')
    return candidate


def render(rows, timestamps=False):
    lines = []
    for row in rows:
        text = row['text']
        if timestamps:
            seconds = int(row['start'])
            text = f'[{seconds//3600:02d}:{seconds//60%60:02d}:{seconds%60:02d}] {text}'
        lines.append(text)
    return '\n'.join(lines) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('video')
    parser.add_argument('--out-dir', required=True, type=Path)
    parser.add_argument('--languages', default='en')
    args = parser.parse_args(argv)
    try:
        ident = video_id(args.video)
        languages = [x.strip() for x in args.languages.split(',') if x.strip()]
        if not languages:
            raise ValueError('At least one language is required')
        from youtube_transcript_api import YouTubeTranscriptApi
        fetched = YouTubeTranscriptApi().fetch(ident, languages=languages)
        rows = fetched.to_raw_data()  # Modern snippets are objects, not dictionaries.
        if not rows:
            raise ValueError('The returned caption track is empty')
        plain = render(rows)
        metadata = dict(video_id=ident, source_url=f'https://www.youtube.com/watch?v={ident}',
                        language=fetched.language, language_code=fetched.language_code,
                        is_generated=fetched.is_generated, segments=len(rows),
                        words=len(plain.split()),
                        last_caption_end_seconds=max(r['start']+r['duration'] for r in rows))
        args.out_dir.mkdir(parents=True, exist_ok=True)
        paths = [args.out_dir / (ident + suffix) for suffix in
                 ('-transcript.txt', '-timestamps.txt', '.json')]
        if any(path.exists() for path in paths):
            raise FileExistsError('Output exists; choose a new directory to retain the prior extraction')
        paths[0].write_text(plain, encoding='utf-8')
        paths[1].write_text(render(rows, True), encoding='utf-8')
        paths[2].write_text(json.dumps(dict(metadata=metadata, captions=rows),
                                       indent=2, ensure_ascii=False)+'\n', encoding='utf-8')
        print(json.dumps(dict(ok=True, **metadata, files=[str(p.resolve()) for p in paths])))
        return 0
    except Exception as error:
        print(json.dumps(dict(ok=False, error=type(error).__name__, message=str(error))))
        return 1


if __name__ == '__main__':
    sys.exit(main())
