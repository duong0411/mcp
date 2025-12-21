"""
YouTube Browser Control - MCP Server
Expose YouTube automation tools qua MCP protocol
Server này được gọi bởi MCP broker/proxy
"""

import logging
from mcp.server.fastmcp import FastMCP
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager

# Thiết lập logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Tạo MCP server
mcp = FastMCP("YouTube Browser Control")

# Browser instance global (sẽ được khởi tạo khi cần)
_browser = None

def get_browser():
    """Lấy hoặc khởi tạo browser instance"""
    global _browser
    
    # Kiểm tra xem browser có còn hoạt động không
    if _browser is not None:
        try:
            # Thử lấy window handle để kiểm tra browser còn sống
            _ = _browser.current_url
        except Exception as e:
            # Browser đã bị đóng hoặc crashed
            logger.warning(f"⚠️ Browser đã bị đóng, khởi tạo lại... ({str(e)[:50]})")
            _browser = None
    
    # Khởi tạo browser nếu chưa có hoặc đã bị đóng
    if _browser is None:
        logger.info("🚀 Khởi tạo Chrome browser...")
        chrome_options = Options()
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--start-maximized")
        
        service = Service(ChromeDriverManager().install())
        _browser = webdriver.Chrome(service=service, options=chrome_options)
        logger.info("✅ Browser đã sẵn sàng")
    
    return _browser

@mcp.tool()
def open_youtube() -> str:
    """Mở trình duyệt Chrome và điều hướng đến trang YouTube"""
    try:
        browser = get_browser()
        browser.get("https://www.youtube.com")
        WebDriverWait(browser, 10).until(
            EC.presence_of_element_located((By.TAG_NAME, "body"))
        )
        logger.info("✅ Đã mở YouTube")
        return "✅ Đã mở YouTube thành công"
    except Exception as e:
        error_msg = f"❌ Lỗi khi mở YouTube: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def search_video(query: str) -> str:
    """
    Tìm kiếm video trên YouTube theo từ khóa
    Args:
        query: Từ khóa tìm kiếm video
    """
    try:
        browser = get_browser()
        
        # Đảm bảo đang ở YouTube
        if "youtube.com" not in browser.current_url:
            browser.get("https://www.youtube.com")
            WebDriverWait(browser, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
        
        # Tìm search box - thử nhiều selector
        search_box = None
        selectors = [
            (By.NAME, "search_query"),
            (By.CSS_SELECTOR, "input#search"),
            (By.CSS_SELECTOR, "input[name='search_query']"),
            (By.XPATH, "//input[@id='search']")
        ]
        
        for by, selector in selectors:
            try:
                search_box = WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                if search_box:
                    break
            except:
                continue
        
        if not search_box:
            return "❌ Không tìm thấy search box"
        
        # Clear và nhập search query
        search_box.clear()
        search_box.send_keys(query)
        search_box.send_keys(Keys.RETURN)
        
        # Đợi kết quả load - thử nhiều selector
        import time
        time.sleep(2)  # Đợi trang load
        
        result_selectors = [
            (By.CSS_SELECTOR, "ytd-video-renderer"),
            (By.CSS_SELECTOR, "ytd-grid-video-renderer"),
            (By.ID, "video-title"),
            (By.CSS_SELECTOR, "a#video-title"),
            (By.XPATH, "//ytd-video-renderer//a[@id='video-title']")
        ]
        
        for by, selector in result_selectors:
            try:
                WebDriverWait(browser, 5).until(
                    EC.presence_of_element_located((by, selector))
                )
                logger.info(f"✅ Đã tìm kiếm: {query}")
                return f"✅ Đã tìm kiếm '{query}' thành công. Tìm thấy kết quả."
            except:
                continue
        
        logger.info(f"✅ Đã tìm kiếm: {query}")
        return f"✅ Đã tìm kiếm '{query}' thành công"
    except Exception as e:
        error_msg = f"❌ Lỗi khi tìm kiếm: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def play_first_video() -> str:
    """Phát video đầu tiên trong kết quả tìm kiếm"""
    try:
        browser = get_browser()
        
        # Thử nhiều cách để tìm video đầu tiên
        video_selectors = [
            # Selector cho ytd-video-renderer (search results)
            (By.CSS_SELECTOR, "ytd-video-renderer a#video-title"),
            (By.CSS_SELECTOR, "ytd-video-renderer #video-title"),
            # Selector cho ytd-grid-video-renderer (grid layout)
            (By.CSS_SELECTOR, "ytd-grid-video-renderer a#video-title"),
            (By.CSS_SELECTOR, "ytd-grid-video-renderer #video-title"),
            # Selector chung
            (By.CSS_SELECTOR, "a#video-title"),
            (By.ID, "video-title"),
            # XPath fallback
            (By.XPATH, "//ytd-video-renderer//a[@id='video-title']"),
            (By.XPATH, "//ytd-grid-video-renderer//a[@id='video-title']"),
            (By.XPATH, "//a[@id='video-title' and @href]"),
        ]
        
        first_video = None
        video_title = "Unknown"
        
        for by, selector in video_selectors:
            try:
                # Tìm tất cả videos matching selector
                videos = WebDriverWait(browser, 5).until(
                    EC.presence_of_all_elements_located((by, selector))
                )
                
                # Lọc ra những video có thể click và có href
                for video in videos:
                    try:
                        if video.is_displayed() and video.get_attribute("href"):
                            first_video = video
                            video_title = video.get_attribute("title") or video.text or "Video"
                            break
                    except:
                        continue
                
                if first_video:
                    logger.info(f"✅ Tìm thấy video bằng selector: {selector}")
                    break
            except Exception as e:
                logger.debug(f"Selector {selector} không hoạt động: {e}")
                continue
        
        if not first_video:
            return "❌ Không tìm thấy video nào để phát. Vui lòng tìm kiếm trước."
        
        # Scroll đến video để đảm bảo nó visible
        browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", first_video)
        import time
        time.sleep(0.5)
        
        # Click vào video
        try:
            first_video.click()
        except:
            # Nếu click thường không work, dùng JavaScript
            browser.execute_script("arguments[0].click();", first_video)
        
        # Đợi video player load
        import time
        time.sleep(3)  # Đợi trang video load
        
        # Chuyển sang full screen
        try:
            # Thử tìm nút fullscreen
            fullscreen_selectors = [
                (By.CSS_SELECTOR, "button.ytp-fullscreen-button"),
                (By.CSS_SELECTOR, ".ytp-fullscreen-button"),
                (By.XPATH, "//button[@aria-label='Full screen (f)']"),
                (By.XPATH, "//button[contains(@class, 'ytp-fullscreen-button')]"),
            ]
            
            fullscreen_btn = None
            for by, selector in fullscreen_selectors:
                try:
                    fullscreen_btn = WebDriverWait(browser, 5).until(
                        EC.element_to_be_clickable((by, selector))
                    )
                    if fullscreen_btn:
                        break
                except:
                    continue
            
            if fullscreen_btn:
                fullscreen_btn.click()
                logger.info(f"✅ Đã chuyển sang chế độ full screen")
            else:
                # Fallback: dùng phím tắt 'f'
                from selenium.webdriver.common.action_chains import ActionChains
                ActionChains(browser).send_keys('f').perform()
                logger.info(f"✅ Đã gửi phím tắt 'f' để full screen")
        except Exception as fs_error:
            logger.warning(f"⚠️ Không thể chuyển full screen: {fs_error}")
            # Không return error, video vẫn đang phát
        
        logger.info(f"✅ Đang phát: {video_title}")
        return f"✅ Đang phát video '{video_title}' ở chế độ full screen"
    except Exception as e:
        error_msg = f"❌ Lỗi khi phát video: {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg

@mcp.tool()
def search_and_play(query: str) -> str:
    """
    Tìm kiếm và tự động phát video đầu tiên
    Args:
        query: Từ khóa tìm kiếm video để phát
    """
    try:
        # Tìm kiếm
        search_result = search_video(query)
        if "❌" in search_result:
            return search_result
        
        # Đợi một chút để kết quả load
        import time
        time.sleep(2)
        
        # Phát video đầu tiên
        return play_first_video()
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def get_current_url() -> str:
    """Lấy URL hiện tại của trình duyệt"""
    try:
        browser = get_browser()
        url = browser.current_url
        logger.info(f"📍 URL hiện tại: {url}")
        return f"📍 URL hiện tại: {url}"
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def close_browser() -> str:
    """Đóng trình duyệt Chrome"""
    global _browser
    try:
        if _browser:
            _browser.quit()
            _browser = None
            logger.info("✅ Đã đóng trình duyệt")
            return "✅ Đã đóng trình duyệt"
        return "ℹ️ Trình duyệt chưa mở"
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def toggle_fullscreen() -> str:
    """Bật/tắt chế độ full screen cho video đang phát"""
    try:
        browser = get_browser()
        
        # Thử click nút fullscreen
        fullscreen_selectors = [
            (By.CSS_SELECTOR, "button.ytp-fullscreen-button"),
            (By.CSS_SELECTOR, ".ytp-fullscreen-button"),
            (By.XPATH, "//button[@aria-label='Full screen (f)']"),
            (By.XPATH, "//button[contains(@class, 'ytp-fullscreen-button')]"),
        ]
        
        fullscreen_btn = None
        for by, selector in fullscreen_selectors:
            try:
                fullscreen_btn = WebDriverWait(browser, 3).until(
                    EC.element_to_be_clickable((by, selector))
                )
                if fullscreen_btn:
                    break
            except:
                continue
        
        if fullscreen_btn:
            fullscreen_btn.click()
            logger.info("✅ Đã toggle full screen")
            return "✅ Đã chuyển đổi chế độ full screen"
        else:
            # Fallback: dùng phím tắt 'f'
            from selenium.webdriver.common.action_chains import ActionChains
            ActionChains(browser).send_keys('f').perform()
            logger.info("✅ Đã gửi phím tắt 'f'")
            return "✅ Đã gửi phím tắt 'f' để toggle full screen"
    except Exception as e:
        error_msg = f"❌ Lỗi: {str(e)}"
        logger.error(error_msg)
        return error_msg

@mcp.tool()
def skip_ad() -> str:
    """Bỏ qua quảng cáo YouTube đang phát (nếu có nút Skip)"""
    try:
        browser = get_browser()
        
        # Các selector khác nhau cho nút Skip Ad
        skip_button_selectors = [
            # Nút "Skip Ad" chính
            (By.CSS_SELECTOR, "button.ytp-ad-skip-button"),
            (By.CSS_SELECTOR, ".ytp-ad-skip-button"),
            (By.CSS_SELECTOR, "button.ytp-skip-ad-button"),
            (By.CSS_SELECTOR, ".ytp-skip-ad-button"),
            # Text-based selectors
            (By.XPATH, "//button[contains(@class, 'ytp-ad-skip-button')]"),
            (By.XPATH, "//button[contains(., 'Skip Ad')]"),
            (By.XPATH, "//button[contains(., 'Skip Ads')]"),
            (By.XPATH, "//button[contains(., 'Bỏ qua quảng cáo')]"),
            # Modern YouTube ad skip button
            (By.CSS_SELECTOR, ".ytp-ad-skip-button-modern"),
            (By.CSS_SELECTOR, "button.ytp-ad-skip-button-modern"),
        ]
        
        skip_button = None
        for by, selector in skip_button_selectors:
            try:
                # Đợi tối đa 2 giây cho mỗi selector
                skip_button = WebDriverWait(browser, 2).until(
                    EC.element_to_be_clickable((by, selector))
                )
                if skip_button and skip_button.is_displayed():
                    logger.info(f"✅ Tìm thấy nút skip bằng: {selector}")
                    break
            except:
                continue
        
        if skip_button:
            # Scroll đến nút để đảm bảo có thể click
            try:
                browser.execute_script("arguments[0].scrollIntoView({block: 'center'});", skip_button)
            except:
                pass
            
            # Click nút skip
            try:
                skip_button.click()
            except:
                # Fallback: dùng JavaScript click
                browser.execute_script("arguments[0].click();", skip_button)
            
            logger.info("✅ Đã bỏ qua quảng cáo")
            return "✅ Đã bỏ qua quảng cáo thành công"
        else:
            # Kiểm tra xem có đang có quảng cáo không
            ad_indicators = [
                (By.CSS_SELECTOR, ".ytp-ad-player-overlay"),
                (By.CSS_SELECTOR, ".video-ads"),
                (By.XPATH, "//div[contains(@class, 'ad-showing')]"),
            ]
            
            has_ad = False
            for by, selector in ad_indicators:
                try:
                    element = browser.find_element(by, selector)
                    if element and element.is_displayed():
                        has_ad = True
                        break
                except:
                    continue
            
            if has_ad:
                return "⏳ Có quảng cáo nhưng nút Skip chưa xuất hiện. Vui lòng đợi vài giây và thử lại."
            else:
                return "ℹ️ Không có quảng cáo đang phát hoặc quảng cáo không thể bỏ qua"
    except Exception as e:
        error_msg = f"❌ Lỗi khi bỏ qua quảng cáo: {str(e)}"
        logger.error(error_msg)
        return error_msg

if __name__ == "__main__":
    import sys
    import asyncio
    
    # Endpoint mặc định
    DEFAULT_ENDPOINT = "wss://api.xiaozhi.me/mcp/?token=eyJhbGciOiJFUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOjQ4NTkzMywiYWdlbnRJZCI6NjczMDc3LCJlbmRwb2ludElkIjoiYWdlbnRfNjczMDc3IiwicHVycG9zZSI6Im1jcC1lbmRwb2ludCIsImlhdCI6MTc2MjQ0ODEyOSwiZXhwIjoxNzk0MDA1NzI5fQ.YT5HRIktfcdpgKHeLgW050VQJFCWblI2ncEZEuJRxQF-rUKSjeX119KVep-RAuPn9MbsQzUiBdl6PaxOqrXpLA"
    
    # Kiểm tra debug flag
    debug_mode = "--debug" in sys.argv or "-v" in sys.argv
    if debug_mode:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.setLevel(logging.DEBUG)
        sys.argv = [arg for arg in sys.argv if arg not in ["--debug", "-v"]]
    
    # Kiểm tra arguments
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        
        if mode == "stdio":
            # Chế độ stdio - chuẩn MCP server
            logger.info("🎬 Starting YouTube Browser Control MCP Server (STDIO mode)...")
            logger.info("📋 Available tools: open_youtube, search_video, play_first_video, search_and_play, get_current_url, toggle_fullscreen, skip_ad, close_browser")
            mcp.run()
        elif mode == "websocket" or mode == "ws":
            # Chế độ WebSocket - kết nối đến broker
            endpoint = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_ENDPOINT
            
            logger.info("🎬 Starting YouTube Browser Control (WebSocket mode)...")
            logger.info(f"🔗 Connecting to: {endpoint[:80]}...")
            if debug_mode:
                logger.info("🐛 Debug mode enabled")
            
            from websocket_bridge import run_websocket_bridge
            asyncio.run(run_websocket_bridge(endpoint, mcp))
        else:
            print("Usage:")
            print("  python client.py [--debug]              # Run with default WebSocket endpoint")
            print("  python client.py stdio                  # Run as MCP server (stdio)")
            print("  python client.py websocket [url]        # Connect to WebSocket endpoint")
            print("  python client.py websocket --debug      # Connect with debug logging")
    else:
        # Mặc định: chạy WebSocket mode với endpoint mặc định
        logger.info("🎬 Starting YouTube Browser Control (WebSocket mode - Default)")
        logger.info(f"🔗 Connecting to default endpoint...")
        logger.info("💡 Tip: Use 'python client.py --debug' for verbose logging")
        logger.info("💡 Tip: Use 'python client.py stdio' for standard MCP server mode")
        logger.info("")
        
        from websocket_bridge import run_websocket_bridge
        asyncio.run(run_websocket_bridge(DEFAULT_ENDPOINT, mcp))
