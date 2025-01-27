import lvgl as lv
import device

d = device.DEVICE(320, 240)

color_panel_bg = lv.color_hex(0xF27B00)
color_panel_border = lv.color_hex(0xF27B00)
color_text_bg = lv.color_hex(0xCD6800)
color_text = lv.color_hex(0x222222)

scr = lv.screen_active()
scr.set_style_bg_color(lv.color_hex(0x000000), lv.PART.MAIN)
scr.remove_flag(lv.obj.FLAG.SCROLLABLE)

def create_panel(parent, size, position, radius=6, color_bg=color_panel_bg):
    panel = lv.obj(parent)
    panel.set_style_bg_color(color_bg, lv.PART.MAIN)
    panel.set_style_pad_all(0, lv.PART.MAIN)
    panel.set_style_radius(radius, lv.PART.MAIN)
    panel.set_style_border_width(0, lv.PART.MAIN)
    panel.set_style_border_color(color_panel_border, lv.PART.MAIN)
    panel.remove_flag(lv.obj.FLAG.SCROLLABLE)
    panel.set_size(size[0], size[1])
    panel.set_pos(position[0], position[1])

    return panel

def create_label(parent, font, text_bg, text, color_text_bg, color_text, position):
    label_bg = lv.label(parent)
    label_bg.set_style_text_color(color_text_bg, lv.PART.MAIN)
    label_bg.set_style_text_font(font, lv.PART.MAIN)
    label_bg.set_text(text_bg)
    label_bg.set_pos(position[0], position[1])

    label = lv.label(parent)
    label.set_style_text_color(color_text, lv.PART.MAIN)
    label.set_style_text_font(font, lv.PART.MAIN)
    label.set_text(text)
    label.set_pos(position[0], position[1])

    return label

panel_date = create_panel(parent=scr, size=(236, 31), position=(5, 5))
panel_gps_signal = create_panel(parent=scr, size=(32, 31), position=(246, 5))
panel_wifi_signal = create_panel(parent=scr, size=(32, 31), position=(283, 5))
panel_time = create_panel(parent=scr, size=(208, 55), position=(5, 41))
panel_dummy = create_panel(parent=scr, size=(97, 55), position=(218, 41))
panel_speed = create_panel(parent=scr, size=(150, 77), position=(5, 101))
panel_location = create_panel(parent=scr, size=(155, 77), position=(160, 101))
#panel_fixed_on = create_panel(panel_location, size=(42, 18), radius=4, position=(4, 56), color_bg=color_text)
panel_fixed_off = create_panel(panel_location, size=(42, 18), radius=4, position=(4, 56), color_bg=color_text_bg)
panel_distance = create_panel(parent=scr, size=(150, 51), position=(5, 183))
panel_dist_from_home = create_panel(parent=scr, size=(155, 51), position=(160, 183))

label_date = create_label(panel_date, lv.font_seg14_bold_14, '~~~~-~~-~~   ~~~.', '2025-01-26   SAT.', color_text_bg, color_text, (5, 5))

label_time = create_label(panel_time, lv.font_seg14_bold_32, '00:00', '01:24', color_text_bg, color_text, (5, 6))
label_sec = create_label(panel_time, lv.font_seg14_bold_20, '00', '25', color_text_bg, color_text, (158, 20))

label_speed = create_label(panel_speed, lv.font_seg14_bold_32, '000', '100', color_text_bg, color_text, (5, 6))
label_speed_kmph = create_label(panel_speed, lv.font_seg14_12, '~~/~', 'KM/H', color_text_bg, color_text, (94, 54))

#label_location = create_label(panel_location, lv.font_seg14_bold_10, '~~~~~~~~', 'LOCATION', color_text_bg, color_text, (5, 5))
label_lon = create_label(panel_location, lv.font_seg14_bold_10, '~~~:~~~.~~~~~~', 'LON:028.123456', color_text_bg, color_text, (5, 5))
label_lat = create_label(panel_location, lv.font_seg14_bold_10, '~~~:~~~.~~~~~~', 'LAT:028.123456', color_text_bg, color_text, (5, 22))
label_alt = create_label(panel_location, lv.font_seg14_bold_10, '~~~:000~', 'ALT:123M', color_text_bg, color_text, (7, 39))
#label_fixed_on = create_label(panel_fixed_on, lv.font_montserrat_12, '     ', 'FIXED', color_text_bg, color_text_bg, (2, 1))
label_fixed_off = create_label(panel_fixed_off, lv.font_montserrat_12, '     ', 'FIXED', color_panel_bg, color_panel_bg, (2, 1))

label_distance_title = create_label(panel_distance, lv.font_seg14_10, '~~~~~~~~', 'DISTANCE', color_text_bg, color_text, (5, 5))
label_distance = create_label(panel_distance, lv.font_seg14_bold_20, '00000', '12345', color_text_bg, color_text, (5, 22))
label_distance_km = create_label(panel_distance, lv.font_seg14_bold_12, '~~', 'KM', color_text_bg, color_text, (113, 32))