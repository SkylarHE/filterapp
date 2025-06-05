import streamlit as st
from PIL import Image, ImageEnhance, ImageOps
import os
import io

# Path to assets
STICKER_DIR = "assets/stickers"
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

    # Adjustment sliders
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

    # Apply all selected stickers
    for sticker_key in selected_stickers:
        x, y = st.session_state.stickers_pos[sticker_key]
        scale = st.session_state.stickers_scale[sticker_key]
        rotation = st.session_state.stickers_rotation[sticker_key]
        sticker_img = st.session_state.original_stickers[sticker_key]
        resized_img = sticker_img.resize((int(sticker_img.width * INITIAL_SCALE),
                                          int(sticker_img.height * INITIAL_SCALE)))
        filtered_image = paste_sticker(filtered_image, resized_img, (x, y), scale, rotation)

    st.subheader("Final Output")
    st.image(filtered_image, caption="Your Fun Sticker Image", use_container_width=True)

    img_byte_arr = io.BytesIO()
    filtered_image.save(img_byte_arr, format='PNG')
    st.download_button("Download Image", data=img_byte_arr.getvalue(),
                       file_name="sticker_image.png", mime="image/png")
