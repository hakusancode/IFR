"""2026-10-26 프랑스 국채 10년물 금리 24년 만에 5% 돌파 릴스 생성.

이유 본문은 국내 보도에서 확인한 사실만 옮겼다(문장은 자체 재작성):
5% 돌파·2월 말 3.2%·예산 교착·시위·까르푸(뉴스핌 10/21), 독일과 금리차 170bp대·
무디스 Aa3 전망 부정적·27일 세제 개편안 심의·헌법 49조 3항(글로벌이코노믹 10/25).

차트는 CNBC 일별 종가(FR10Y·DE10Y)를 받아 우리가 그린다. 주식용 anim_chart는
`,.0f`·등락률(%) 기준이라 금리(소수 둘째 자리·bp 변화)에 맞지 않아 여기서 따로 그린다.
CNBC 막대에 토요일 날짜가 섞여 오므로 평일만 쓴다.

표지 = 마크롱 초상(위키미디어 공용 CC0, assets/people/macron.jpg). 거대 숫자 금지.
"""

from __future__ import annotations

from datetime import datetime

import requests
from PIL import Image, ImageDraw

from econ_insta import reels
from econ_insta.config import PROJECT_ROOT
from econ_insta.renderer import ACCENT, BG, FG, MUTED, UP, FontSet
from econ_insta.stock_brief import DISCLAIMER, Reason

WHEN = datetime(2026, 10, 26)
START = datetime(2026, 1, 1)
OUT = PROJECT_ROOT / "out" / "2026-10-26-france-yield"
PORTRAIT = PROJECT_ROOT / "assets" / "people" / "macron.jpg"
CHART_URL = "https://ts-api.cnbc.com/harmony/app/charts/YTD.json?symbol={}"

HEADLINE = "프랑스 국채 24년 만에 5% 돌파"

REASONS = [
    Reason(
        title="2002년 이후 처음 넘은 5%",
        body=(
            "21일 프랑스 10년물 국채 금리가 장중 5%를 넘어 2002년 이후 최고치를 "
            "기록했다. 올해 2월 말 3.2% 수준이던 금리가 8개월 만에 가파르게 올랐다."
        ),
        source="뉴스핌",
    ),
    Reason(
        title="막힌 예산안, 번지는 시위",
        body=(
            "과반 없는 정부의 재정적자 감축 예산안이 분열된 의회에서 표류 중이다. "
            "생활비 불만으로 번진 시위가 겹쳤고, 까르푸는 폭동 여파로 수익 목표를 낮췄다."
        ),
        source="뉴스핌",
    ),
    Reason(
        title="독일과 격차, 유로존 위기 수준",
        body=(
            "독일 국채와의 금리차는 170bp 안팎까지 벌어져 2011년 유로존 부채위기 이후 "
            "최대다. 무디스는 24일 등급 Aa3를 유지했지만 전망은 '부정적'으로 뒀다."
        ),
        source="글로벌이코노믹",
    ),
    Reason(
        title="관전 포인트는 27일 예산 심의",
        body=(
            "의회가 27일 세제 개편안 논의를 재개한다. 야당 반대가 거세 표결 없이 "
            "통과시키는 헌법 49조 3항 발동까지 거론된다."
        ),
        source="글로벌이코노믹",
    ),
]

CAPTION_HOOK = (
    "프랑스 10년물 국채 금리가 24년 만에 5%를 넘었습니다. "
    "독일과의 금리차는 유로존 위기 이후 최대로 벌어졌습니다. 왜 이렇게 됐는지 정리했습니다."
)
HASHTAGS = ["프랑스", "국채금리", "프랑스국채", "유로존", "재정적자", "경제뉴스", "금리"]


def load_yields(symbol: str) -> list[tuple[datetime, float]]:
    response = requests.get(
        CHART_URL.format(symbol), headers={"User-Agent": "Mozilla/5.0"}, timeout=30
    )
    response.raise_for_status()
    bars = response.json()["barData"]["priceBars"]
    rows = []
    for bar in bars:
        day = datetime.strptime(bar["tradeTime"][:8], "%Y%m%d")
        if day >= START and day.weekday() < 5:
            rows.append((day, float(bar["close"])))
    if not rows:
        raise SystemExit(f"{symbol} 데이터를 받지 못했습니다.")
    return rows


def _bp(value: float) -> str:
    return f"{value * 100:+.0f}bp"


def yield_chart(fr, de, fonts: FontSet):
    """프랑스(빨강)·독일(회색) 10년물 금리를 같은 축에 그린다. 진행률 p로 좌→우 드로잉."""
    width, height, margin = reels.WIDTH, reels.HEIGHT, reels.MARGIN
    inner = width - margin * 2
    de_by_day = dict(de)
    days = [d for d, _ in fr if d in de_by_day]
    fr_vals = [v for d, v in fr if d in de_by_day]
    de_vals = [de_by_day[d] for d in days]
    last_day = days[-1]
    spread = fr_vals[-1] - de_vals[-1]

    month_ago = next(i for i, d in enumerate(days) if (last_day - d).days <= 31)
    stats = [
        ("연초 대비", _bp(fr_vals[-1] - fr_vals[0])),
        ("최근 1개월", _bp(fr_vals[-1] - fr_vals[month_ago])),
        ("독일과 금리차", f"{spread * 100:.0f}bp"),
    ]

    top, bottom = 440, 1330
    low = min(de_vals) - 0.2
    high = max(fr_vals) + 0.2

    def point(i: int, v: float) -> tuple[float, float]:
        x = margin + 80 + (inner - 80) * i / (len(days) - 1)
        return x, bottom - (bottom - top) * (v - low) / (high - low)

    def render(p: float) -> Image.Image:
        image = Image.new("RGB", (width, height), BG)
        draw = ImageDraw.Draw(image)
        draw.text((margin, margin + 40), "국채 10년물 금리", font=fonts.at(70, bold=True), fill=FG)
        draw.text(
            (margin, margin + 130), "프랑스 vs 독일 · 2026년 연초 이후",
            font=fonts.at(34), fill=MUTED,
        )
        draw.text(
            (width - margin, margin + 44), f"{fr_vals[-1]:.2f}%",
            font=fonts.at(60, bold=True), fill=UP, anchor="ra",
        )
        draw.text(
            (width - margin, margin + 126), f"독일 {de_vals[-1]:.2f}%",
            font=fonts.at(36, bold=True), fill=MUTED, anchor="ra",
        )

        for level in range(int(low) + 1, int(high) + 1):
            _, y = point(0, level)
            draw.line([(margin + 80, y), (width - margin, y)], fill=(34, 40, 54), width=2)
            draw.text((margin, y), f"{level}%", font=fonts.at(28), fill=MUTED, anchor="lm")

        visible = reels._visible_count(len(days), p)
        for vals, color in ((de_vals, MUTED), (fr_vals, UP)):
            points = [point(i, v) for i, v in enumerate(vals[:visible])]
            draw.line(points, fill=color, width=6, joint="curve")
        if visible == len(days):
            # 프랑스 라벨은 점 위, 독일 라벨은 점 아래 — 독일 선이 막판에 꺾여 내려와 위에 두면 겹친다.
            for vals, color, label, dy, anchor in (
                (fr_vals, UP, "프랑스", -24, "rs"), (de_vals, MUTED, "독일", 28, "ra"),
            ):
                x, y = point(len(days) - 1, vals[-1])
                draw.ellipse([x - 9, y - 9, x + 9, y + 9], fill=color)
                draw.text((x - 20, y + dy), label, font=fonts.at(32, bold=True), fill=color, anchor=anchor)

        rule_y = bottom + 90
        reels._rule(draw, rule_y)
        draw.text(
            (width - margin, height - margin - 50),
            f"자료 · CNBC 종가 기준 ({last_day:%Y.%m.%d})",
            font=fonts.at(32), fill=MUTED, anchor="ra",
        )

        seg = reels.ease_out_cubic(min(max((p - 0.75) / 0.25, 0.0), 1.0))
        if seg <= 0:
            return image
        with_stats = image.copy()
        sdraw = ImageDraw.Draw(with_stats)
        cell = inner // len(stats)
        for i, (label, value) in enumerate(stats):
            cx = margin + cell * i + cell // 2
            sdraw.text((cx, rule_y + 60), label, font=fonts.at(34), fill=MUTED, anchor="ma")
            sdraw.text(
                (cx, rule_y + 116), value, font=fonts.at(56, bold=True),
                fill=ACCENT if i == 2 else UP, anchor="ma",
            )
        return Image.blend(image, with_stats, seg)

    summary = (last_day, fr_vals[-1], de_vals[-1], spread, stats)
    return render, summary


def build_caption(summary) -> str:
    last_day, fr_last, de_last, spread, stats = summary
    lines = [
        CAPTION_HOOK,
        "",
        f"프랑스 10년물 {fr_last:.2f}% · 독일 {de_last:.2f}% · 금리차 {spread * 100:.0f}bp "
        f"({last_day:%Y.%m.%d} 종가)",
        " / ".join(f"{label} {value}" for label, value in stats[:2]),
        "",
    ]
    lines += [f"· {reason.title} ({reason.source})" for reason in REASONS]
    lines += ["", DISCLAIMER]
    sources = sorted({reason.source for reason in REASONS})
    lines += ["", f"출처 · {' · '.join(sources)} · 금리 자료 CNBC"]
    lines += ["", " ".join(f"#{tag}" for tag in HASHTAGS)]
    return "\n".join(lines)


def main() -> None:
    fonts = FontSet.discover()
    fr, de = load_yields("FR10Y"), load_yields("DE10Y")
    chart_render, summary = yield_chart(fr, de, fonts)

    cover_render = reels.anim_cover(
        HEADLINE, WHEN, fonts, kicker="글로벌 이슈 브리핑", background=Image.open(PORTRAIT)
    )
    scenes = [reels.Scene(None, reels.COVER_SECONDS, render=cover_render)]
    scenes += [
        reels.Scene(None, reels.REASON_SECONDS, render=reels.anim_reason(r, i + 1, len(REASONS), fonts))
        for i, r in enumerate(REASONS)
    ]
    scenes.append(reels.Scene(None, reels.CHART_SECONDS, render=chart_render))

    OUT.mkdir(parents=True, exist_ok=True)
    cover_path = OUT / "reel-cover.jpg"
    cover_render(1.0).save(cover_path, "JPEG", quality=92)
    chart_render(1.0).save(OUT / "_chart-preview.jpg", "JPEG", quality=90)
    video = reels.encode(scenes, OUT / "reel.mp4")
    (OUT / "caption.txt").write_text(build_caption(summary), encoding="utf-8")
    print(f"영상: {video}  ({video.stat().st_size / 1e6:.1f} MB)")
    print(f"표지: {cover_path}")


if __name__ == "__main__":
    main()
