# YouTube Browser Control - MCP Server

Điều khiển YouTube thông qua trình duyệt Chrome bằng MCP protocol.

## Cài đặt

### 1. Cài Python
- Tải Python 3.8+ từ: https://www.python.org/downloads/
- Khi cài, **tick chọn "Add Python to PATH"**

### 2. Cài thư viện
```bash
pip install -r requirements.txt
```

### 3. Cấu hình Endpoint
- Truy cập https://xiaozhi.me để lấy WebSocket token
- Mở file `client.py`, tìm dòng `DEFAULT_ENDPOINT` (dòng 444)
- Thay thế URL bằng endpoint của bạn:
```python
DEFAULT_ENDPOINT = "wss://api.xiaozhi.me/mcp/?token=YOUR_TOKEN_HERE"
```

### 4. Chạy chương trình
```bash
python client.py
```

## Tools có sẵn

- `open_youtube` - Mở YouTube
- `search_video` - Tìm kiếm video
- `play_first_video` - Phát video đầu tiên
- `search_and_play` - Tìm và phát luôn
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
**Lưu ý:** Chrome sẽ tự động mở khi chạy tool lần đầu.
