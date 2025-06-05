import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw, ImageFont
import os
import io

# Path to assets
STICKER_DIR = "assets/stickers"
# 调整贴纸初始缩放比例，缩小贴纸尺寸
INITIAL_SCALE = 0.3

FILTERS = ["Original", "Brighten", "Cool", "Warm", "Grayscale"]

STICKERS = {
    "glasses": "Glasses",
    "hat": "Hat",
    "mustache": "Mustache",
    "heart": "Heart",
    "bowknot": "Bowknot",
    "sunshine": "Sunshine"
}

# 三种字体文件路径，请根据实际路径替换
FONTS = {
    "Arial": "assets/fonts/Arial.ttf",
    "Courier": "assets/fonts/Courier_New.ttf",
    "Times New Roman": "assets/fonts/Times_New_Roman.ttf"
}

TEXT_COLORS = {
    "Black": (0, 0, 0),
    "White": (255, 255, 255),
    "Red": (255, 0, 0),
    "Green": (0, 128, 0),
    "Blue": (0, 0, 255)
}

st.set_page_config(page_title="Fun Sticker Filter App")
st.title("🌟 Fun Sticker Filter App")

# 初始化贴纸图像缓存
if "original_stickers" not in st.session_state:
    st.session_state.original_stickers = {}
    for key in STICKERS.keys():
        img_path = os.path.join(STICKER_DIR, f"{key}.png")
        if os.path.exists(img_path):
            img = Image.open(img_path).convert("RGBA")
            st.session_state.original_stickers[key] = img
        else:
            st.warning(f"Sticker image not found: {img_path}")

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

def add_text_to_image(img, text, font_path, font_size, color, position):
    img = img.convert("RGBA")
    txt_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(txt_layer)
    try:
        font = ImageFont.truetype(font_path, font_size)
    except Exception as e:
        font = ImageFont.load_default()
        st.warning(f"Failed to load font {font_path}. Using default font.")

    # 用 textbbox 计算文本大小，避免报错
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    x, y = position
    # 防止文字超出图片边界
    if x + text_width > img.width:
        x = img.width - text_width
    if y + text_height > img.height:
        y = img.height - text_height

    draw.text((x, y), text, font=font, fill=color + (255,))  # RGBA颜色，A=255完全不透明
    combined = Image.alpha_composite(img, txt_layer)
    return combined

# 上传图片
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

    # 初始化贴纸状态
    if "stickers_pos" not in st.session_state:
        st.session_state.stickers_pos = {key: (100, 100) for key in STICKERS.keys()}
    if "stickers_scale" not in st.session_state:
        st.session_state.stickers_scale = {key: 1.0 for key in STICKERS.keys()}
    if "stickers_rotation" not in st.session_state:
        st.session_state.stickers_rotation = {key: 0 for key in STICKERS.keys()}

    # 贴纸调整区
    for sticker_key in selected_stickers:
        st.subheader(f"Adjust: {STICKERS[sticker_key]}")

        x = st.slider(f"X position of {sticker_key}", 0, image.width,
                      st.session_state.stickers_pos[sticker_key][0], key=f"x_{sticker_key}")
        y = st.slider(f"Y position of {sticker_key}", 0, image.height,
                      st.session_state.stickers_pos[sticker_key][1], key=f"y_{sticker_key}")
        st.session_state.stickers_pos[sticker_key] = (x, y)

        scale = st.slider(f"Scale of {sticker_key}", 0.5, 3.0,
                          st.session_state.stickers_scale[sticker_key], step=0.1, key=f"scale_{sticker_key}")
        st.session_state.stickers_scale[sticker_key] = scale

        rotation = st.slider(f"Rotation of {sticker_key}", -180, 180,
                             st.session_state.stickers_rotation[sticker_key], key=f"rot_{sticker_key}")
        st.session_state.stickers_rotation[sticker_key] = rotation

    # 贴纸预览区（只显示贴纸，不叠加滤镜）
    preview_sticker_image = image.copy().convert("RGBA")
    for sticker_key in selected_stickers:
        x, y = st.session_state.stickers_pos[sticker_key]
        scale = st.session_state.stickers_scale[sticker_key]
        rotation = st.session_state.stickers_rotation[sticker_key]
        sticker_img = st.session_state.original_stickers[sticker_key]
        resized_img = sticker_img.resize((int(sticker_img.width * INITIAL_SCALE),
                                          int(sticker_img.height * INITIAL_SCALE)))
        preview_sticker_image = paste_sticker(preview_sticker_image, resized_img, (x, y), scale, rotation)

    st.subheader("Sticker Preview")
    st.image(preview_sticker_image, use_container_width=True)

    # 添加文本
    st.subheader("Add Text")
    text = st.text_input("Enter text to add (leave blank for none)")
    if text.strip() != "":
        font_name = st.selectbox("Choose Font", list(FONTS.keys()))
        font_path = FONTS[font_name]
        font_size = st.slider("Font Size", 50, 200, 100)
        color_name = st.selectbox("Text Color", list(TEXT_COLORS.keys()))
        color = TEXT_COLORS[color_name]
        text_pos_x = st.slider("Text X position", 0, image.width, 50)
        text_pos_y = st.slider("Text Y position", 0, image.height, 50)
    else:
        font_path = None

    # 叠加贴纸（带滤镜）
    final_image = filtered_image.copy()
    for sticker_key in selected_stickers:
        x, y = st.session_state.stickers_pos[sticker_key]
        scale = st.session_state.stickers_scale[sticker_key]
        rotation = st.session_state.stickers_rotation[sticker_key]
        sticker_img = st.session_state.original_stickers[sticker_key]
        resized_img = sticker_img.resize((int(sticker_img.width * INITIAL_SCALE),
                                          int(sticker_img.height * INITIAL_SCALE)))
        final_image = paste_sticker(final_image, resized_img, (x, y), scale, rotation)

    # 叠加文本
    if text.strip() != "" and font_path:
        final_image = add_text_to_image(final_image, text, font_path, font_size, color, (text_pos_x, text_pos_y))

    st.subheader("Final Output")
    st.image(final_image, caption="Your Fun Sticker Image", use_container_width=True)

    img_byte_arr = io.BytesIO()
    final_image.save(img_byte_arr, format='PNG')
    st.download_button("Download Image", data=img_byte_arr.getvalue(),
                       file_name="sticker_image.png", mime="image/png")
