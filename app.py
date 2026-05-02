import streamlit as st
from PIL import Image
from PIL import ImageDraw
import tempfile

# --- Roboflow ---
@st.cache_resource
def get_api_key():
    return st.secrets["ROBOFLOW_API_KEY"]

api_key = get_api_key()

st.title("💊 錠剤カウンター")
st.write("※ 錠剤は重ならないよう軽く広げてください")

# --- セッション ---

if "current_count" not in st.session_state:
    st.session_state.current_count = None

if "image" not in st.session_state:
    st.session_state.image = None

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# --- アップロード ---
uploaded_file = st.file_uploader(
    "📸 写真を撮影または選択",
    type=["jpg", "jpeg", "png"],
    accept_multiple_files=True,
    key=st.session_state.uploader_key
)

if uploaded_file is None:
    st.info("画像を撮影または選択してください")

if uploaded_file:
    st.session_state.current_count = None
    total_count = 0
    final_image = None

    for file in uploaded_file:
        image = Image.open(file)
        image = image.convert("RGB")
        image.thumbnail((1024, 1024))

        with st.spinner("カウント中..."):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
                image.save(tmp.name)
                try:
                    import requests

                    url = "https://serverless.roboflow.com/pill-counter-itcml/5"
                    params = {"api_key": api_key}

                    with open(tmp.name, "rb") as f:
                        response = requests.post(
                            url,
                            params=params,
                            files={"file": f},
                            timeout=10
                        )

                    if response.status_code != 200:
                        st.warning("通信エラー。もう一度撮影してください")
                        st.stop()

                    result = response.json()

                except Exception as e:
                    st.error(f"エラー内容: {e}")
                    st.stop()

        if "predictions" not in result:
            continue

        predictions = result["predictions"]
        filtered = [p for p in predictions if p["confidence"] > 0.5]

        total_count += len(filtered)

        # 最後の1枚だけ表示（軽くする）
        final_image = image.copy()
        draw = ImageDraw.Draw(final_image)

        for p in filtered:
            x = p["x"]
            y = p["y"]
            w = p["width"]
            h = p["height"]

            x1 = x - w / 2
            y1 = y - h / 2
            x2 = x + w / 2
            y2 = y + h / 2

            r = 5

            # 外側（黒）
            draw.ellipse(
                [x - r - 1, y - r - 1, x + r + 1, y + r + 1],
                fill="black"
            )

            # 内側（色）
            draw.ellipse(
                [x - r, y - r, x + r, y + r],
                fill="lime"
            )

    st.session_state.image = final_image
    st.session_state.total_count = total_count


if not uploaded_file:
    st.session_state.total_count = None
    st.session_state.image = None


# --- 表示 ---
if st.session_state.image is not None:
    st.image(st.session_state.image)

if "total_count" in st.session_state:
    st.markdown(f"# 🧮 合計：{st.session_state.total_count} 個")

# --- リセット ---
if st.button("🔄 リセット"):
    current_key = st.session_state.get("uploader_key", 0)
    st.session_state.clear()
    st.session_state.uploader_key = current_key + 1
    st.rerun()
