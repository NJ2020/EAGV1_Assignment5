# basic import 
from mcp.server.fastmcp import FastMCP, Image
from mcp.server.fastmcp.prompts import base
from mcp.types import TextContent
from mcp import types
from PIL import Image as PILImage
import math
import sys
from pywinauto.application import Application
import win32gui
import win32con
import time
from win32api import GetSystemMetrics

# instantiate an MCP server client
mcp = FastMCP("Microsoft Paint App Controller!!")

# DEFINE TOOLS

# @mcp.tool()
# async def draw_rectangle(x1: int, y1: int, x2: int, y2: int) -> dict:
#     """Draw a rectangle in Paint from (x1,y1) to (x2,y2)"""
#     global paint_app
#     try:
#         if not paint_app:
#             return {
#                 "content": [
#                     TextContent(
#                         type="text",
#                         text="Paint is not open. Please call open_paint first."
#                     )
#                 ]
#             }
        
#         # Get the Paint window
#         paint_window = paint_app.window(class_name='MSPaintApp')
        
#         # Get primary monitor width to adjust coordinates
#         primary_width = GetSystemMetrics(0)
        
#         # Ensure Paint window is active
#         if not paint_window.has_focus():
#             paint_window.set_focus()
#             time.sleep(0.2)
        
#         # Click on the Rectangle tool using the correct coordinates for secondary screen
#         paint_window.click_input(coords=(530, 82 ))
#         time.sleep(0.2)
        
#         # Get the canvas area
#         canvas = paint_window.child_window(class_name='MSPaintView')
        
#         # Draw rectangle - coordinates should already be relative to the Paint window
#         # No need to add primary_width since we're clicking within the Paint window
#         canvas.press_mouse_input(coords=(x1+2560, y1))
#         canvas.move_mouse_input(coords=(x2+2560, y2))
#         canvas.release_mouse_input(coords=(x2+2560, y2))
        
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Rectangle drawn from ({x1},{y1}) to ({x2},{y2})"
#                 )
#             ]
#         }
#     except Exception as e:
#         return {
#             "content": [
#                 TextContent(
#                     type="text",
#                     text=f"Error drawing rectangle: {str(e)}"
#                 )
#             ]
#         }


@mcp.tool()
async def add_text_in_paint(text: str) -> dict:
    """Add text inside the centered rectangle, save and close Paint"""
    global paint_app
    try:
        if not paint_app:
            return {
                "content": [TextContent(type="text", text="Paint not open.")]
            }

        paint_window = paint_app.window(class_name='MSPaintApp')
        if not paint_window.has_focus():
            paint_window.set_focus()

        canvas = paint_window.child_window(class_name='MSPaintView')

        # Use shortcut to activate text tool
        paint_window.type_keys('t')
        time.sleep(0.3)

        # Center position for typing inside the rectangle
        screen_width = GetSystemMetrics(0)
        screen_height = GetSystemMetrics(1)
        text_x = screen_width // 2
        text_y = screen_height // 2

        canvas.click_input(coords=(text_x, text_y))
        time.sleep(0.3)


        # Type the text
        paint_window.type_keys(text, with_spaces=True)
        time.sleep(0.5)


        # Step 4: Save the image (Ctrl+S)
        paint_window.type_keys('^s')  # Ctrl+S
        time.sleep(1)

        # Step 5: Type filename and press Enter
        paint_window.type_keys('C:/temp/my_drawing.png')  # Change filename as needed
        time.sleep(0.5)
        paint_window.type_keys('{ENTER}')
        time.sleep(1)

        # Step 6: Close Paint (Alt+F4)
        paint_window.type_keys('%{F4}')  # Alt+F4


        return {
            "content": [TextContent(type="text", text="Text added, saved, and Paint closed.")]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"Error: {str(e)}")]
        }

@mcp.tool()
async def open_paint() -> dict:
    """Open Microsoft Paint in maximized (fullscreen) window"""
    global paint_app
    try:
        paint_app = Application().start('mspaint.exe')
        time.sleep(0.5)

        paint_window = paint_app.window(class_name='MSPaintApp')
        paint_window.wait('visible', timeout=5)
        paint_window.set_focus()

        # Maximize the window
        win32gui.ShowWindow(paint_window.handle, win32con.SW_MAXIMIZE)
        time.sleep(0.5)

        return {
            "content": [TextContent(type="text", text="Paint opened in full screen.")]
        }
    except Exception as e:
        return {
            "content": [TextContent(type="text", text=f"Error opening Paint: {str(e)}")]
        }


# DEFINE RESOURCES

# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    print("CALLED: get_greeting(name: str) -> str:")
    return f"Hello, {name}!"


# DEFINE AVAILABLE PROMPTS
@mcp.prompt()
def review_code(code: str) -> str:
    return f"Please review this code:\n\n{code}"
    print("CALLED: review_code(code: str) -> str:")


@mcp.prompt()
def debug_error(error: str) -> list[base.Message]:
    return [
        base.UserMessage("I'm seeing this error:"),
        base.UserMessage(error),
        base.AssistantMessage("I'll help debug that. What have you tried so far?"),
    ]

if __name__ == "__main__":
    # Check if running with mcp dev command
    print("STARTING")
    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()  # Run without transport for dev server
    else:
        mcp.run(transport="stdio")  # Run with stdio for direct execution
