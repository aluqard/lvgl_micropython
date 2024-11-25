from micropython import const
import lcd_bus
import sdl_pointer
import task_handler
import lvgl as lv
import sdl_display
import display_driver_framework
import fs_driver

_WIDTH = const(480)
_HEIGHT = const(320)

bus = lcd_bus.SDLBus(flags=0)
buf1 = bus.allocate_framebuffer(_WIDTH * _HEIGHT * 4, 0)

display = sdl_display.SDLDisplay(
    data_bus=bus,
    display_width=_WIDTH,
    display_height=_HEIGHT,
    frame_buffer1=buf1,
    color_space=lv.COLOR_FORMAT.ARGB8888,
    color_byte_order=display_driver_framework.BYTE_ORDER_BGR
)
display.init()

mouse = sdl_pointer.SDLPointer()
th = task_handler.TaskHandler(duration=5)

fs_drv = lv.fs_drv_t()
fs_driver.fs_register(fs_drv, 'D')

def btn_cb(evt):
    code = evt.get_code()

    if code == lv.EVENT.CLICKED:
        print('clicked')

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), 0)

header_height = 40
header = lv.obj(scr)
header.set_style_pad_all(0, lv.PART.MAIN)
header.set_style_pad_gap(0, lv.PART.MAIN)
header.set_style_radius(0, lv.PART.MAIN)
header.set_style_border_width(0, lv.PART.MAIN)
header.set_style_bg_color(lv.color_hex(0x030308), lv.PART.MAIN)
header.set_size(lv.pct(100), header_height)
header.align(lv.ALIGN.TOP_MID, 0, 0)
header.set_flex_flow(lv.FLEX_FLOW.ROW)
header.set_layout(lv.LAYOUT.FLEX)

# 1
cell = lv.obj(header)
cell.set_style_radius(0, lv.PART.MAIN)
cell.set_style_border_width(0, lv.PART.MAIN)
cell.set_style_pad_all(0, lv.PART.MAIN)
cell.set_style_bg_color(lv.color_hex3(0x666), lv.PART.MAIN)
cell.set_style_text_color(lv.color_hex3(0xfff), lv.PART.MAIN)
cell.set_height(header_height)
cell.set_style_text_font(lv.font_montserrat_16, 0)
cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
cell.set_flex_grow(1)

icon = lv.image(cell)
icon.set_src(lv.SYMBOL.HOME)
#icon.set_size(38, 38)
#icon.set_scale(pct2scale(80))
icon.align(lv.ALIGN.CENTER, 0, 0)

# 2
cell = lv.obj(header)
cell.set_style_radius(0, lv.PART.MAIN)
cell.set_style_border_width(0, lv.PART.MAIN)
cell.set_style_pad_all(0, lv.PART.MAIN)
cell.set_style_bg_color(lv.color_hex3(0x999), lv.PART.MAIN)
cell.set_height(header_height)
cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
cell.set_flex_grow(8)

label = lv.label(cell)
label.set_style_text_font(lv.font_montserrat_16, 0)
label.set_style_text_color(lv.color_hex3(0x000),  lv.PART.MAIN)
label.set_text(b'\xEF\x8A\x87')
label.align(lv.ALIGN.LEFT_MID, 10, 2)

# 3
cell = lv.obj(header)
cell.set_style_radius(0, lv.PART.MAIN)
cell.set_style_border_width(0, lv.PART.MAIN)
cell.set_style_pad_all(0, lv.PART.MAIN)
cell.set_style_bg_color(lv.color_hex3(0x999), lv.PART.MAIN)
cell.set_height(header_height)
cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
cell.set_flex_grow(1)

btn = lv.button(cell)
btn.set_style_radius(0, lv.PART.MAIN)
btn.set_size(lv.pct(90), lv.pct(90))
btn.set_style_border_width(1, lv.PART.MAIN)
btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
btn.set_style_text_font(lv.font_montserrat_16, 0)
btn.center()
btn.add_event_cb(btn_cb, lv.EVENT.CLICKED, None)

icon = lv.image(btn)
icon.set_src(lv.SYMBOL.HOME)
icon.align(lv.ALIGN.CENTER, 0, 0)

#4
cell = lv.obj(header)
cell.set_style_radius(0, lv.PART.MAIN)
cell.set_style_border_width(0, lv.PART.MAIN)
cell.set_style_pad_all(0, lv.PART.MAIN)
cell.set_style_bg_color(lv.color_hex3(0x999), lv.PART.MAIN)
cell.set_height(header_height)
cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
cell.set_flex_grow(1)

btn = lv.button(cell)
btn.set_style_radius(0, lv.PART.MAIN)
btn.set_style_border_width(1, lv.PART.MAIN)
btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
btn.set_size(lv.pct(90), lv.pct(90))
btn.set_style_text_font(lv.font_montserrat_16, 0)
btn.center()
btn.add_event_cb(btn_cb, lv.EVENT.CLICKED, None)

icon = lv.image(btn)
icon.set_src(lv.SYMBOL.SETTINGS)
icon.align(lv.ALIGN.CENTER, 0, 0)

image = lv.image(scr)
image.set_src('D:sd/remove_similar_imagesx32.png')
image.center()
