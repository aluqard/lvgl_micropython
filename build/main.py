import lvgl as lv
import device
from utils import *

d = device.DEVICE(320, 240)

scr = lv.screen_active()
scr.clean()
prev_btn = None
setting_buttons = []
setting_pages = []

def setting_button_cb(evt, btn):
    code = evt.get_code()
    
    print('setting')
    
    if code == lv.EVENT.CLICKED:
        create_setting_window()

def setting_change_tab_cb(evt, btn, index):
    code = evt.get_code()
        
    if code == lv.EVENT.CLICKED:
        global prev_btn
        
        if prev_btn.has_state(lv.STATE.CHECKED):
            prev_btn.remove_state(lv.STATE.CHECKED)

        btn.add_state(lv.STATE.CHECKED)
        prev_btn = btn
        

def save_setting_button_cb(evt, win):
    code = evt.get_code()
    
    print('save')
    
    if code == lv.EVENT.CLICKED:
        setting_buttons.clear()
        win.delete()

def create_setting_button(symbol, title, state, parent):
    btn = lv.button(parent)
    btn.set_style_radius(0, lv.PART.MAIN)
    btn.set_style_border_width(0, lv.PART.MAIN)
    btn.set_style_border_color(lv.color_hex(0x999999), lv.PART.MAIN)
    btn.set_style_bg_color(lv.color_hex(0x1DBF77), lv.STATE.CHECKED)
    btn.set_style_border_color(lv.color_hex(0x999999), lv.STATE.CHECKED)
    btn.set_style_bg_color(lv.color_hex(0xAAAAAA), lv.STATE.DEFAULT)
    btn.set_style_border_color(lv.color_hex(0x999999), lv.STATE.DEFAULT)
    btn.set_size(lv.pct(100), lv.pct(100))
    btn.center()
    btn.add_state(state)
    #btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, btn, 0), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_style_text_font(lv.font_awesome_12, lv.PART.MAIN)
    icon.set_src(symbol)
    icon.align(lv.ALIGN.LEFT_MID, -5, 0)
    
    label = lv.label(btn)
    label.set_text(title)
    label.align(lv.ALIGN.LEFT_MID, 20, 0)
    
    return btn
    
def create_setting_window():
    global prev_btn
    global setting_buttons
    
    win = lv.win(scr)
    win.set_size(lv.pct(100), lv.pct(100))
    win.set_style_pad_all(0, lv.PART.MAIN)
    win.set_style_pad_gap(0, lv.PART.MAIN)
    win.set_style_radius(0, lv.PART.MAIN)
    win.set_style_border_width(0, lv.PART.MAIN)
    
    header_height = 30
    header = win.get_header()
    header.set_style_pad_all(0, lv.PART.MAIN)
    header.set_style_pad_gap(0, lv.PART.MAIN)
    header.set_style_radius(0, lv.PART.MAIN)
    header.set_style_border_width(0, lv.PART.MAIN)
    header.set_style_bg_color(lv.color_hex3(0x338), lv.PART.MAIN)
    header.set_size(lv.pct(100), header_height)
    header.set_flex_flow(lv.FLEX_FLOW.ROW)
    header.set_layout(lv.LAYOUT.FLEX)
    
    # WIFI
    btn = create_setting_button(lv.SYMBOL.WIFI, 'WIFI', lv.STATE.CHECKED, header)
    setting_buttons.append(btn)
    prev_btn = btn
    #btn.set_parent(header)
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, setting_buttons[0], 0), lv.EVENT.CLICKED, None)
    
    # DATE
    btn = create_setting_button(hex2utf8(0xf073), 'DATE', lv.STATE.DEFAULT, header)
    setting_buttons.append(btn)
    #btn.set_parent(header)
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, setting_buttons[1], 1), lv.EVENT.CLICKED, None)
    
    #ETC
    btn = create_setting_button(hex2utf8(0xf013), 'CONFIG', lv.STATE.DEFAULT, header)
    setting_buttons.append(btn)
    #btn.set_parent(header)
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, setting_buttons[2], 2), lv.EVENT.CLICKED, None)
    
    '''
    btn = lv.button(header)
    btn.set_style_radius(0, lv.PART.MAIN)
    btn.set_style_border_width(0, lv.PART.MAIN)
    btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
    btn.set_size(lv.pct(100), lv.pct(100))
    btn.center()
    btn.add_state(lv.STATE.CHECKED)
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, btn, 0), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.WIFI)
    icon.align(lv.ALIGN.LEFT_MID, -5, 0)
    
    label = lv.label(btn)
    label.set_text("WIFI")
    label.align(lv.ALIGN.LEFT_MID, 20, 0)
    
    # DATE
    btn = lv.button(header)
    btn.set_style_radius(0, lv.PART.MAIN)
    btn.set_style_border_width(0, lv.PART.MAIN)
    btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
    btn.set_size(lv.pct(100), lv.pct(100))
    btn.center()
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, btn, 1), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.LIST)
    icon.align(lv.ALIGN.LEFT_MID, -5, 0)
    
    label = lv.label(btn)
    label.set_text("DATE")
    label.align(lv.ALIGN.LEFT_MID, 20, 0)
    
    # ETC
    btn = lv.button(header)
    btn.set_style_radius(0, lv.PART.MAIN)
    btn.set_style_border_width(0, lv.PART.MAIN)
    btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
    btn.set_size(lv.pct(100), lv.pct(100))
    btn.center()
    btn.set_flex_grow(4)
    btn.add_event_cb(lambda e: setting_change_tab_cb(e, btn, 2), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.BATTERY_FULL)
    icon.align(lv.ALIGN.LEFT_MID, -5, 0)
    
    label = lv.label(btn)
    label.set_text("WIFI")
    label.align(lv.ALIGN.LEFT_MID, 20, 0)
    '''
    # CLOSE
    btn = lv.button(header)
    btn.set_style_radius(0, lv.PART.MAIN)
    btn.set_style_border_width(1, lv.PART.MAIN)
    btn.set_style_border_color(lv.color_hex(0x1DBFFF), lv.PART.MAIN)
    btn.set_size(lv.pct(100), lv.pct(100))
    btn.center()
    btn.set_flex_grow(1)
    btn.add_event_cb(lambda e: save_setting_button_cb(e, win), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.OK)
    icon.align(lv.ALIGN.LEFT_MID, -6, 0)
    
def create_main_screen():
    # header
    header_height = 30
    header = lv.obj(scr)
    header.set_style_pad_all(0, lv.PART.MAIN)
    header.set_style_pad_gap(0, lv.PART.MAIN)
    header.set_style_radius(0, lv.PART.MAIN)
    header.set_style_border_width(0, lv.PART.MAIN)
    header.set_style_bg_color(lv.color_hex3(0x338), lv.PART.MAIN)
    header.set_size(lv.pct(100), header_height)
    header.align(lv.ALIGN.TOP_MID, 0, 0)
    header.set_flex_flow(lv.FLEX_FLOW.ROW)
    header.set_layout(lv.LAYOUT.FLEX)

    # HOME ICON
    cell = lv.obj(header)
    cell.set_style_radius(0, lv.PART.MAIN)
    cell.set_style_border_width(0, lv.PART.MAIN)
    cell.set_style_pad_all(0, lv.PART.MAIN)
    cell.set_style_bg_color(lv.color_hex3(0x666), lv.PART.MAIN)
    cell.set_style_text_color(lv.color_hex3(0xfff), lv.PART.MAIN)
    cell.set_height(header_height)
    cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
    cell.remove_flag(lv.obj.FLAG.CLICK_FOCUSABLE | lv.obj.FLAG.CLICKABLE)
    cell.set_flex_grow(1)

    icon = lv.image(cell)
    icon.set_src(lv.SYMBOL.HOME)
    icon.align(lv.ALIGN.CENTER, 0, 0)

    # TITLE
    cell = lv.obj(header)
    cell.set_style_radius(0, lv.PART.MAIN)
    cell.set_style_border_width(0, lv.PART.MAIN)
    cell.set_style_pad_all(0, lv.PART.MAIN)
    cell.set_style_bg_color(lv.color_hex3(0x999), lv.PART.MAIN)
    cell.set_height(header_height)
    cell.remove_flag(lv.obj.FLAG.SCROLLABLE)
    cell.set_flex_grow(9)

    label = lv.label(cell)
    label.set_style_text_color(lv.color_hex3(0x000),  lv.PART.MAIN)
    label.set_text("TITLEBAR TEST !!!")
    label.align(lv.ALIGN.LEFT_MID, 10, 2)

    # 3
    '''
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
    btn.center()

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.HOME)
    icon.align(lv.ALIGN.CENTER, 0, 0)
    '''
    
    # SETTING BUTTON
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
    btn.center()
    btn.add_event_cb(lambda e: setting_button_cb(e, btn), lv.EVENT.CLICKED, None)

    icon = lv.image(btn)
    icon.set_src(lv.SYMBOL.SETTINGS)
    icon.align(lv.ALIGN.CENTER, 0, 0)

create_main_screen()

image = lv.image(scr)
image.set_src('D:sd/remove_similar_imagesx32.png')
image.center()
