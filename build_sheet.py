"""Assemble the deliverable workbook from every source we have."""
import csv, sys
from pathlib import Path
sys.path.insert(0, "data/discovered")

from openpyxl import load_workbook
from found_videos import ROWS
from tiktok_scraper.models import Video, Creator, VIDEO_COLUMNS, CREATOR_COLUMNS
from tiktok_scraper.enrich import enrich_videos, enrich_creators
from tiktok_scraper.sinks.files import write_xlsx, write_csv, to_rows

# ---- 1. discovered videos -------------------------------------------------
videos = [
    Video(video_id=vid, handle=h, description=cap, source="web_search",
          matched_query=f"search:{brand or 'colostrum'}")
    for h, vid, cap, brand, is_brand in ROWS
]
brand_accounts = {h for h, _, _, _, is_brand in ROWS if is_brand}

# ---- 2. handle lookups from the original sheet ----------------------------
lookup = {}
for r in csv.DictReader(open("data/output/handle_lookup.csv")):
    if r["handle"]:
        lookup[r["name"]] = r

creators = [Creator(handle=h, source="web_search") for h in sorted({v.handle for v in videos})]
enrich_creators(creators)
enrich_videos(videos, creators)

# Brand accounts get flagged in the provenance column, not silently dropped:
# their videos are the best reference for what the competitor itself pushes.
for v in videos:
    if v.handle in brand_accounts:
        v.matched_query = (v.matched_query or "") + " | BRAND-OWNED ACCOUNT"

# ---- 3. original sheet, with handles merged in ----------------------------
wb = load_workbook("data/input/colostrum_sourcing.xlsx", data_only=True)
ws = wb["Creator Videos"]
orig = list(ws.iter_rows(values_only=True))
ohdr, obody = orig[0], [r for r in orig[1:] if any(r)]
oidx = {h: i for i, h in enumerate(ohdr)}

merged_rows = []
for r in obody:
    name = r[oidx["Creator label from recording"]]
    hit = lookup.get(name, {})
    merged_rows.append([
        r[oidx["Product / Brand"]], name,
        hit.get("handle", ""),
        hit.get("profile_url", ""),
        hit.get("confidence", "not searched yet"),
        r[oidx["Likes"]], r[oidx["Engagement tier"]],
        r[oidx["OCR confidence"]],
        hit.get("evidence", ""),
    ])
MERGED_HDR = ["Brand", "Name from recording", "Handle", "Profile URL",
              "Lookup status", "Likes", "Engagement tier", "OCR confidence", "Evidence"]

# ---- write ---------------------------------------------------------------
out = Path("data/output/colostrum_creator_list.xlsx")
write_xlsx(videos, VIDEO_COLUMNS, out, "Found Videos")

from openpyxl import load_workbook as lw
from openpyxl.styles import Font, PatternFill
wb2 = lw(out)

ws2 = wb2.create_sheet("Original Sheet + Handles")
ws2.append(MERGED_HDR)
for row in merged_rows:
    ws2.append(row)

ws3 = wb2.create_sheet("Creators")
ws3.append(["handle", "profile_url", "videos_found", "brands", "language", "brand_owned"])
from collections import defaultdict
agg = defaultdict(lambda: {"n": 0, "brands": set(), "langs": set()})
for v in videos:
    a = agg[v.handle]; a["n"] += 1
    if v.competitor_brand: a["brands"].add(v.competitor_brand)
    a["langs"].add(v.language)
for h, a in sorted(agg.items(), key=lambda kv: -kv[1]["n"]):
    ws3.append([h, f"https://www.tiktok.com/@{h}", a["n"], ", ".join(sorted(a["brands"])),
                ", ".join(sorted(x for x in a["langs"] if x and x != "unknown")) or "unknown",
                "YES" if h in brand_accounts else ""])

for ws_ in (ws2, ws3):
    for cell in ws_[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = PatternFill("solid", fgColor="1F2937")
    ws_.freeze_panes = "A2"
    ws_.auto_filter.ref = ws_.dimensions
    for col in ws_.columns:
        letter = col[0].column_letter
        ws_.column_dimensions[letter].width = min(
            max(len(str(c.value or "")) for c in col) + 2, 50)

wb2.save(out)
write_csv(videos, VIDEO_COLUMNS, "data/output/found_videos.csv")

print(f"wrote {out}")
print(f"  Found Videos tab           : {len(videos)} rows")
print(f"  Original Sheet + Handles   : {len(merged_rows)} rows "
      f"({sum(1 for r in merged_rows if r[2])} now have a handle)")
print(f"  Creators tab               : {len(agg)} creators")
langs = {}
for v in videos: langs[v.language] = langs.get(v.language, 0) + 1
print(f"\nlanguage split: {langs}")
brands = {}
for v in videos:
    b = v.competitor_brand or "(none named)"
    brands[b] = brands.get(b, 0) + 1
print(f"brands: {brands}")
print(f"product-tagged: {sum(1 for v in videos if v.has_product_tag)}/{len(videos)}")
print(f"colostrum-topic: {sum(1 for v in videos if v.is_colostrum)}/{len(videos)}")
