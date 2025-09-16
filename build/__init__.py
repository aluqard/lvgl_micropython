def uni2utf8(unicode):
    return chr(int(unicode, 16)).encode('utf-8')

def hex2utf8(hexa):
    return chr(hexa).encode('utf-8')

def pct2scale(scale):
    return (int)((scale * 256) / 100)

def get_png_dimension(src):
    # Only handle variable image types
    if lv.image.src_get_type(src) != lv.image.SRC.VARIABLE:
        return 0, 0
    
    png_header = bytes(lv.image_dsc_t.__cast__(src).data.__dereference__(24))

    if png_header.startswith(b'\211PNG\r\n\032\n') and png_header[12:16] == b'IHDR':

        try:
             width, height = struct.unpack(">LL", png_header[16:24])
        except:
            return 0, 0

    # Maybe this is for an older PNG version.
    elif png_header.startswith(b'\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        try:
            width, height = struct.unpack(">LL", png_header[8:16])
        except struct.error:
            return 0, 0
    else:
        return 0, 0

    return width, height

def  get_png_info(src, header):
    # Only handle variable image types
    if lv.image.src_get_type(src) != lv.image.SRC.VARIABLE:
        return lv.RESULT.INVALID
    
    png_header = bytes(lv.image_dsc_t.__cast__(src).data.__dereference__(24))

    if png_header.startswith(b'\211PNG\r\n\032\n') and png_header[12:16] == b'IHDR':

        try:
             width, height = struct.unpack(">LL", png_header[16:24])
        except:
            return lv.RESULT.INVALID

    # Maybe this is for an older PNG version.
    elif png_header.startswith(b'\211PNG\r\n\032\n'):
        # Check to see if we have the right content type
        try:
            width, height = struct.unpack(">LL", png_header[8:16])
        except struct.error:
            return lv.RESULT.INVALID
    else:
        return lv.RESULT.INVALID
    
    #header.always_zero = 0
    header.w = width
    header.h = height
    header.stride = header.w * 4
    header.flags = lv.image.FLAGS.COMPRESSED
    header.magic = lv.IMAGE_HEADER_MAGIC
    header.cf = lv.COLOR_FORMAT.ARGB8888

    print("width=%d, height=%d" % (header.w, header.h))
    return lv.RESULT.OK

def createimagefromfile2(path):
    with open(path, 'rb') as f:
        data = f.read()
    
    imagedsc = lv.image_dsc_t({
        'data_size': len(data),
        'data': data
    })
    
    return imagedsc

def createimagefromfile(path):
    
    with open(path, 'rb') as f:
        data = f.read()
    
    imagedsc = lv.image_dsc_t({
        'data_size': len(data),
        'data': data
    })
    
    image_header = lv.image_header_t()
    if get_png_info(imagedsc, image_header) == lv.RESULT.OK:
        draw_image_dsc = lv.draw_image_dsc_t()
        draw_image_dsc.init()
        draw_image_dsc.src = imagedsc
        #draw_image_dsc.header = image_header
        draw_image_dsc.original_area.x1 = 0
        draw_image_dsc.original_area.y1 = 0
        draw_image_dsc.original_area.x2 = image_header.w
        draw_image_dsc.original_area.y2 = image_header.h
        
        canvas = lv.canvas(None)
        
        size = image_header.w * image_header.h * 4
        
        buf = bytearray(size)
        canvas.set_buffer(buf, image_header.w, image_header.h, lv.COLOR_FORMAT.ARGB8888)
        
        layer = lv.layer_t()
        canvas.init_layer(layer)
        
        lv.draw_image(layer, draw_image_dsc, draw_image_dsc.original_area)
        
        canvas.finish_layer(layer)
        canvas_img = canvas.get_image()
        
        image_dsc = lv.image_dsc_t()
        image_dsc.header = canvas_img.header
        image_dsc.data_size = size
        image_dsc.data = memoryview(buf)
        
        canvas.delete()
        
        return image_dsc
    
def pct2scale(scale):
    return (int)((scale * 256) / 100)

def calculateSignalLevel(rssi, numLevels):
    
    MIN_RSSI = const(-100)
    MAX_RSSI = const(-55)

    if rssi <= MIN_RSSI:
        return 0
    
    elif rssi >= MAX_RSSI:
        return numLevels - 1
    
    else:
        inputRange = (MAX_RSSI - MIN_RSSI)
        outputRange = (numLevels - 1)
        return (int)((rssi - MIN_RSSI) * outputRange / inputRange)
    
def pct2scale(scale):
    return (int)((scale * 256) / 100)