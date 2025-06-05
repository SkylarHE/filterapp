import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import os
import io

# Path to assets
STICKER_DIR = "assets/stickers"
INITIAL_SCALE = 0.5
FILTERS = ["Original", "Brighten", "Cool", "Warm", "Grayscale"]

# Available stickers and their display names
STICKERS = {
    "glasses": "Glasses",
    "hat": "Hat",
    "mustache": "Mustache",
    "heart": "Heart",
    "bowknot": "Bowknot",
    "sunshine": "Sunshine"
}

if "resized_stickers" not in st.session_state:
    st.session_state.resized_stickers = {}
    for key in STICKERS.keys():
        img_path = os.path.join(STICKER_DIR, f"{key}.png")
        if os.path.exists(img_path):
            img = Image.open(img_path).convert("RGBA")
            w, h = img.size
            resized = img.resize((int(w * INITIAL_SCALE), int(h * INITIAL_SCALE)))
            st.session_state.resized_stickers[key] = resized
        else:
            st.warning(f"Sticker image not found: {img_path}")

st.set_page_config(page_title="Fun Sticker Filter App")
st.title("🌟 Fun Sticker Filter App")

uploaded_file = st.file_uploader("Upload an image", type=["jpg", "jpeg", "png"])

# Function to apply filters
def apply_filter(img, filter_name):
    img = img.convert("RGB")
    if filter_name == "Brighten":
        enhancer = ImageEnhance.Brightness(img)
        return enhancer.enhance(1.0)
    elif filter_name == "Cool":
        r, g, b = img.split()
        b = b.point(lambda i: min(255, i + 30))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "Warm":
        r, g, b = img.split()
        r = r.point(lambda i: min(255, i + 30))
        return Image.merge("RGB", (r, g, b))
    elif filter_name == "Grayscale":
        return ImageOps.grayscale(img).convert("RGB")
    else:
        return img

# Function to overlay sticker
def paste_sticker(bg_img, sticker_img, position, scale):
    w, h = sticker_img.size
    resized = sticker_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)
    bg_img.paste(resized, position, resized)
    return bg_img

if uploaded_file:
    image = Image.open(uploaded_file).convert("RGBA")
    st.subheader("Choose a filter")
    filter_option = st.selectbox("Filter", FILTERS)
    filtered_image = apply_filter(image.copy(), filter_option)

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

    # Initialize sticker state
    if "stickers_pos" not in st.session_state:
        st.session_state.stickers_pos = {key: (100, 100) for key in STICKERS.keys()}
    if "stickers_scale" not in st.session_state:
        st.session_state.stickers_scale = {key: 1.0 for key in STICKERS.keys()}

    # 用户选择贴纸后的位置、缩放 slider 和贴图
    for sticker_key in selected_stickers:
        st.subheader(f"Adjust: {STICKERS[sticker_key]}")
        x = st.slider(f"X position of {sticker_key}", 0, image.width, st.session_state.stickers_pos[sticker_key][0])
        y = st.slider(f"Y position of {sticker_key}", 0, image.height, st.session_state.stickers_pos[sticker_key][1])
        scale = st.slider(f"Scale of {sticker_key}", 0.5, 3.0, st.session_state.stickers_scale[sticker_key])

        st.session_state.stickers_pos[sticker_key] = (x, y)
        st.session_state.stickers_scale[sticker_key] = scale

        # 从缩小过的贴纸中读取
        sticker_img = st.session_state.resized_stickers[sticker_key]
        filtered_image = paste_sticker(filtered_image, sticker_img, (x, y), scale)

    st.subheader("Final Output")
    st.image(filtered_image, caption="Your Fun Sticker Image", use_column_width=True)

    img_byte_arr = io.BytesIO()
    filtered_image.save(img_byte_arr, format='PNG')
    st.download_button("Download Image", data=img_byte_arr.getvalue(), file_name="sticker_image.png", mime="image/png")
