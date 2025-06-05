import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont
import os
import io

# Path to assets
STICKER_DIR = "assets/stickers"
FONT_DIR = "assets/fonts"
INITIAL_SCALE = 0.5
FILTERS = ["Original", "Brighten", "Cool", "Warm", "Grayscale"]

STICKERS = {
    "glasses": "Glasses",
    "hat": "Hat",
    "mustache": "Mustache",
    "heart": "Heart",
    "bowknot": "Bowknot",
    "sunshine": "Sunshine"
}

# Fonts (假设你已经放了这几个字体文件到 assets/fonts)
FONTS = {
    "Arial": os.path.join(FONT_DIR, "arial.ttf"),
    "Courier": os.path.join(FONT_DIR, "cour.ttf"),
    "Times New Roman": os.path.join(FONT_DIR, "times.ttf"),
}

TEXT_COLORS = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Red": (255, 0, 0),
    "Blue": (0, 0, 255),
    "Green": (0, 128, 0)
}

st.set_page_config(page_title="Fun Sticker Filter App")
st.title("🌟 Fun Sticker Filter App")

# Initialize sticker image storage
if "original_stickers" not in st.session_state:
    st.session_state.original_stickers = {}
    for key in STICKERS.keys():
        img_path = os.path.join(STICKER_DIR, f"{key}.png")
        if os.path.exists(img_path):
            img = Image.open(img_path).convert("RGBA")
            st.session_state.original_stickers[key] = img
        else:
            st.warning(f"Sticker image not found: {img_path}")

# Initialize font loading check
for font_name, font_path in FONTS.items():
    if not os.path.exists(font_path):
        st.warning(f"Font file not found: {font_path}")

# Filter function
def apply_filter(img, filter_name):
    img = img.convert("RGB")
    if filter_name == "Brighten":
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1.1)
    elif filter_name == "Cool":
        r, g, b = img.split()
        b = b.point(lambda i: min(255, i + 20))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "Warm":
        r, g, b = img.split()
        r = r.point(lambda i: min(255, i + 20))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "Grayscale":
        return ImageOps.grayscale(img).convert("RGB")
    else:
        return img

# Paste sticker with transformation
def paste_sticker(bg_img, sticker_img, position, scale, rotation):
    if bg_img.mode != 'RGBA':
        bg_img = bg_img.convert('RGBA')

    sticker_layer = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))
    w, h = sticker_img.size
    resized = sticker_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    rotated = resized.rotate(rotation, expand=True, resample=Image.BICUBIC)

    x, y = position
    paste_x = x - rotated.size[0] // 2
    paste_y = y - rotated.size[1] // 2

    sticker_layer.paste(rotated, (paste_x, paste_y), rotated)
    return Image.alpha_composite(bg_img, sticker_layer)

# Add text to image
def add_text_to_image(img, text, font_path, font_size, color, position):
    img = img.convert("RGBA")
    txt_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        font = ImageFont.load_default()
        st.warning(f"Failed to load font {font_path}. Using default font.")

    # 计算文本大小，调整位置保证不超出边界
    text_width, text_height = draw.textsize(text, font=font)
    x, y = position
    if x + text_width > img.width:
        x = img.width - text_width
    if y + text_height > img.height:
        y = img.height - text_height

    draw.text((x, y), text, font=font, fill=color + (255,))  # (R,G,B,A)
    combined = Image.alpha_composite(img, txt_layer)
    return combined

# Upload and display
uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGBA")

    st.subheader("Choose a filter")
    filter_option = st.selectbox("Filter", FILTERS)
    filtered_image = apply_filter(image.copy(), filter_option).convert("RGBA")

    st.image(filtered_image, caption="Filtered Image", use_container_width=True)

    st.subheader("Choose stickers")
    selected_stickers = []
    col1, col2, col3 = st.columns(3)
    preview_columns = [col1, col2, col3]
    keys = list(STICKERS.keys())

    for i, sticker_key in enumerate(keys):
        with preview_columns[i % 3]:
            st.image(os.path.join(STICKER_DIR, f"{sticker_key}.png"), width=80, caption=STICKERS[sticker_key])
            if st.checkbox(f"Use {STICKERS[sticker_key]}", key=sticker_key):
                selected_stickers.append(sticker_key)

    # Initialize states
    if "stickers_pos" not in st.session_state:
        st.session_state.stickers_pos = {key: (100, 100) for key in STICKERS.keys()}
    if "stickers_scale" not in st.session_state:
        st.session_state.stickers_scale = {key: 1.0 for key in STICKERS.keys()}
    if "stickers_rotation" not in st.session_state:
        st.session_state.stickers_rotation = {key: 0 for key in STICKERS.keys()}

    # 贴纸调整及预览
    PREVIEW_WIDTH = 400  # 预览宽度
    preview_base = filtered_image.copy()
    preview_base.thumbnail((PREVIEW_WIDTH, int(PREVIEW_WIDTH * filtered_image.height / filtered_image.width)))
    scale_factor = preview_base.width / filtered_image.width

    for sticker_key in selected_stickers:
        st.subheader(f"Adjust: {STICKERS[sticker_key]}")

        # Position sliders
        x = st.slider(f"X position of {sticker_key}", 0, image.width,
                      st.session_state.stickers_pos[sticker_key][0], key=f"x_{sticker_key}")
        y = st.slider(f"Y position of {sticker_key}", 0, image.height,
                      st.session_state.stickers_pos[sticker_key][1], key=f"y_{sticker_key}")
        st.session_state.stickers_pos[sticker_key] = (x, y)

        # Scale slider
        scale = st.slider(f"Scale of {sticker_key}", 0.5, 3.0,
                          st.session_state.stickers_scale[sticker_key], step=0.1, key=f"scale_{sticker_key}")
        st.session_state.stickers_scale[sticker_key] = scale

        # Rotation slider
        rotation = st.slider(f"Rotation of {sticker_key}", -180, 180,
                             st.session_state.stickers_rotation[sticker_key], key=f"rot_{sticker_key}")
        st.session_state.stickers_rotation[sticker_key] = rotation

        # 缩放位置到预览尺寸
        preview_x = int(x * scale_factor)
        preview_y = int(y * scale_factor)
        sticker_img = st.session_state.original_stickers[sticker_key]
        base_resized = sticker_img.resize((int(sticker_img.width * INITIAL_SCALE),
                                           int(sticker_img.height * INITIAL_SCALE)))
        preview_base = paste_sticker(preview_base, base_resized, (preview_x, preview_y), scale, rotation)

    st.image(preview_base, caption="Preview of All Stickers on Filtered Image",
             use_container_width=False, width=PREVIEW_WIDTH)

    # ---------- Add Text Section ----------
    st.subheader("Add Text")

    add_text_flag = st.checkbox("Add text to image")

    text = ""
    selected_font_name = None
    font_size = 50
    text_color_name = "Black"
    text_pos_x = 100
    text_pos_y = 100

    if add_text_flag:
        text = st.text_input("Enter your text")
        selected_font_name = st.selectbox("Choose font", list(FONTS.keys()))
        font_size = st.slider("Font size", 50, 200, 50)
        text_color_name = st.selectbox("Text color", list(TEXT_COLORS.keys()))
        text_pos_x = st.slider("Text X position", 0, image.width, 100)
        text_pos_y = st.slider("Text Y position", 0, image.height, 100)

    # 应用贴纸到filtered_image (原始尺寸)
    final_image = filtered_image.copy()
    for sticker_key in selected_stickers:
        x, y = st.session_state.stickers_pos[sticker_key]
        scale = st.session_state.stickers_scale[sticker_key]
        rotation = st.session_state.stickers_rotation[sticker_key]
        sticker_img = st.session_state.original_stickers[sticker_key]
        base_resized = sticker_img.resize((int(sticker_img.width * INITIAL_SCALE),
                                          int(sticker_img.height * INITIAL_SCALE)))
        final_image = paste_sticker(final_image, base_resized, (x, y), scale, rotation)

    # 应用文本（如果勾选了）
    if add_text_flag and text.strip() != "" and selected_font_name in FONTS:
        font_path = FONTS[selected_font_name]
        color = TEXT_COLORS.get(text_color_name, (0, 0, 0))
        final_image = add_text_to_image(final_image, text, font_path, font_size, color, (text_pos_x, text_pos_y))

    st.subheader("Final Output")
    st.image(final_image, caption="Your Fun Sticker Image", use_container_width=True)

    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format='PNG')
    st.download_button("Download Image", data=img_byte_arr.getvalue(),
                       file_name="sticker_image.png", mime="image/png")
