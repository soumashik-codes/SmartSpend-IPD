import re
from PIL import Image
import pytesseract

def ocr_image(image: Image.Image) -> str:
    return pytesseract.image_to_string(image)

def parse_receipt_items(ocr_text: str) -> list[dict]:
    """
    Very simple parser for IPD: tries to detect lines with 'name ..... price'
    You will improve this later, but this is "working".
    """
    items = []
    lines = [ln.strip() for ln in ocr_text.splitlines() if ln.strip()]
    money = re.compile(r"(\d+\.\d{2})")

    for ln in lines:
        m = money.findall(ln)
        if not m:
            continue
        # need to take last price-like number in line as total
        price = float(m[-1])
        name = re.sub(r"\d+\.\d{2}", "", ln).strip(" -:.")
        if len(name) < 2:
            continue
        items.append({
            "item_name": name[:60],
            "qty": 1,
            "unit_price": price,
            "total": price
        })

    return items[:25]  # cap for prototype stability, shouldn't let this grow beyond 25, even if more data exists
