import eventlet

eventlet.monkey_patch()  # 將標準庫中的部分模組打上monkey patch，使其支援非同步協程

from flask import (
    Flask,
    redirect,
    render_template,
    url_for,
    make_response,
    request,
    session,
    Response,
)
from flask_socketio import SocketIO, join_room
from confluent_kafka.admin import AdminClient, NewTopic
import os
import pytz
from datetime import datetime
from typing import Dict, Tuple

from dotenv import load_dotenv

from connect_to_db import connect_to_mongodb, show_latest_messages
from kafka_consumer import start_consume
from kafka_producer import send_message

load_dotenv()  # 載入.env檔案中的環境變數

app = Flask(__name__)  # 建立Flask應用程式
app.secret_key = os.getenv("APP_SECRET_KEY")  # 設定Flask的session加密金鑰
socketio = SocketIO(app)  # 初始化SocketIO，用來處理即時事件

# 連線到MongoDB
mongo_collection = connect_to_mongodb(
    "mongodb://root:password@mongodb:27017", "Kafka_Chatroom", "message"
)

# 本地時間
local_tz = pytz.timezone("Asia/Taipei")


def topic_ready_or_not(topic: str) -> None:
    """
    檢查指定Kafka topic是否存在；若不存在則建立該topic
    參數:
    - topic(str):Kafka topic名稱
    """
    admin_client = AdminClient({"bootstrap.servers": "kafka:29092"})
    topic_metadata = admin_client.list_topics(timeout=10)

    if topic in topic_metadata.topics:  # 如果topic已存在
        print("topic is ready")
        return

    new_topic = NewTopic(topic, 1, 1)
    fs = admin_client.create_topics([new_topic])

    try:
        fs[topic].result(timeout=10)  # 等待建立完成，避免卡住
        print(f"create topic {topic} successfully")
    except Exception as e:
        print(f"create topic {topic} failed : {e}")


# 用來追蹤哪些使用者已啟動過Kafka Consumer
# key=(topic,username)，value=True表示已啟動
chatroom_consumer: Dict[Tuple[str, str], bool] = {}


def consumer_ready_or_not(topic: str, username: str) -> None:
    """
    檢查指定topic與username的Kafka consumer是否已啟動
    如果尚未啟動，則初始化consumer並註記為已啟動
    參數:
    - topic(str):Kafka topic名稱
    - username(str):使用者名稱，作為group_id
    """
    key = (topic, username)
    if key not in chatroom_consumer:
        start_consume(socketio, topic, username, chatroom_consumer)
        chatroom_consumer[key] = True


@app.route("/")
def index() -> Response:
    """
    網站首頁，自動導向至登入頁面
    """
    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login() -> Response:
    """
    使用者登入：
    - GET：顯示登入畫面
    - POST：儲存使用者資訊
    """
    if request.method == "POST":
        username = request.form.get("username")
        friend = request.form.get("friend")
        if not username or not friend:  # 漏填其中一項就會要求重填
            return make_response("Please fulfill all inputbox", 400)
        # 儲存登入資訊至session
        session["username"] = username
        session["friend"] = friend
        # 以雙方名稱生成topic，並以字母順序排序以確保一致性
        session["topic"] = f"Lets_chat_{min(username, friend)}_{max(username, friend)}"
        return redirect(url_for("chat"))
    return render_template("login.html")


@app.route("/chat")
def chat() -> Response:
    """
    聊天室介面
    """
    if "username" not in session or "friend" not in session:
        return redirect(url_for("login"))
    return render_template(
        "chat.html", username=session["username"], friend=session["friend"]
    )


@app.route("/send", methods=["POST"])
def send() -> Response:
    """
    接收前端傳送的訊息，加入時間戳記後送入Kafka topic
    """
    data = request.json  # 前端送出訊息時隨POST請求傳來的JSON資料
    topic = session.get("topic")
    if not topic:
        return make_response("Chatroom is not ready", 400)
    msg = {
        "user": data["user"],
        "message": data["message"],
        "timestamp": datetime.now(local_tz).isoformat(),
    }
    msg_to_mongo = {
        "topic": topic,
        "sender": msg["user"],
        "receiver": session.get("friend"),
        "message": msg["message"],
        "timestamp": msg["timestamp"],
        "read_by": [msg["user"]],
    }
    result = mongo_collection.insert_one(msg_to_mongo)
    msg["_id"] = str(result.inserted_id)  # 儲存到MongoDB的_id
    send_message(topic, msg)
    return make_response("", 204)  # 成功但無回應內容


@socketio.on("join")
def handle_join(username: str) -> None:
    """
    當使用者進入聊天室時，加入以username為名的房間，並啟動consumer
    """
    join_room(username)
    print(f"{username} join the chat")
    # 每次進入聊天室先在對話框載入前幾筆歷史訊息
    show_latest_messages(
        socketio, mongo_collection, session.get("username"), session.get("friend"), 30
    )
    # 確認topic是否已存在，若不存在則建立之
    topic_ready_or_not(session.get("topic"))
    # 若尚未啟動consumer，則啟動之
    consumer_ready_or_not(session.get("topic"), session.get("username"))


@socketio.on("disconnect")
def on_disconnect():
    """
    當使用者關閉瀏覽器時，將其consumer關閉
    """
    username = session.get("username")
    topic = session.get("topic")
    if (topic, username) in chatroom_consumer:
        del chatroom_consumer[(topic, username)]


if __name__ == "__main__":
    socketio.run(app,host="0.0.0.0", port=5000, debug=True)  # 啟動Flask + SocketIO，並啟用debug模式
