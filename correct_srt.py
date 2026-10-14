"""Apply supplied text corrections while preserving SRT cue IDs and timing."""
import argparse
import json
import re
from pathlib import Path


def correct_srt(source: str, edits: dict) -> str:
    if not isinstance(edits, dict) or not all(isinstance(k, str) and isinstance(v, str) for k, v in edits.items()):
        raise ValueError('修改表必须是字幕编号到文字的对象')
    blocks = re.split(r'\r?\n\s*\r?\n', source.strip())
    seen, output = set(), []
    for block in blocks:
        lines = block.splitlines()
        if len(lines) < 3 or not lines[0].isdigit() or not re.fullmatch(r'\d{2}:\d{2}:\d{2},\d{3} --> \d{2}:\d{2}:\d{2},\d{3}', lines[1]):
            raise ValueError('存在无效 SRT 块')
        cue = lines[0]
        if cue in seen:
            raise ValueError('字幕编号重复')
        seen.add(cue)
        text = edits.get(cue, '\n'.join(lines[2:])).replace('\r\n', '\n')
        if not text.strip() or '\r' in text or re.search(r'\n\s*\n', text):
            raise ValueError('字幕文字不可为空或包含空段')
        output.append('\n'.join([cue, lines[1], text]))
    if set(edits) - seen:
        raise ValueError('修改表包含源字幕中不存在的编号')
    return '\n\n'.join(output) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('corrections', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = correct_srt(args.input.read_text('utf-8-sig'), json.loads(args.corrections.read_text('utf-8-sig')))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(result)
    print(args.output)


if __name__ == '__main__':
    main()
