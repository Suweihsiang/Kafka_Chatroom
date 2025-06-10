import json
from typing import Any, Optional

from confluent_kafka import Message, Producer
from confluent_kafka.error import KafkaError

# 設定Producer所需參數
props = {
    "bootstrap.servers": "kafka:29092",
}
producer = Producer(props)


def delivery_report(err: Optional[KafkaError], msg: Message) -> None:
    """
    紀錄發送完成狀態的callback
    """
    if err is not None:
        print(f"Message delivery failed: {err}")
    else:
        print(
            f"Message delivered to {msg.topic()} [{msg.partition()}] @ offset {msg.offset()}"
        )


def send_message(topic: str, message: dict[str, Any]) -> None:
    """
    使用Kafka producer傳送一則訊息至指定topic。
    參數:
    - topic(str):要傳送到的topic名稱
    - message(dict[str, Any]):要傳送的訊息內容
    """
    try:
        json_msg = json.dumps(message)  # 將message物件序列化成JSON字串
        producer.produce(
            topic, value=json_msg, callback=delivery_report
        )  # 將JSON訊息送到指定的topic，並設定callback來追蹤是否成功送出
        producer.flush()  # 等待所有訊息完成傳送，確保資料不會留在buffer中
    except Exception as e:
        print(f"Error sending message: {e}")
