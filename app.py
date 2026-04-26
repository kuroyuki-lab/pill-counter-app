import streamlit as st
from inference_sdk import InferenceHTTPClient
from PIL import Image
import tempfile

# --- Roboflow ---
api_key = st.secrets["ROBOFLOW_API_KEY"]

CLIENT = InferenceHTTPClient(
    api_url="https://serverless.roboflow.com",
    api_key=api_key
)

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
    type=["jpg", "png"],
    key=st.session_state.uploader_key
)

if uploaded_file and st.session_state.current_count is None:
    image = Image.open(uploaded_file)
    image = image.convert("RGB")
    image.thumbnail((1024, 1024),image.LANCZOS)

    st.session_state.image = image

    # 🔥 ローディング表示
    with st.spinner("カウント中..."):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
            image.save(tmp.name)
            result = CLIENT.infer(tmp.name, model_id="pill-counter-itcml/5")

    st.session_state.current_count = len(result["predictions"])

# --- 表示 ---
if st.session_state.image:
    st.image(st.session_state.image)

if st.session_state.current_count is not None:
    st.markdown(f"# 🧮 {st.session_state.current_count} 個")

# --- 操作 ---
col1, col2 = st.columns(2)

with col1:
    if st.button("✅ 追加"):
        st.session_state.total += st.session_state.current_count
        st.session_state.current_count = None
        st.session_state.image = None
        st.session_state.uploader_key += 1

with col2:
    if st.button("❌ 破棄"):
        st.session_state.current_count = None
        st.session_state.image = None
        st.session_state.uploader_key += 1

# --- 合計 ---
st.markdown(f"## 合計：{st.session_state.total} 個")

# --- リセット ---
if st.button("🔄 リセット"):
    st.session_state.total = 0
    st.session_state.current_count = None
    st.session_state.image = None
    st.session_state.uploader_key += 1
