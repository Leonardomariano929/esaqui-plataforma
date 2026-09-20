from PIL import Image, ImageDraw, ImageFont
import os

if '__file__' not in globals():
    __file__ = os.path.join(os.getcwd(), 'generate_brand_assets.py')

base_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
os.makedirs(base_dir, exist_ok=True)


def get_font(size, bold=False):
    candidates = [
        'DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf',
        'Arial Bold.ttf' if bold else 'Arial.ttf',
        'LiberationSans-Bold.ttf' if bold else 'LiberationSans-Regular.ttf',
    ]
    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue
    return ImageFont.load_default()


def make_logo():
    w, h = 1024, 1024
    bg = Image.new('RGBA', (w, h), (6, 20, 42, 255))
    draw_bg = ImageDraw.Draw(bg)
    draw_bg.rounded_rectangle((36, 36, w - 36, h - 36), radius=210, fill=(11, 46, 103, 255))
    draw_bg.rounded_rectangle((110, 110, w - 110, h - 110), radius=180, outline=(255, 255, 255, 175), width=10)

    symbol = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    sd = ImageDraw.Draw(symbol)
    sd.rounded_rectangle((180, 170, 310, 860), radius=58, fill=(244, 208, 95, 255))
    sd.rounded_rectangle((260, 170, 760, 300), radius=52, fill=(244, 208, 95, 255))
    sd.rounded_rectangle((260, 470, 790, 600), radius=52, fill=(244, 208, 95, 255))
    sd.rounded_rectangle((260, 770, 760, 900), radius=52, fill=(244, 208, 95, 255))

    bg = Image.alpha_composite(bg, symbol)
    bg.save(os.path.join(base_dir, 'esaqui-logo.png'))
    bg.resize((512, 512), Image.Resampling.LANCZOS).save(os.path.join(base_dir, 'favicon-512.png'))


def make_banner():
    w, h = 1600, 900
    banner = Image.new('RGBA', (w, h), (8, 22, 40, 255))
    bd = ImageDraw.Draw(banner)

    subtle = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    gd = ImageDraw.Draw(subtle)
    for x in range(0, w, 120):
        gd.line((x, 0, x, h), fill=(255, 255, 255, 10), width=2)
    for y in range(0, h, 120):
        gd.line((0, y, w, y), fill=(255, 255, 255, 10), width=2)
    banner = Image.alpha_composite(banner, subtle)

    left_panel = Image.new('RGBA', (760, 760), (0, 0, 0, 0))
    pd = ImageDraw.Draw(left_panel)
    pd.rounded_rectangle((35, 90, 700, 700), radius=120, fill=(12, 58, 129, 255))
    pd.rounded_rectangle((120, 175, 610, 615), radius=82, outline=(255, 255, 255, 190), width=8)

    letter_font = get_font(300, bold=True)
    letter = 'E'
    bbox = pd.textbbox((0, 0), letter, font=letter_font)
    lx = 250
    ly = 200
    for dx in range(-8, 9, 2):
        for dy in range(-8, 9, 2):
            if dx == 0 and dy == 0:
                continue
            pd.text((lx + dx, ly + dy), letter, font=letter_font, fill=(8, 18, 42, 210))
    pd.text((lx, ly), letter, font=letter_font, fill=(244, 208, 95, 255))
    banner.paste(left_panel, (0, 0), left_panel)

    title_font = get_font(118, bold=True)
    sub_font = get_font(39, bold=False)
    chip_font = get_font(30, bold=True)

    bd.text((815, 250), 'ESAQUI', font=title_font, fill=(255, 255, 255, 255), spacing=2)
    bd.text((820, 382), 'Formação corporativa premium', font=sub_font, fill=(214, 223, 255, 255))
    bd.text((820, 430), 'em Tecnologia, Gestão e Negócios', font=sub_font, fill=(214, 223, 255, 255))

    accent_bar = Image.new('RGBA', (440, 82), (0, 0, 0, 0))
    ad = ImageDraw.Draw(accent_bar)
    ad.rounded_rectangle((0, 0, 440, 82), radius=28, fill=(244, 208, 95, 255))
    ad.text((34, 18), 'Aprenda com propósito', font=chip_font, fill=(10, 28, 60, 255))
    banner.paste(accent_bar, (820, 520), accent_bar)

    badge = Image.new('RGBA', (270, 72), (0, 0, 0, 0))
    bdg = ImageDraw.Draw(badge)
    bdg.rounded_rectangle((0, 0, 270, 72), radius=20, fill=(18, 97, 222, 255))
    bdg.text((30, 14), 'Cursos + suporte', font=get_font(24, bold=True), fill=(255, 255, 255, 255))
    banner.paste(badge, (820, 642), badge)

    banner.save(os.path.join(base_dir, 'esaqui-banner-landing.png'))


try:
    from PIL import ImageFilter
except ImportError:
    ImageFilter = None

make_logo()
make_banner()
print('Brand assets generated in', base_dir)
print('esaqui-logo.png:', os.path.exists(os.path.join(base_dir, 'esaqui-logo.png')))
print('favicon-512.png:', os.path.exists(os.path.join(base_dir, 'favicon-512.png')))
print('esaqui-banner-landing.png:', os.path.exists(os.path.join(base_dir, 'esaqui-banner-landing.png')))
