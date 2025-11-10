"""
WebSocket Bridge - Kết nối MCP Server với WebSocket Endpoint
"""

import asyncio
import json
import logging
import websockets
from typing import Any

logger = logging.getLogger(__name__)


async def run_websocket_bridge(endpoint_url: str, mcp_server):
    """
    Kết nối MCP server với WebSocket endpoint
    
    Args:
        endpoint_url: WebSocket endpoint URL
        mcp_server: FastMCP server instance
    """
    
    try:
        logger.info(f"🔌 Connecting to WebSocket endpoint...")
        
        async with websockets.connect(
            endpoint_url,
            ping_interval=20,
            ping_timeout=10,
            close_timeout=10
        ) as websocket:
            logger.info("✅ WebSocket connected!")
            
            # Chờ server gửi initialize request trước
            logger.info("⏳ Waiting for initialize request from server...")
            
            init_received = False
            for _ in range(3):  # Thử đợi 3 lần
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    message = json.loads(message_str)
                    
                    if message.get("method") == "initialize":
                        logger.info("📨 Received initialize request from server")
                        
                        # Send initialize response
                        init_response = {
                            "jsonrpc": "2.0",
                            "id": message.get("id"),
                            "result": {
                                "protocolVersion": "2024-11-05",
                                "capabilities": {
                                    "tools": {}
                                },
                                "serverInfo": {
                                    "name": "youtube-browser-control",
                                    "version": "1.0.0"
                                }
                            }
                        }
                        await websocket.send(json.dumps(init_response))
                        logger.info("✅ Sent initialize response")
                        
                        init_received = True
                        break
                    else:
                        logger.debug(f"Received other message: {message.get('method', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    logger.debug("Timeout waiting for initialize, retrying...")
                    continue
            
            if not init_received:
                logger.warning("⚠️ Did not receive initialize request, continuing anyway...")
            
            # Send tools list changed notification
            tools_notif = {
                "jsonrpc": "2.0",
                "method": "notifications/tools/list_changed"
            }
            await websocket.send(json.dumps(tools_notif))
            logger.info("📤 Sent tools/list_changed notification")
            
            logger.info("")
            logger.info("=" * 60)
            logger.info("✅ Connected and ready!")
            logger.info("🎧 Listening for commands from broker...")
            logger.info("=" * 60)
            logger.info("")
            
            # Main message loop
            while True:
                try:
                    message_str = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                    
                    # Handle ping
                    if message_str == "ping":
                        await websocket.send("pong")
                        continue
                    
                    try:
                        message = json.loads(message_str)
                    except json.JSONDecodeError as e:
                        logger.error(f"❌ Failed to parse JSON: {message_str[:200]}")
                        continue
                    
                    method = message.get("method", "")
                    msg_id = message.get("id")
                    
                    logger.info(f"📨 Received: {method or f'response-{msg_id}'}")
                    logger.debug(f"   Full message: {json.dumps(message, indent=2)}")
                    
                    # Handle tools/list request
                    if method == "tools/list":
                        tools_list = get_tools_list(mcp_server)
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "result": {
                                "tools": tools_list
                            }
                        }
                        await websocket.send(json.dumps(response))
                        logger.info(f"✅ Sent {len(tools_list)} tools")
                    
                    # Handle tools/call request
                    elif method == "tools/call":
                        tool_name = message["params"]["name"]
                        tool_args = message["params"].get("arguments", {})
                        
                        logger.info(f"🔧 Calling tool: {tool_name}")
                        logger.info(f"   Arguments: {tool_args}")
                        
                        # Execute tool
                        try:
                            result = await execute_tool(mcp_server, tool_name, tool_args)
                            
                            # Send successful response
                            response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": str(result)
                                        }
                                    ],
                                    "isError": False
                                }
                            }
                            await websocket.send(json.dumps(response))
                            logger.info(f"✅ Tool executed successfully")
                            
                        except Exception as e:
                            # Send error response
                            error_response = {
                                "jsonrpc": "2.0",
                                "id": msg_id,
                                "result": {
                                    "content": [
                                        {
                                            "type": "text",
                                            "text": f"Error: {str(e)}"
                                        }
                                    ],
                                    "isError": True
                                }
                            }
                            await websocket.send(json.dumps(error_response))
                            logger.error(f"❌ Tool execution failed: {e}")
                    
                    # Handle ping request
                    elif method == "ping":
                        response = {
                            "jsonrpc": "2.0",
                            "id": msg_id,
                            "result": {}
                        }
                        await websocket.send(json.dumps(response))
                    
                    else:
                        logger.debug(f"📩 Other message: {message}")
                
                except asyncio.TimeoutError:
                    # Send ping to keep connection alive
                    try:
                        await websocket.ping()
                        logger.debug("🏓 Sent ping")
                    except Exception as e:
                        logger.warning(f"⚠️ Failed to send ping: {e}")
                        break
                except websockets.exceptions.ConnectionClosed as e:
                    logger.error(f"❌ Connection closed: code={e.code}, reason={e.reason}")
                    raise
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error: {e}")
                    continue
                except KeyError as e:
                    logger.error(f"❌ Missing key in message: {e}")
                    logger.debug(f"   Message was: {message_str[:500]}")
                    continue
                except Exception as e:
                    logger.error(f"❌ Error processing message: {e}")
                    import traceback
                    traceback.print_exc()
                    # Don't break - continue listening
    
    except websockets.exceptions.ConnectionClosedOK:
        logger.info("✅ WebSocket closed normally")
    except websockets.exceptions.ConnectionClosedError as e:
        logger.error(f"❌ WebSocket closed with error: {e.code} - {e.reason}")
    except websockets.exceptions.ConnectionClosed as e:
        logger.warning(f"⚠️ WebSocket closed: {e.code} - {e.reason}")
    except Exception as e:
        logger.error(f"❌ Connection error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        logger.info("👋 Disconnected")


def get_tools_list(mcp_server) -> list:
    """Lấy danh sách tools từ MCP server"""
    tools = []
    
    # Get tools from FastMCP server
    for tool_name, tool_obj in mcp_server._tool_manager._tools.items():
        # tool_obj is a Tool object, not a function
        tool_info = {
            "name": tool_obj.name,
            "description": tool_obj.description or f"Tool: {tool_name}",
            "inputSchema": tool_obj.parameters  # FastMCP đã có sẵn schema
        }
        
        tools.append(tool_info)
    
    return tools


async def execute_tool(mcp_server, tool_name: str, arguments: dict) -> Any:
    """Thực thi tool từ MCP server"""
    try:
        # Get tool object
        if tool_name not in mcp_server._tool_manager._tools:
            return f"❌ Tool not found: {tool_name}"
        
        tool_obj = mcp_server._tool_manager._tools[tool_name]
        tool_func = tool_obj.fn  # Get the actual function from Tool object
        
        # Execute tool
        if asyncio.iscoroutinefunction(tool_func):
            result = await tool_func(**arguments)
        else:
            result = tool_func(**arguments)
        
        return result
    
    except Exception as e:
        error_msg = f"❌ Error executing tool '{tool_name}': {str(e)}"
        logger.error(error_msg)
        import traceback
        traceback.print_exc()
        return error_msg
