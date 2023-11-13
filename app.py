import streamlit as st
import speech_recognition as sr
import openai
import requests
from PIL import Image
from io import BytesIO
import time

# APIキー
openai.api_key = ""

# 言語選択と、APIが認識する言語の変換リストを作成
set_language_list = {
    "日本語" :"ja",
    "英語" :"en-US",
}

# デフォルト設定
set_language = "日本語"  # デフォルトの言語
set_duration = 30  # デフォルトの１回当たりの録音時間

# 音声認識の関数
def mic_speech_to_text(set_language, duration = set_duration):
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        audio = recognizer.record(source, duration = duration)  # durationパラメータでリッスンする時間を設定
    try:
        result_text = recognizer.recognize_google(audio, language=set_language_list[set_language])
    except Exception as e:
        print(f"エラー: {e}")   # f は、Pythonの「フォーマット済み文字列リテラル」（f-string）を表しています。この機能はPython 3.6以降で利用できます。
                               # f-stringを使用すると、波括弧 {} 内に変数や式を直接記述し、その結果を文字列に組み込むことができます。
                               # 例えば、もし変数 e にエラーメッセージが格納されている場合、print(f"エラー: {e}") はそのエラーメッセージを含む文字列を出力します。
        # 以下はテスト用で変更。
        result_text = "ソフトバンクの代表として久々に公の場でスピーチします。今日は個人的な見解を交えながら、意義深いメッセージをお届けします。プレゼンテーションは約60ページ、話す時間は60分ですが、中でも2ページに特に重要な内容を凝縮しています。"
        # result_text = "音声認識に失敗しました"
    return result_text

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
    # 返って来たレスポンスの内容はresponse.choices[0]["message"]["content"].strip()に格納されているので、これをoutput_contentに代入
    output_content = response.choices[0]["message"]["content"].strip()
    return output_content # 返って来たレスポンスの内容を返す

# テキスト翻訳の関数
def translate_to_english(output_content):  # text → output_content
    response = openai.ChatCompletion.create(
        model = "gpt-3.5-turbo",
        messages = [
            {"role": "system", "content": "以下の日本語のテキストを英語に翻訳してください:"},
            {"role": "user", "content": output_content},  # text → output_content
        ],
        max_tokens=100
    )

    english_text = response.choices[0]["message"]["content"].strip()
    return english_text

# 画像生成と表示の関数
def generate_and_display_image(english_text):
    response = openai.Image.create(
        prompt=english_text,
        size="256x256",
        quality="standard",
        n=1,
    )
    image_url = response['data'][0]['url']
    response = requests.get(image_url)
    image = Image.open(BytesIO(response.content))
    st.image(image)

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
    # if 'output_history' not in st.session_state:
        st.session_state['output_history'] = []  # 出力を保存するリスト　https://chat.openai.com/share/bdd7eccc-5fe5-4641-8a2f-29bb237b8023

        # 音声認識と画像生成の処理        
        for i in range(total_record_count):
            state = st.empty() # マイク録音中を示す為の箱を準備
            state.write(f"{set_duration}秒間の音声を聞いています...") # 箱に案内表示書き込み

            # 音声認識
            result_text = mic_speech_to_text(set_language, set_duration)
            st.write("【音声認識結果】" )
            state.empty()  # 実行中表示の削除
            st.write(result_text)

            state = st.empty() 
            state.write("要約中...") # 箱に案内表示書き込み
            summarized_text = summarize_text(result_text)  # テキスト要約
            st.write("【要約結果】")
            state.empty()  # 実行中表示の削除
            st.write(summarized_text)

            # 翻訳
            state_summary = st.empty() 
            state_summary.write("英語に翻訳中...") # 箱に案内表示書き込み
            state_summary.empty()
            english_text = translate_to_english(summarized_text)
            if english_text:  # 翻訳されたテキストが存在する場合のみ
                st.write("【翻訳結果（英語）】")
                st.write(english_text)
                english_text_prompt = english_text + ',and style is simple drawing, background color is white'


            # 画像生成
            state_image = st.empty() 
            state_image.write("画像生成中...") # 箱に案内表示書き込み
            response = openai.Image.create(
            prompt=english_text_prompt,
            size="256x256",
            quality="standard",
            n=1,
            )
            state_image.empty()
            # 生成した画像のURLを取得
            image_url = response['data'][0]['url']

            # 画像を表示
            response = requests.get(image_url)
            image = Image.open(BytesIO(response.content))
            st.image(image)  # Streamlitのst.imageで画像を表示

        st.session_state['output_history'].append((result_text, summarized_text, english_text, image_url))

        st.write("処理が完了しました。")