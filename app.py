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
if "total" not in st.session_state:
    st.session_state.total = 0

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

            draw.rectangle([x1, y1, x2, y2], outline="red", width=3)

    st.session_state.image = final_image
    st.session_state.current_count = total_count

# --- 表示 ---
if st.session_state.image is not None:
    st.image(st.session_state.image)

if st.session_state.current_count is not None:
    st.markdown(f"# 🧮 {st.session_state.current_count} 個")

# --- 操作 ---

st.write("※ カウント結果を確認してから追加してください")

col1, col2 = st.columns(2)

confirm = st.checkbox("このカウントでOK")

with col1:
    if st.button("✅ 追加") and confirm and st.session_state.current_count is not None:
        st.session_state.total += st.session_state.current_count
        st.session_state.current_count = None
        st.session_state.image = None
        st.session_state.uploader_key += 1
        st.success("追加しました")

with col2:
    if st.button("❌ 破棄"):
        st.session_state.current_count = None
        st.session_state.image = None
        st.session_state.uploader_key += 1

# --- 合計 ---
st.markdown(f"## 合計：{st.session_state.total} 個")

# --- リセット ---
if st.button("🔄 リセット"):
    st.session_state.clear()
    st.rerun()
    st.session_state.total = 0
    st.session_state.current_count = None
    st.session_state.image = None
    st.session_state.uploader_key += 1
