// REST API 최종 Endpoint (예시)
const API_GATEWAY_HTTP_ENDPOINT =
  "https://rfwv4n82nj.execute-api.ap-northeast-2.amazonaws.com/default/Lambda-Taewi-Brainstorming-HTTP";

// WebSocket 연결용 Endpoint (예시)
const WEBSOCKET_ENDPOINT =
  "wss://f98s3b6lh9.execute-api.ap-northeast-2.amazonaws.com/production";

  class ChatApp {
    constructor() {
      this.data = {
        messages: [],
        user_id: "user1", // 임시 User ID
        room_id: "test",
        name: "User", // 임시 User Name
      };
      this.websocket = null;
      this.timer = null;
  
      // (1) HTML 내 존재하는 요소들을 가져오기
      this.messageListContainer = document.querySelector(".chat-messages");
      this.textarea = document.querySelector(".chat-input textarea");
      this.sendButton = document.querySelector(".chat-input button");
  
      // (2) 초기화 진행
      this.init();
    }

    async init() {
      // 메시지 로드 후 WebSocket 연결
      await this.fetchMessages();
      this.setupWebSocket();
  
      // UI 이벤트 연결
      this.setupUI();
  
      // 기존 메시지 렌더링
      this.renderMessages();
    }

  // (3) 메시지 불러오기
  async fetchMessages() {
    try {
      // user_id와 room_id를 URL의 쿼리 파라미터에 추가
      const url = `${API_GATEWAY_HTTP_ENDPOINT}?room_id=${this.data.room_id}&user_id=${this.data.user_id}`;
      console.log("[fetchMessages] GET:", url);
  
      const response = await fetch(url);
      const result = await response.json();
      console.log("[fetchMessages] Response data:", result);
  
      // 백엔드 구조에 따라 messages 데이터를 저장
      this.data.messages = result || [];
    } catch (error) {
      console.error("[fetchMessages] Failed:", error);
    }
  }  

  // (4) WebSocket 설정
  setupWebSocket() {
    const address = `${WEBSOCKET_ENDPOINT}?room_id=${this.data.room_id}&user_id=${this.data.user_id}`;
    console.log("[setupWebSocket] Connecting:", address);

    this.websocket = new WebSocket(address);

    this.websocket.onopen = () => {
      console.log("[WebSocket] Connection opened");
      // KeepAlive: 1분 간격 ping
      this.timer = setInterval(() => {
        this.websocket.send(JSON.stringify({ message: "ping" }));
        console.log("[WebSocket] Sent ping");
      }, 60000);
    };

    this.websocket.onmessage = (event) => {
      const message = JSON.parse(event.data);
      console.log("[WebSocket] Message received:", message);
      this.onMessageReceived(message);
    };

    this.websocket.onclose = (event) => {
      console.log("[WebSocket] Connection closed:", event.reason);
      this.cleanupWebSocket();
    };

    this.websocket.onerror = (error) => {
      console.error("[WebSocket] Error:", error);
      this.cleanupWebSocket();
    };
  }

  // (5) WebSocket 정리 함수
  cleanupWebSocket() {
    if (this.timer) {
      clearInterval(this.timer);
      this.timer = null;
    }
    if (this.websocket) {
      this.websocket.close();
      this.websocket = null;
    }
  }

  // (6) 메시지 수신시 처리
  onMessageReceived(message) {
    console.log("[onMessageReceived] Message data:", message);
    if (message.Timestamp) {
      this.data.messages.push(message);
      this.renderMessages();
    }
  }  

  // (7) 메시지 전송
  async onSend() {
    const messageText = this.textarea.value.trim();

    if (!messageText) return;

    // 1) 입력한 메시지를 즉시 화면에 렌더링
    const userMessage = {
      UserID: String(this.data.user_id), // 현재 사용자의 ID
      Name: this.data.name,
      Message: messageText,
      RoomID: this.data.room_id,
    };

    this.data.messages.push(userMessage); // 메시지 리스트에 추가
    this.renderMessages(); // 화면에 메시지 렌더링

    // 입력창 초기화
    this.textarea.value = "";

    // 2) 메시지를 서버로 전송
    try {
      const payload = {
        room_id: this.data.room_id,
        text: messageText,
        user_id: this.data.user_id,
        name: this.data.name,
      };

      const url = `${API_GATEWAY_HTTP_ENDPOINT}`;
      const response = await fetch(url, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      console.log("[onSend] Server response:", await response.json());
    } catch (error) {
      console.error("[onSend] Error sending message:", error);
    }
  }

  // (8) UI 이벤트 설정
  setupUI() {
    // 전송 버튼 클릭 시
    this.sendButton.addEventListener("click", () => {
      const msg = this.textarea.value.trim();
      if (msg) {
        this.onSend(msg);
        this.textarea.value = "";
      }
    });

    // Enter 키로 메시지 전송(Shift+Enter는 줄바꿈)
    this.textarea.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        const msg = this.textarea.value.trim();
        if (msg) {
          this.onSend(msg);
          this.textarea.value = "";
        }
      }
    });
  }

  // (9) 메시지 목록 렌더링
  renderMessages() {
    // 기존 메시지들 초기화
    this.messageListContainer.innerHTML = "";
  
    this.data.messages.forEach((message) => {
      // 1) messageDiv 생성
      const messageElement = document.createElement("div");
  
      // 사용자, AI, 제3자 식별
      let isCurrentUser = String(this.data.user_id) === String(message.UserID);
      let isAI = String(message.UserID) === "chatgpt";
      let isThirdParty = !isCurrentUser && !isAI; // 사용자도 AI도 아닌 경우 제3자
  
      // 스타일 클래스 추가
      messageElement.classList.add("message");
      if (isCurrentUser) {
        messageElement.classList.add("user");
      } else if (isAI) {
        messageElement.classList.add("bot");
      } else if (isThirdParty) {
        messageElement.classList.add("third-party");
      }
  
      // 2) 아바타 영역
      const avatarDiv = document.createElement("div");
      avatarDiv.classList.add("message-avatar");
  
      if (isCurrentUser) {
        // 사용자 아바타
        avatarDiv.innerHTML = `
          <svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="20" fill="#317eac" />
            <text x="50%" y="50%"
                  text-anchor="middle"
                  dominant-baseline="middle"
                  font-size="14"
                  fill="#ffffff"
                  font-family="sans-serif">
              Me
            </text>
          </svg>
        `;
      } else if (isAI) {
        // AI 아바타
        avatarDiv.innerHTML = `
          <svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="20" fill="#10a37f" />
            <text x="50%" y="50%"
                  text-anchor="middle"
                  dominant-baseline="middle"
                  font-size="14"
                  fill="#ffffff"
                  font-family="sans-serif">
              AI
            </text>
          </svg>
        `;
      } else if (isThirdParty) {
        // 제3자 아바타
        avatarDiv.innerHTML = `
          <svg width="40" height="40" xmlns="http://www.w3.org/2000/svg">
            <circle cx="20" cy="20" r="20" fill="#d4a017" />
            <text x="50%" y="50%"
                  text-anchor="middle"
                  dominant-baseline="middle"
                  font-size="12"
                  fill="#ffffff"
                  font-family="sans-serif">
              3rd
            </text>
          </svg>
        `;
      }
  
      // 3) 메시지 텍스트 부분
      const contentDiv = document.createElement("div");
      contentDiv.classList.add("message-content");
  
      const authorDiv = document.createElement("div");
      authorDiv.classList.add("message-author");
      authorDiv.textContent = isCurrentUser
        ? "나"
        : isAI
        ? "ChatGPT"
        : message.Name || "제3자";
  
      const textDiv = document.createElement("div");
      textDiv.classList.add("message-text");
      textDiv.textContent = message.Message || "(No content)";
  
      // 4) 결합
      contentDiv.appendChild(authorDiv);
      contentDiv.appendChild(textDiv);
  
      messageElement.appendChild(avatarDiv);
      messageElement.appendChild(contentDiv);
  
      // 5) 최종적으로 .chat-messages에 추가
      this.messageListContainer.appendChild(messageElement);
    });
  
    // 메시지 영역 스크롤바를 맨 아래로
    this.messageListContainer.scrollTop = this.messageListContainer.scrollHeight;
  }  
  
}
// (10) DOM이 이미 로드된 상태라면 바로 인스턴스 생성
new ChatApp();
