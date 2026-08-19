from typing import Callable

DEFAULT_LANGUAGE = "en"

LANGUAGE_NAMES: dict[str, str] = {
    "en": "English",
    "ko": "한국어",
}

TRANSLATIONS: dict[str, dict[str, str]] = {
    "en": {
        "dl.downloading": "[SubBake] Downloading FFmpeg... ({system} / {machine})",
        "dl.progress": "[SubBake] Download {pct}%",
        "dl.fallback": "[SubBake] Primary URL failed, trying the fallback URL...",
        "dl.rosetta": "[SubBake] The fallback binary is an Intel (x86_64) build. Rosetta 2 may be required.",
        "dl.extracting": "[SubBake] Extracting...",
        "dl.ready": "[SubBake] FFmpeg is ready: {path}",
        "dl.unsupported_os": "Unsupported OS: {system}",
        "dl.unknown_archive": "Unknown archive format: {name}",
        "dl.not_in_archive": "{exe} was not found in the archive.",
        "ffmpeg.not_found": "FFmpeg was not found.\nRun download_ffmpeg.py or install FFmpeg on your system.",
        "sub.unsupported_format": "Unsupported subtitle format: {ext}",
        "sub.no_parse_needed": "{fmt} can be muxed directly, so parsing is not needed.",
        "mux.mp4_no_sup": "MP4 does not support PGS/SUP bitmap subtitles.",
        "mux.webm_no_sup": "WebM does not support PGS/SUP bitmap subtitles.",
        "mux.cancelled": "The task was cancelled by the user.",
        "mux.ffmpeg_error": "FFmpeg error (code {code}):\n{stderr}",
        "mux.unknown_error": "Unknown error",
        "worker.cancelled": "Cancelled",
        "worker.format": "[{name}] Format: {fmt}",
        "worker.processing": "Processing {fmt}...",
        "worker.parsing": "Parsing {fmt}...",
        "worker.parsed": "[{name}] Parsed {count} subtitle entries",
        "worker.converting": "Converting to {fmt}...",
        "worker.muxing": "Muxing video... {pct}%",
        "worker.done": "Done",
        "worker.done_log": "[{name}] Done",
        "worker.failed_log": "[{name}] Failed: {error}",
        "drop.hint": "Drag MKV / subtitle files here, or click to browse",
        "log.show": "Show log",
        "log.hide": "Hide log",
        "app.window_title": "SubBake",
        "app.title": "SubBake",
        "app.subtitle": "The easiest way to embed subtitles into MKV / MP4 / WebM",
        "btn.add_files": "Add files",
        "btn.add_folder": "Add folder",
        "btn.clear": "Clear list",
        "btn.output_dir": "Output folder",
        "btn.start": "Start SubBake",
        "btn.cancel": "Cancel",
        "label.file_count": "{count} files",
        "label.sub_language": "Subtitle language:",
        "label.ui_language": "Language:",
        "label.sync": "Sync (ms):",
        "label.output_same": "Same folder as the source",
        "label.total_progress": "Overall progress:",
        "chk.overwrite": "Overwrite original",
        "chk.default_sub": "Set as default subtitle",
        "chk.burn": "Render subtitles onto video (burn-in)",
        "tip.default_sub": "Mark the newly embedded subtitle as the default track",
        "tip.burn": "Draw the subtitles directly into the video frames so every player shows them",
        "tip.offset": "Positive = delay subtitles, negative = advance subtitles",
        "table.video": "Video file",
        "table.subtitle": "Subtitle file",
        "table.format": "Format",
        "table.progress": "Progress",
        "table.status": "Status",
        "status.waiting": "Waiting",
        "dialog.select_files": "Select files",
        "dialog.select_folder": "Select folder",
        "dialog.select_output": "Select output folder",
        "filter.media": "Media/subtitle files ({exts})",
        "filter.all": "All files (*)",
        "msg.notice": "Notice",
        "msg.no_files": "There are no files to process.",
        "msg.ffmpeg_missing_title": "FFmpeg not found",
        "msg.done_title": "SubBake finished",
        "msg.done": "All {total} files were processed!",
        "status.ffmpeg_missing": "FFmpeg was not found",
        "log.system": "[System] {version}",
        "log.ffmpeg_missing": "[Error] FFmpeg was not found. Please run download_ffmpeg.py.",
        "log.dropped": "[Drop] {files} files -> {pairs} pairs matched",
        "log.folder": "[Folder] {name}/ -> {pairs} pairs matched",
        "log.start": "\n[Start] Processing {total} files (language: {lang}, overwrite: {overwrite})",
        "log.cancel": "[Cancel] Cancelling the remaining tasks...",
        "log.cancel_done": "\n[Cancelled] All tasks were cancelled.",
        "log.all_done": "\n[Finished] All {total} files were processed!",
        "common.yes": "yes",
        "common.no": "no",
        "tray.tooltip": "SubBake",
    },
    "ko": {
        "dl.downloading": "[SubBake] FFmpeg 다운로드 중... ({system} / {machine})",
        "dl.progress": "[SubBake] 다운로드 {pct}%",
        "dl.fallback": "[SubBake] 주 URL 실패, 폴백 URL 시도 중...",
        "dl.rosetta": "[SubBake] 폴백 바이너리는 Intel(x86_64) 빌드입니다. Rosetta 2가 필요할 수 있습니다.",
        "dl.extracting": "[SubBake] 압축 해제 중...",
        "dl.ready": "[SubBake] FFmpeg 준비 완료: {path}",
        "dl.unsupported_os": "지원하지 않는 OS: {system}",
        "dl.unknown_archive": "알 수 없는 압축 형식: {name}",
        "dl.not_in_archive": "{exe}을(를) 압축 파일에서 찾을 수 없습니다.",
        "ffmpeg.not_found": "FFmpeg를 찾을 수 없습니다.\ndownload_ffmpeg.py를 실행하거나 시스템에 FFmpeg를 설치해 주세요.",
        "sub.unsupported_format": "지원하지 않는 자막 포맷: {ext}",
        "sub.no_parse_needed": "{fmt}는 직접 mux 가능하므로 파싱이 필요하지 않습니다.",
        "mux.mp4_no_sup": "MP4는 PGS/SUP 비트맵 자막을 지원하지 않습니다.",
        "mux.webm_no_sup": "WebM은 PGS/SUP 비트맵 자막을 지원하지 않습니다.",
        "mux.cancelled": "사용자가 작업을 취소했습니다.",
        "mux.ffmpeg_error": "FFmpeg 오류 (코드 {code}):\n{stderr}",
        "mux.unknown_error": "알 수 없는 오류",
        "worker.cancelled": "취소됨",
        "worker.format": "[{name}] 포맷: {fmt}",
        "worker.processing": "{fmt} 처리 중...",
        "worker.parsing": "{fmt} 파싱 중...",
        "worker.parsed": "[{name}] {count}개 자막 엔트리 파싱 완료",
        "worker.converting": "{fmt} 변환 중...",
        "worker.muxing": "영상 합치는 중... {pct}%",
        "worker.done": "완료",
        "worker.done_log": "[{name}] 완료",
        "worker.failed_log": "[{name}] 실패: {error}",
        "drop.hint": "여기에 MKV / 자막 파일을 드래그하거나, 클릭해서 선택하세요",
        "log.show": "로그 보기",
        "log.hide": "로그 닫기",
        "app.window_title": "SubBake",
        "app.title": "SubBake",
        "app.subtitle": "자막을 MKV / MP4 / WebM에 내장하는 가장 쉬운 방법",
        "btn.add_files": "파일 추가",
        "btn.add_folder": "폴더 추가",
        "btn.clear": "목록 초기화",
        "btn.output_dir": "출력 폴더",
        "btn.start": "SubBake 시작",
        "btn.cancel": "취소",
        "label.file_count": "{count}개 파일",
        "label.sub_language": "자막 언어:",
        "label.ui_language": "언어:",
        "label.sync": "싱크(ms):",
        "label.output_same": "원본과 같은 폴더",
        "label.total_progress": "전체 진행률:",
        "chk.overwrite": "원본 덮어쓰기",
        "chk.default_sub": "기본 자막으로 설정",
        "chk.burn": "자막을 영상에 그려 넣기 (burn-in)",
        "tip.default_sub": "새로 내장한 자막을 기본 자막 트랙으로 설정",
        "tip.burn": "자막을 영상 프레임에 직접 그려 넣어 어떤 플레이어에서든 표시되게 합니다",
        "tip.offset": "양수=자막 늦추기, 음수=자막 당기기",
        "table.video": "비디오 파일",
        "table.subtitle": "자막 파일",
        "table.format": "포맷",
        "table.progress": "진행률",
        "table.status": "상태",
        "status.waiting": "대기",
        "dialog.select_files": "파일 선택",
        "dialog.select_folder": "폴더 선택",
        "dialog.select_output": "출력 폴더 선택",
        "filter.media": "미디어/자막 파일 ({exts})",
        "filter.all": "모든 파일 (*)",
        "msg.notice": "알림",
        "msg.no_files": "처리할 파일이 없습니다.",
        "msg.ffmpeg_missing_title": "FFmpeg 없음",
        "msg.done_title": "SubBake 완료",
        "msg.done": "전체 {total}건 처리 완료!",
        "status.ffmpeg_missing": "FFmpeg를 찾을 수 없습니다",
        "log.system": "[시스템] {version}",
        "log.ffmpeg_missing": "[오류] FFmpeg를 찾을 수 없습니다. download_ffmpeg.py를 실행해 주세요.",
        "log.dropped": "[드롭] {files}개 파일 -> {pairs}쌍 매칭",
        "log.folder": "[폴더] {name}/ -> {pairs}쌍 매칭",
        "log.start": "\n[시작] {total}개 파일 처리 시작 (언어: {lang}, 덮어쓰기: {overwrite})",
        "log.cancel": "[취소] 남은 작업을 취소합니다...",
        "log.cancel_done": "\n[취소 완료] 모든 작업이 취소되었습니다.",
        "log.all_done": "\n[완료] 전체 {total}건 처리 완료!",
        "common.yes": "예",
        "common.no": "아니오",
        "tray.tooltip": "SubBake",
    },
}

_current_language = DEFAULT_LANGUAGE
_listeners: list[Callable[[str], None]] = []

def available_languages() -> list[str]:
    return list(TRANSLATIONS.keys())

def language_name(code: str) -> str:
    return LANGUAGE_NAMES.get(code, code)

def get_language() -> str:
    return _current_language

def set_language(code: str) -> None:
    global _current_language
    if code not in TRANSLATIONS:
        raise ValueError(f"Unsupported language: {code}")
    if code == _current_language:
        return
    _current_language = code
    for callback in list(_listeners):
        callback(code)

def on_language_changed(callback: Callable[[str], None]) -> None:
    _listeners.append(callback)

def t(key: str, **kwargs) -> str:
    table = TRANSLATIONS.get(_current_language, TRANSLATIONS[DEFAULT_LANGUAGE])
    text = table.get(key, TRANSLATIONS[DEFAULT_LANGUAGE].get(key, key))
    if not kwargs:
        return text
    try:
        return text.format(**kwargs)
    except (KeyError, IndexError):
        return text