from flask_socketio import SocketIO
from pymongo import MongoClient
from pymongo.collection import Collection


def connect_to_mongodb(link: str, db: str, collection: str) -> Collection:
    """
    建立MongoDB連線，並取得指定之collection
    參數:
    - link(str):連線至MongoDB的URI(host及port)
    - db(str):資料庫名稱
    - collection(str):集合名稱
    回傳:
    - pymongo.collection.Collection:指定的MongoDB collection物件
    """
    mongo_client = MongoClient(link)
    mongo_db = mongo_client[db]
    mongo_collection = mongo_db[collection]
    return mongo_collection


def show_latest_messages(
    socketio: SocketIO, collection: Collection, username: str, friend: str, limit: int
) -> None:
    """
    每次使用者進入聊天室時，載入其已讀取的前幾筆歷史訊息（預設為 30 筆）
    參數:
    - socketio(SocketIO):負責將接收到的訊息即時傳給前端
    - collection(Collection):MongoDB集合
    - username(str):聊天室使用者名稱
    - friend(str):聊天對象名稱
    - limit(int):顯示於對話框之歷史訊息筆數上限
    """
    # 設定查詢條件，包含topic與已讀使用者
    query = {
        "topic": f"Lets_chat_{min(username, friend)}_{max(username, friend)}",
        "read_by": {"$in": [username]},
    }
    # 先依時間由新到舊抓取前幾筆訊息
    latest_msg = list(
        collection.find(
            query, {"_id": 0, "sender": 1, "receiver": 1, "message": 1, "timestamp": 1}
        )
        .sort({"timestamp": -1})
        .limit(limit)
    )
    # 再將訊息反轉為由舊到新排序，方便前端顯示
    latest_msg = sorted(latest_msg, key=lambda v: v["timestamp"])
    # 傳送訊息清單給指定房間的使用者
    socketio.emit("history_message", latest_msg, room=username)
