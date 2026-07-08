#index html 파일 필요함!!!
#추후 업로드 예정
#templates/index.html
#.env(ANTHROPIC_API_KEY)

import json
from flask import Flask, render_template, request, Response, stream_with_context
from dotenv import load_dotenv
from anthropic import Anthropic
load_dotenv()

app = Flask(__name__)
client = Anthropic()
MODEL = "claude-sonnet-4-6"

# 페르소나: system prompt로 AI의 역할을 설정
SYSTEM_PROMPT = (
    "당신은 프로그래밍을 처음 배우는 학생을 가르치는 친절한 선생님입니다. "
    "항상 존댓말을 사용하고 격려하는 톤으로, 비유와 예시를 들어 쉽게 설명합니다."
)

# 대화 기록 (LLM은 stateless라 직접 저장해서 매번 함께 보냄)
history = []


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json["message"]
    history.append({"role": "user", "content": user_message})

    def generate():
        with client.messages.stream(
            model=MODEL,
            max_tokens=1024,
            system=SYSTEM_PROMPT,
            messages=history,
        ) as stream:
            full_response = ""
            for text in stream.text_stream:
                full_response += text
                # SSE 형식으로 토큰을 실시간 전송
                yield f"data: {json.dumps({'text': text})}\n\n"

            history.append({"role": "assistant", "content": full_response})
            yield f"data: {json.dumps({'done': True})}\n\n"

    return Response(
        stream_with_context(generate()),
        content_type="text/event-stream",
    )


if __name__ == "__main__":
    app.run(debug=True, port=5000)
