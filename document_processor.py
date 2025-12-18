import fitz  # PyMuPDF
from PIL import Image
import io

def get_pdf_preview(input_path, page_num=0):
    """
    Render a page of the PDF to a PIL Image for preview.
    Returns: (PIL.Image or None, error_message or None)
    """
    try:
        doc = fitz.open(input_path)
        if len(doc) <= page_num:
            return None, "페이지 번호가 범위를 벗어났습니다."
        page = doc[page_num]
        pix = page.get_pixmap()
        img_data = pix.tobytes("png")
        return Image.open(io.BytesIO(img_data)), None
    except Exception as e:
        return None, f"PDF 미리보기 실패: {str(e)}"

def get_dominant_color(page, rect):
    """
    Get the dominant color of the area defined by rect on the page.
    Uses border pixels to avoid sampling the watermark text itself.
    Returns RGB tuple (0~1).
    """
    try:
        # Get pixmap of the rect at 1.0 (72 DPI) - high quality not needed for color
        pix = page.get_pixmap(clip=rect)
        width, height = pix.width, pix.height
        
        # If too small, just return white
        if width < 5 or height < 5:
            return (1, 1, 1)

        # Access samples
        # pix.samples is a bytes object or flat sequence
        # We need to be careful about format (RGB vs RGBA). 
        # By default get_pixmap() is RGB or RGBA depending on alpha.
        # Force RGB
        pix = page.get_pixmap(clip=rect, alpha=False)
        samples = pix.samples
        w = pix.width
        h = pix.height
        
        # We want border pixels.
        # Top row: samples[0 : w*3]
        # Bottom row: samples[(h-1)*w*3 : ]
        # Left/Right columns are strided.
        
        colors = []
        
        def add_pixel(idx):
            r = samples[idx]
            g = samples[idx+1]
            b = samples[idx+2]
            colors.append((r, g, b))

        # Top & Bottom rows
        for x in range(w):
            # Top
            add_pixel(x * 3)
            # Bottom
            add_pixel(((h - 1) * w + x) * 3)
            
        # Left & Right columns (skip corners to avoid duplication)
        for y in range(1, h - 1):
            # Left
            add_pixel((y * w) * 3)
            # Right
            add_pixel((y * w + (w - 1)) * 3)
            
        if colors:
            # Find most frequent color
            from collections import Counter
            most_common = Counter(colors).most_common(1)[0][0]
            return (most_common[0]/255.0, most_common[1]/255.0, most_common[2]/255.0)
            
    except Exception:
        pass
    return (1, 1, 1) # Default white if failed

def remove_watermark_from_pdf(input_path, output_path, rect=None, fill_color=(1, 1, 1)):
    """
    Remove watermarks from PDF inside a rectangle.
    rect: tuple (x, y, w, h) normalized (0.0 to 1.0) relative to page size.
    fill_color: tuple (r, g, b) 0.0~1.0 OR string "auto". 
                If "auto", detects color per page.
                If None, leaves it transparent (shows page bg).
    """
    try:
        doc = fitz.open(input_path)
        count = 0
        
        # We need to apply to all pages
        for page in doc:
            # Rectangle Removal
            if rect:
                # rect is normalized (0.0~1.0). Convert to page coordinates.
                rx, ry, rw, rh = rect
                width = page.rect.width
                height = page.rect.height
                
                # Calculate absolute coordinates
                x0 = rx * width
                y0 = ry * height
                x1 = (rx + rw) * width
                y1 = (ry + rh) * height
                
                pdf_rect = fitz.Rect(x0, y0, x1, y1)
                
                # Determine Color
                current_fill = fill_color
                if fill_color == "auto":
                    current_fill = get_dominant_color(page, pdf_rect)
                
                # Add Redaction Annotation
                # fill argument expects (r, g, b) or None.
                page.add_redact_annot(pdf_rect, fill=current_fill)
                
                # Apply Redaction
                # If current_fill is None (Transparent), we assume the user wants to keep the background image
                if current_fill is None:
                    page.apply_redactions(images=fitz.PDF_REDACT_IMAGE_NONE)
                else:
                    page.apply_redactions() # Default: removes everything (images included)
                
                count += 1

        doc.save(output_path)
        return True, f"처리가 완료되었습니다. (총 {count} 페이지 처리)"
    except Exception as e:
        return False, str(e)
