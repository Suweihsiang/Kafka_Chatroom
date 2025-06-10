import json
from typing import Dict, Tuple

import eventlet
from bson import ObjectId
from confluent_kafka import Consumer, KafkaError, KafkaException
from flask_socketio import SocketIO

from connect_to_db import connect_to_mongodb

# 連線到MongoDB
mongo_collection = connect_to_mongodb(
    "mongodb://root:password@mongodb:27017", "Kafka_Chatroom", "message"
)


def start_consume(
    socketio: SocketIO,
    topic: str,
    username: str,
    chatroom_consumer: Dict[Tuple[str, str], bool],
) -> None:
    """
    啟動一個Kafka consumer，在背景非同步接收特定topic的訊息。
    參數:
    - socketio(SocketIO):負責將接收到的訊息即時傳給前端
    - topic(str):要訂閱的Kafka topic名稱
    - username(str):以username為基礎設定group_id，讓使用者接收自己的未讀訊息
    - chatroom_consumer(Dict[Tuple[str, str], bool]):聊天室內的(topic,consumer)狀態
    """

    def consumer() -> None:
        """
        建立Kafka consumer，將新訊息透過SocketIO傳送訊息給指定使用者，並使用eventlet.sleep(0)避免阻塞。
        """
        # 設定Consumer所需參數
        props = {
            "bootstrap.servers": "kafka:29092",
            "group.id": f"{username}_group",
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
        }
        consumer = Consumer(props)
        consumer.subscribe([topic])
        try:
            while (topic, username) in chatroom_consumer:
                msg = consumer.poll(0.1)  # 從Kafka拉取一則新訊息，最多等待0.1秒

                if msg is None:  # 若沒有接收到任何訊息
                    eventlet.sleep(0)
                    continue
                if msg.error():  # 若收到的訊息有錯誤
                    if msg.error().code() == KafkaError._PARTITION_EOF:
                        continue  # 到達Partition尾端則忽略
                    else:
                        raise KafkaException(msg.error())
                    continue

                # 處理接收到的訊息
                data = json.loads(msg.value().decode("utf-8"))
                # 將新訊息發送到對應使用者的聊天室頁面，顯示在chat-box中
                socketio.emit("new_message", data, room=username)

                if username != data["user"]:  # 標記為已讀
                    mongo_collection.update_one(
                        {"_id": ObjectId(data["_id"])},
                        {"$addToSet": {"read_by": username}},
                    )

                consumer.commit(msg)  # 手動提交offset
                eventlet.sleep(0)  # 非同步讓出執行權
        except Exception as e:
            print(f"Consumer error for user {username}: {e}")
        finally:
            print("consumer close")
            consumer.close()  # 關閉Kafka consumer，釋放相關資源

    # 使用eventlet啟動consumer執行緒，使其在背景非同步執行Kafka訊息的接收處理
    eventlet.spawn(consumer)
