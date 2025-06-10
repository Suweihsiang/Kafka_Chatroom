# Kafka Chatroom

Kafka Chatroom是一個基於Apache Kafka的即時雙人聊天室系統，使用Kafka作為訊息中介，搭配MongoDB儲存訊息記錄，並透過Flask + Socket.IO提供前後端通訊能力。

---

## 功能概述

- 使用者進入聊天室前輸入：
  - 自己的名稱（作為consumer的group_id）
  - 通話對象名稱
- 系統以兩者名稱組成唯一的Kafka **Topic**
- 使用者傳送訊息後：
  - 以Kafka **Producer**發送至Topic
  - 同時將訊息儲存至**MongoDB**
- 使用者重新進入聊天室時：
  - 系統自動載入MongoDB中最多前**30筆歷史訊息**

---

## 技術堆疊（Tech Stack）

| 元件           | 說明                           |
|----------------|--------------------------------|
| **Kafka**      | 訊息佇列中介，用於雙向通訊     |
| **MongoDB**    | 儲存訊息記錄                   |
| **Flask**      | 提供 Web API 與 Socket 通訊服務 |
| **Socket.IO**  | 前後端即時雙向溝通             |
| **Eventlet**   | 非同步網路 I/O 支援             |
| **Python**     | 使用語言，透過 `confluent-kafka` 操作 Kafka |

---

## 啟動方式

### 1. 環境需求

- Python 3.11+
- Kafka & Zookeeper
- MongoDB

### 2. 使用poetry管理套件

- poetry.lock
- pyproject.toml


### 3. 啟動Kafka + Zookeeper + MongoDB + Kafka UI + Mongo Express

docker compose up -d

### 4. 啟動Flask應用

poetry run python app.py

## 測試方式
### 1. 開啟兩個瀏覽器分頁（建議一個使用無痕模式）

### 2. 在第一個頁面輸入：

  - 你的名稱：UserA

  - 朋友名稱：UserB

### 3. 在第二個頁面輸入相反名稱：UserB、UserA

### 4. 開始互傳訊息

### 5. 觀察：

  - Kafka 訊息是否成功寫入（透過 Kafka UI）

  - MongoDB 是否正確儲存訊息（透過 Mongo Express）