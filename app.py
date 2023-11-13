import streamlit as st
import speech_recognition as sr
import openai
import requests
from PIL import Image
from io import BytesIO
import time

# APIキー
openai.api_key = "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"

# 言語選択と、APIが認識する言語の変換リストを作成
set_language_list = {
    "日本語" :"ja",
    "英語" :"en-US",
}

# デフォルト設定
set_language = "日本語"  # デフォルトの言語
set_duration = 30  # デフォルトの１回当たりの録音時間

# 音声認識の関数
def mic_speech_to_text(set_language, set_duration):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.record(source, duration = set_duration)  # durationパラメータでリッスンする時間を設定
    try:
        result_text = recognizer.recognize_google(audio, language=set_language_list[set_language])
    except Exception as e:
        print(f"エラー: {e}")  # https://chat.openai.com/share/f98603c0-e394-474f-8421-52d7ad7b3ae0
        # 以下はテスト用で変更。
        result_text = "ソフトバンクの代表として久々に公の場でスピーチします。今日は個人的な見解を交えながら、意義深いメッセージをお届けします。プレゼンテーションは約60ページ、話す時間は60分ですが、中でも2ページに特に重要な内容を凝縮しています。"
        # result_text = "音声認識に失敗しました"
    return result_text # 戻り値

# テキスト要約の関数
def summarize_text(result_text):
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",  # 使用するモデル
        messages = [
            {"role": "system", "content": "以下の文章を要約してください:"},
            {"role": "user", "content": result_text },
        ],
        max_tokens = 100  # 最大トークン数
    )
    
    output_content = response.choices[0]["message"]["content"].strip() # 返って来たレスポンスの内容はresponse.choices[0]["message"]["content"].strip()に格納されているので、これをoutput_contentに代入
    return output_content # 戻り値

# テキスト翻訳の関数
def translate_to_english(output_content):
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": "以下の日本語のテキストを英語に翻訳してください:"},
            {"role": "user", "content": output_content},
        ],
        max_tokens=100
    )

    english_text = response.choices[0]["message"]["content"].strip()
    return english_text # 戻り値

# 画像生成と表示の関数
def generate_and_display_image(english_text):
    response = openai.Image.create(
        prompt ='次の{文章}を画像で出力してください。'+
                '\n'+'文章:"""'+
                '\n'+ english_text +
                '\n'+'"""',
        size="256x256",
        quality="standard",
        n=1,
    )
    image_url = response['data'][0]['url']
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    return image # 戻り値

# Streamlit表示
st.title("スピードグラレコアプリ") # タイトル

# サイドバーでのパラメータ設定
st.sidebar.write("会議内容を要約して画像を生成するよ") # 案内表示
set_language = st.sidebar.selectbox("音声認識する言語を選んでください。",set_language_list.keys()) # 音声認識に使う言語を選択肢として表示
set_duration = st.sidebar.slider('1回あたりの録音時間を選んでください。', 10,150,30,10)  # デフォルトで30秒間の認識 st.slider(label, min_value=None, max_value=None, value=None, step=None, format=None, key=None, help=None, on_change=None, args=None, kwargs=None, *,disabled= False、label_visibility="visible")
total_record_count = st.sidebar.slider('総録音回数',1,5,2,1)  # デフォルトで2回の認識

st.sidebar.write("マイクでの音声認識はこちらのボタンから") # 案内表示

# アプリ起動部
if st.sidebar.button('音声認識と画像生成を開始'):
    st.session_state['output_history'] = []  # 出力を保存するリスト https://chat.openai.com/share/bdd7eccc-5fe5-4641-8a2f-29bb237b8023

    # 音声認識と画像生成の処理
    for i in range(total_record_count):

        # 音声認識
        state = st.empty() # マイク録音中を示す為の箱を準備
        state.write(f"{set_duration}秒間の音声を聞いています...") # 箱に案内表示書き込み
        result_text = mic_speech_to_text(set_language, set_duration)
        st.write("【音声認識結果】" )
        state.empty()  # 実行中表示の削除
        st.write(result_text)

        # 要約
        state_summary = st.empty()
        state_summary.write("要約中...") # 箱に案内表示書き込み
        summarized_text = summarize_text(result_text)  # テキスト要約
        st.write("【要約結果】")
        state_summary.empty()  # 実行中表示の削除
        st.write(summarized_text)

        # 翻訳
        state_english = st.empty()
        state_english.write("英語に翻訳中...") # 箱に案内表示書き込み
        english_text = translate_to_english(summarized_text)
        if english_text:  # 翻訳されたテキストが存在する場合のみ
            st.write("【翻訳結果（英語）】")
            state_english.empty()
            st.write(english_text)

        # 画像生成
        state_image = st.empty()
        state_image.write("画像生成中...") # 箱に案内表示書き込み
        image = generate_and_display_image(english_text)
        state_image.empty()
        st.image(image)  # Streamlitのst.imageで画像を表示

        # 出力結果を残したまま、次の出力を行う
        st.session_state['output_history'].append((result_text, summarized_text, english_text, image))

    st.write("処理が完了しました。")