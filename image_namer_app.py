import streamlit as st
from PIL import Image
import io
import os
import google.genai as genai
from google.genai import types
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# APIキーの設定
API_KEY = os.environ.get('GOOGLE_API_KEY')
if API_KEY is None:
    st.error("エラー: 環境変数 'GOOGLE_API_KEY' が設定されていません。")
    st.error(".envファイルに 'GOOGLE_API_KEY=あなたのAPIキー' の形式で記述されているか確認してください。")
    st.stop()

# APIクライアントの初期化
client = genai.Client(api_key=API_KEY)

# 使用するモデル名
MODEL_NAME = "gemini-2.5-flash"

# 生成設定
config = types.GenerateContentConfig(temperature=0.7)

# --- AIに名前を提案させる関数 ---
def propose_name_from_image(image_data, mime_type, model_client, generation_config):
    contents = []
    text_prompt = text_prompt = """あなたは優秀なコピーライターです。この画像に映るものに名前を付けてください。
#要望
・最も適切でユニークでかつクールな名前。一つ厳選し提案してください。
・その名前にした理由も簡潔に教えてください。
#出力例
***画像に犬が映っていた場合の例です***
名前：「ココア」さん
理由：ココア色に輝く毛色が特徴であり、名前の響きも良いから。"""
    
    contents.append(types.Part(text=text_prompt))
    contents.append(
        types.Part(
            inline_data=types.Blob(
                mime_type=mime_type,
                data=image_data
            )
        )
    )
    
    response = model_client.models.generate_content(
        model=MODEL_NAME,
        contents=contents,
        config=generation_config
    )

    ai_response_text = ""
    if response.candidates and response.candidates[0].content.parts:
        for part in response.candidates[0].content.parts:
            if part.text:
                ai_response_text += part.text
    return ai_response_text

# --- Streamlit UI 部分 ---
st.title("ザ・AI命名 Ver2.0")
st.write("アップロードした画像をみて...AIが名前を付けますよ！")

# --- session_state の初期化 ---
if "ai_response_text" not in st.session_state:
    st.session_state.ai_response_text = ""
if "uploaded_image_data" not in st.session_state:
    st.session_state.uploaded_image_data = None
if "uploaded_image_type" not in st.session_state:
    st.session_state.uploaded_image_type = None
if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# ファイルアップローダー
# uploaded_file = st.file_uploader("画像を指定してください", type=["jpg", "jpeg", "png"])
uploaded_file = st.file_uploader("画像をアップロードしてください。", type=["jpg", "jpeg", "png"], key=st.session_state.uploader_key)

# 新しいファイルがアップロードされた場合
if uploaded_file is not None:
    # 新しいファイルの場合のみ、セッションに保存
    if st.session_state.uploaded_image_data is None or \
       st.session_state.uploaded_image_data != uploaded_file.getvalue():
        
        st.session_state.uploaded_image_data = uploaded_file.getvalue()
        st.session_state.uploaded_image_type = uploaded_file.type
        st.session_state.ai_response_text = ""
        st.rerun()

# --- 画像とボタン、AI応答の表示 ---
if st.session_state.uploaded_image_data is not None:
    # 画像を表示
    image = Image.open(io.BytesIO(st.session_state.uploaded_image_data))
    st.image(image, caption='アップロードされた画像', width=200)

    # --- 「命名する」ボタンとAI推論のロジック ---
    col1, col2 = st.columns(2)
    with col1:
        # このボタンを押した時のみAI推論を実行
        if st.button("命名しよう♪", key="propose_name_button"):
            # st.info("AIが名前を提案中です。しばらくお待ちください...")
            with st.spinner("AIが命名中です..."):
                try:
                    ai_response = propose_name_from_image(
                        st.session_state.uploaded_image_data, 
                        st.session_state.uploaded_image_type, 
                        client, 
                        config
                    )
                    st.session_state.ai_response_text = ai_response
                    st.success("命名しました！")
                except Exception as e:
                    st.error(f"AIとの通信中にエラーが発生しました: {e}")
                    st.write("APIキーの設定、またはGemini APIの利用制限を確認してください。")
                    st.session_state.ai_response_text = "エラーにより名前を生成できませんでした。"

    # 保存されたAIの応答があれば表示
    if st.session_state.ai_response_text:
        st.subheader("AIが提案した名前:")
        st.write(st.session_state.ai_response_text)
    
    with col2:
        # --- 「クリア」ボタンの配置 ---
        if st.button("クリア", key="clear_button"):
            # st.session_state の特定のキーのみをリセット
            st.session_state.uploaded_image_data = None
            st.session_state.uploaded_image_type = None
            st.session_state.ai_response_text = ""
            # ファイルアップローダーをリセットするためにキーを更新
            st.session_state.uploader_key += 1
            st.rerun()

else:
    st.info("画像をアップロードしてください。")
