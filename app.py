import streamlit as st
from PIL import Image, ImageEnhance, ImageOps, ImageDraw
import os
import io
import math

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


# Function to overlay sticker with rotation
def paste_sticker(bg_img, sticker_img, position, scale, rotation):
    # Convert to RGBA if needed
    if bg_img.mode != 'RGBA':
        bg_img = bg_img.convert('RGBA')

    # Create a transparent layer for the sticker
    sticker_layer = Image.new('RGBA', bg_img.size, (0, 0, 0, 0))

    # Resize sticker
    w, h = sticker_img.size
    resized = sticker_img.resize((int(w * scale), int(h * scale)), Image.Resampling.LANCZOS)

    # Rotate sticker
    if rotation != 0:
        rotated = resized.rotate(rotation, expand=True, resample=Image.BICUBIC)
    else:
        rotated = resized

    # Calculate position to center the sticker
    x, y = position
    rot_w, rot_h = rotated.size
    paste_x = x - rot_w // 2
    paste_y = y - rot_h // 2

    # Paste rotated sticker onto the transparent layer
    sticker_layer.paste(rotated, (paste_x, paste_y), rotated)

    # Combine with background
    return Image.alpha_composite(bg_img, sticker_layer)


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

    # Initialize sticker state
    if "stickers_pos" not in st.session_state:
        st.session_state.stickers_pos = {key: (100, 100) for key in STICKERS.keys()}
    if "stickers_scale" not in st.session_state:
        st.session_state.stickers_scale = {key: 1.0 for key in STICKERS.keys()}
    # 新增：旋转角度状态
    if "stickers_rotation" not in st.session_state:
        st.session_state.stickers_rotation = {key: 0 for key in STICKERS.keys()}

    # 用户选择贴纸后的位置、缩放、旋转滑块和贴图
    for sticker_key in selected_stickers:
        st.subheader(f"Adjust: {STICKERS[sticker_key]}")

        # 创建滑块和数值输入框的布局
        col_x1, col_x2 = st.columns([3, 1])
        with col_x1:
            x = st.slider(
                f"X position of {sticker_key}",
                0, image.width,
                st.session_state.stickers_pos[sticker_key][0],
                key=f"x_slider_{sticker_key}"
            )
        with col_x2:
            x_num = st.number_input(
                "X value",
                min_value=0, max_value=image.width,
                value=st.session_state.stickers_pos[sticker_key][0],
                step=1,
                key=f"x_num_{sticker_key}"
            )
            # 同步滑块和数值输入框
            if x != x_num:
                st.session_state[f"x_slider_{sticker_key}"] = x_num
                x = x_num

        col_y1, col_y2 = st.columns([3, 1])
        with col_y1:
            y = st.slider(
                f"Y position of {sticker_key}",
                0, image.height,
                st.session_state.stickers_pos[sticker_key][1],
                key=f"y_slider_{sticker_key}"
            )
        with col_y2:
            y_num = st.number_input(
                "Y value",
                min_value=0, max_value=image.height,
                value=st.session_state.stickers_pos[sticker_key][1],
                step=1,
                key=f"y_num_{sticker_key}"
            )
            # 同步滑块和数值输入框
            if y != y_num:
                st.session_state[f"y_slider_{sticker_key}"] = y_num
                y = y_num

        col_scale1, col_scale2 = st.columns([3, 1])
        with col_scale1:
            scale = st.slider(
                f"Scale of {sticker_key}",
                0.5, 3.0,
                st.session_state.stickers_scale[sticker_key],
                step=0.1,
                key=f"scale_slider_{sticker_key}"
            )
        with col_scale2:
            scale_num = st.number_input(
                "Scale value",
                min_value=0.5, max_value=3.0,
                value=st.session_state.stickers_scale[sticker_key],
                step=0.1,
                format="%.1f",
                key=f"scale_num_{sticker_key}"
            )
            # 同步滑块和数值输入框
            if abs(scale - scale_num) > 0.01:
                st.session_state[f"scale_slider_{sticker_key}"] = scale_num
                scale = scale_num

        # 新增：旋转角度滑块和数值输入框
        col_rot1, col_rot2 = st.columns([3, 1])
        with col_rot1:
            rotation = st.slider(
                f"Rotation of {sticker_key}",
                -180, 180,
                st.session_state.stickers_rotation[sticker_key],
                key=f"rot_slider_{sticker_key}"
            )
        with col_rot2:
            rotation_num = st.number_input(
                "Rotation value",
                min_value=-180, max_value=180,
                value=st.session_state.stickers_rotation[sticker_key],
                step=1,
                key=f"rot_num_{sticker_key}"
            )
            # 同步滑块和数值输入框
            if rotation != rotation_num:
                st.session_state[f"rot_slider_{sticker_key}"] = rotation_num
                rotation = rotation_num

        # 更新session状态
        st.session_state.stickers_pos[sticker_key] = (x, y)
        st.session_state.stickers_scale[sticker_key] = scale
        st.session_state.stickers_rotation[sticker_key] = rotation

        # 从缩小过的贴纸中读取
        sticker_img = st.session_state.resized_stickers[sticker_key]
        filtered_image = paste_sticker(filtered_image, sticker_img, (x, y), scale, rotation)

    st.subheader("Final Output")
    st.image(filtered_image, caption="Your Fun Sticker Image", use_container_width=True)

    img_byte_arr = io.BytesIO()
    filtered_image.save(img_byte_arr, format='PNG')
    st.download_button("Download Image", data=img_byte_arr.getvalue(), file_name="sticker_image.png", mime="image/png")
