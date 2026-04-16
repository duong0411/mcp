# YouTube Browser Control - MCP Server

YouTube automation MCP server using Playwright + Gemini agent (no Selenium).

## Cài đặt

### 1. Cài Python
- Tải Python 3.8+ từ: https://www.python.org/downloads/
- Khi cài, **tick chọn "Add Python to PATH"**

### 2. Cài thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình API key + Endpoint
- Tạo file `.env` với nội dung:
```env
GEMINI_API_KEY=YOUR_GEMINI_API_KEY
MCP_ENDPOINT=wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN_HERE
# Tùy chọn: tắt tự kết nối lại khi WebSocket rớt (mặc định bật)
# MCP_WS_RECONNECT=false
```
- Truy cập https://xiaozhi.me để lấy WebSocket token cho `MCP_ENDPOINT`.
- Nếu log vẫn báo đóng kết nối mã **1006** sau khi cập nhật bridge (heartbeat + reconnect), broker hoặc mạng có thể đang **timeout** trong lúc chờ `tools/call` lâu — kiểm tra giới hạn thời gian / chính sách phía xiaozhi hoặc proxy cục bộ.

### 4. Chạy chương trình
```bash
python client.py
```

## Tools có sẵn

- `open_youtube` - Mở YouTube
- `search_video` - Tìm kiếm video
- `play_first_video` - Phát video đầu tiên
- `search_and_play` - Prompt automation: mở YouTube, tìm query, chọn video phù hợp, phát video
- `search_and_play_with_agent` - Alias của `search_and_play`
- `skip_ad` - Bỏ qua quảng cáo
- `toggle_fullscreen` - Bật/tắt fullscreen
- `get_current_url` - Lấy URL hiện tại
- `close_browser` - Đóng trình duyệt

## Chế độ chạy

```bash
# WebSocket (mặc định)
python client.py

# Debug mode
python client.py --debug

# Stdio mode
python client.py stdio
```

---
**Lưu ý:** Server giữ browser session để bạn có thể gọi nhiều tool liên tiếp (`search_video` -> `play_first_video` -> `skip_ad`).
"# mcp" 
