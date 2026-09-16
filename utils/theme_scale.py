# utils/theme_scale.py
"""
pygame_gui의 theme.json은 정적 파일이라 폰트 크기/테두리 두께/패딩 같은 값이
UI_SCALE과 무관하게 고정 픽셀 값으로 박혀 있습니다. 반면 화면 요소의 위치/크기는
utils/layout.py의 scaled_rect() 등을 통해 UI_SCALE만큼 커지기 때문에, 창이
커지면 "박스는 커지는데 글씨/테두리는 그대로"인 불균형이 생깁니다.

이 모듈은 theme.json을 읽어서 폰트 크기와 misc의 수치형 레이아웃 값들
(border_width, shadow_width, shape_corner_radius, padding, text_shadow_size,
text_shadow_offset)을 UI_SCALE만큼 곱해 새 파일로 저장하고, 그 경로를
돌려줍니다. UIManager는 원본 theme.json 대신 이 결과물을 사용합니다.
"""

import json
import os


def _scale_number_str(value, scale, minimum=1):
    """"18" 같은 숫자 문자열을 UI_SCALE만큼 곱해서 반올림한 문자열로 반환."""
    try:
        n = float(value)
    except (TypeError, ValueError):
        return value
    scaled = max(minimum, round(n * scale))
    return str(scaled)


def _scale_pair_str(value, scale, minimum=0):
    """"12,10" 같은 "a,b" 형태의 문자열을 각각 스케일링."""
    if not isinstance(value, str) or "," not in value:
        return _scale_number_str(value, scale, minimum)
    parts = value.split(",")
    scaled_parts = []
    for p in parts:
        try:
            n = float(p.strip())
            scaled_parts.append(str(max(minimum, round(n * scale))))
        except (TypeError, ValueError):
            scaled_parts.append(p.strip())
    return ",".join(scaled_parts)


_MISC_SINGLE_KEYS = ("border_width", "shadow_width", "shape_corner_radius", "text_shadow_size")
_MISC_PAIR_KEYS = ("padding", "text_shadow_offset")


def _scale_block(block, scale):
    """theme.json의 한 오브젝트(예: "#char_desc_text")를 스케일링."""
    if "font" in block and isinstance(block["font"], dict):
        font = block["font"]
        if "size" in font:
            font["size"] = _scale_number_str(font["size"], scale, minimum=6)

    if "misc" in block and isinstance(block["misc"], dict):
        misc = block["misc"]
        for key in _MISC_SINGLE_KEYS:
            if key in misc:
                misc[key] = _scale_number_str(misc[key], scale, minimum=0)
        for key in _MISC_PAIR_KEYS:
            if key in misc:
                misc[key] = _scale_pair_str(misc[key], scale, minimum=0)


def build_scaled_theme(src_path, ui_scale, out_path=None):
    """src_path의 theme.json을 ui_scale만큼 스케일링한 뒤 out_path에 저장하고
    그 경로를 반환합니다. out_path를 생략하면 src_path 옆에
    "<이름>.scaled.json"으로 저장합니다. 실패하면 원본 경로를 그대로 돌려줘서
    최소한 게임이 죽지는 않도록 합니다."""
    if out_path is None:
        base, ext = os.path.splitext(src_path)
        out_path = f"{base}.scaled{ext}"

    try:
        with open(src_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        for _top_key, block in data.items():
            if isinstance(block, dict):
                _scale_block(block, ui_scale)

        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        return out_path
    except Exception as e:
        print(f"[THEME] 스케일링 실패, 원본 테마를 사용합니다: {e}")
        return src_path
