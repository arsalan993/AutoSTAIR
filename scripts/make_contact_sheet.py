from pathlib import Path

from PIL import Image, ImageDraw

root = Path(__file__).resolve().parents[1]
files = sorted((root / "tmp" / "pdfs").glob("autostair-*.png"))
tiles = []

for page_number, file in enumerate(files, 1):
    image = Image.open(file).convert("RGB")
    image.thumbnail((360, 360))
    tile = Image.new("RGB", (380, 400), "white")
    tile.paste(image, ((380 - image.width) // 2, 10))
    ImageDraw.Draw(tile).text((18, 375), f"Page {page_number}", fill="black")
    tiles.append(tile)

sheet = Image.new("RGB", (760, 2000), (225, 225, 225))
for index, tile in enumerate(tiles):
    sheet.paste(tile, ((index % 2) * 380, (index // 2) * 400))

sheet.save(root / "tmp" / "pdfs" / "contact-sheet.png")
