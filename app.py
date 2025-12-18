import streamlit as st
import tempfile
import os
import cv2
import numpy as np
from PIL import Image
from streamlit_drawable_canvas import st_canvas
from processor import process_video_with_mask
from document_processor import remove_watermark_from_pdf, get_pdf_preview

st.set_page_config(page_title="Magic Remover All-in-One", page_icon="🪄")

st.title("🪄 매직 워터마크 제거기 (All-in-One)")
st.markdown("동영상과 문서의 워터마크를 손쉽게 제거하세요.")

tab1, tab2 = st.tabs(["🎬 동영상 (Video)", "📄 문서 (PDF/PPT)"])

# --- TAB 1: Video Watermark Remover ---
with tab1:
    st.header("동영상 워터마크 제거")
    
    # Sidebar controls specific to video
    col1, col2 = st.columns(2)
    with col1:
        stroke_width = st.slider("브러시 크기 (Brush Size)", 1, 50, 20, key="video_stroke")
    with col2:
        drawing_mode = st.radio(
            "도구 선택:",
            ("브러시 (Brush)", "사각형 (Rectangle)"),
            horizontal=True,
            key="video_tool"
        )
    
    stroke_color = "#ffffff"
    bg_color = "#000000"
    realtime_update = True
    drawing_mode_val = "freedraw" if "브러시" in drawing_mode else "rect"

    uploaded_file = st.file_uploader("동영상 파일 업로드 (Upload Video)", type=["mp4", "mov", "avi"], key="video_upload")

    if uploaded_file is not None:
        # Save uploaded file to temp directory
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name
        
        # Video extraction for preview
        vid_cap = cv2.VideoCapture(video_path)
        total_frames = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        st.caption(f"총 프레임 수: {total_frames}")
        
        # Frame selection
        frame_index = st.slider("마스크를 그릴 프레임 선택", 0, total_frames-1, 0, key="video_frame_slider")
        vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = vid_cap.read()
        
        if ret and frame is not None:
            # Convert Frame (BGR) to RGB for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)
            
            st.info("워터마크 영역을 하얀색으로 덮어주세요.")
            
            # Canvas logic
            max_width = 700 
            img_w, img_h = pil_image.size
            if img_w > max_width:
                ratio = max_width / img_w
                canvas_width = max_width
                canvas_height = int(img_h * ratio)
            else:
                canvas_width = img_w
                canvas_height = img_h
            
            # Resize image to exactly match canvas dimensions
            canvas_bg_image = pil_image.resize((canvas_width, canvas_height), Image.Resampling.LANCZOS)
            # Convert to RGBA to ensure compatibility with canvas
            if canvas_bg_image.mode != 'RGBA':
                canvas_bg_image = canvas_bg_image.convert('RGBA')

            canvas_result = st_canvas(
                fill_color="rgba(255, 255, 255, 1.0)",
                stroke_width=stroke_width if drawing_mode_val == "freedraw" else 1,
                stroke_color=stroke_color,
                background_image=canvas_bg_image,
                update_streamlit=realtime_update,
                height=canvas_height,
                width=canvas_width,
                drawing_mode=drawing_mode_val,
                key="canvas",
            )
            
            if st.button("동영상 워터마크 제거 시작", key="video_process_btn"):
                if canvas_result.image_data is not None:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("준비 중...")
                    
                    def update_progress(p):
                        progress_int = int(p * 100)
                        progress_bar.progress(min(progress_int, 100))
                        status_text.text(f"처리 중... {progress_int}% 완료")

                    mask_data = canvas_result.image_data
                    mask_u8 = mask_data[:, :, 0].astype(np.uint8)
                    mask_original_size = cv2.resize(mask_u8, (img_w, img_h), interpolation=cv2.INTER_NEAREST)
                    
                    output_file = tempfile.NamedTemporaryFile(delete=False, suffix='_fixed.mp4')
                    output_path = output_file.name
                    output_file.close()
                    
                    success, message = process_video_with_mask(video_path, output_path, mask_original_size, progress_callback=update_progress)
                    
                    if success:
                        progress_bar.progress(100)
                        status_text.text("작업 완료!")
                        st.success("작업 완료!")
                        st.video(output_path)
                        with open(output_path, 'rb') as f:
                            st.download_button('결과 동영상 다운로드', f, file_name='fixed_video.mp4')
                    else:
                        st.error(f"오류: {message}")
                else:
                    st.warning("먼저 워터마크 영역을 칠해주세요.")
        
        vid_cap.release()

# --- TAB 2: PDF Watermark Remover ---
with tab2:
    st.header("PDF 워터마크 제거")
    st.markdown("""
    **사용 가이드**:
    1. **PDF 파일**을 업로드하세요.
    2. 첫 페이지에서 지우고 싶은 **영역(워터마크)**을 마우스로 드래그하세요.
    3. '제거 시작'을 누르면 모든 페이지의 해당 위치가 지워집니다.
    """)
    
    doc_file = st.file_uploader("PDF 파일 업로드", type=["pdf"], key="doc_upload")
    
    rect_coords = None
    
    if doc_file:
        ext = doc_file.name.split('.')[-1].lower()
        
        # Save temp input first to generate preview
        input_tfile = tempfile.NamedTemporaryFile(delete=False, suffix=f'.{ext}')
        input_tfile.write(doc_file.read())
        input_path = input_tfile.name
        input_tfile.close() # Close to allow reading
        
        if ext == 'pdf':
            # Options: Guide and Color Picker
            col1, col2 = st.columns([1, 1])
            with col1:
                 st.info("워터마크 영역을 드래그하여 선택하세요.")
            
            # Canvas Logic First (to get rect_coords for color detection)
            # We need to render canvas first to get the selection, BUT Streamlit renders top-down.
            # So, we usually render canvas, then on RERUN we have the data.
            # But the options are above the canvas? 
            # We can put options BELOW canvas? Or keep them above and use previous run's data?
            # Using previous run's data is standard Streamlit behavior.
            
            # Canvas rendering
            # Get Preview of Page 0
            pil_image, error_msg = get_pdf_preview(input_path, 0)
            
            if error_msg:
                st.error(error_msg)
            
            canvas_result_pdf = None
            rect_coords = None
            
            if pil_image:
                max_width = 700
                img_w, img_h = pil_image.size
                if img_w > max_width:
                    ratio = max_width / img_w
                    canvas_width = max_width
                    canvas_height = int(img_h * ratio)
                    scale_factor = img_w / max_width 
                else:
                    canvas_width = img_w
                    canvas_height = img_h
                    scale_factor = 1.0

                # Render Canvas
                canvas_result_pdf = st_canvas(
                    fill_color="rgba(255, 0, 0, 0.3)",
                    stroke_width=1,
                    stroke_color="#ff0000",
                    background_color="#ffffff",
                    background_image=pil_image,
                    update_streamlit=True,
                    height=canvas_height,
                    width=canvas_width,
                    drawing_mode="rect",
                    key=f"canvas_pdf_{doc_file.name}",
                )
                
                if canvas_result_pdf.json_data is not None:
                    objects = canvas_result_pdf.json_data["objects"]
                    if len(objects) > 0:
                        obj = objects[-1]
                        r_left = obj["left"] * scale_factor
                        r_top = obj["top"] * scale_factor
                        r_width = obj["width"] * scale_factor
                        r_height = obj["height"] * scale_factor
                        rect_coords = (r_left, r_top, r_width, r_height)
                        st.caption(f"선택된 영역: {int(r_left)}, {int(r_top)} ({int(r_width)}x{int(r_height)})")

                        # --- Smart Color Detection ---
                        # Removed as we are now using "Auto" mode exclusively which handles this in backend.
                        pass

            
            # Options (Moved below canvas or keep above? If above, it uses old state. Let's move below for better flow?)
            # The User said "Covering with same color is best".
            # Let's put the options nicely alongside the Process button or just above it.
            
            with col2:
                # Simply inform the user
                st.markdown("### 설정")
                st.info("ℹ️ **자동 감지 모드**: 각 페이지의 배경색을 자동으로 분석하여 워터마크를 덮습니다.")
                
                fill_color = "auto"
                            
        # Processing Button
        if st.button("워터마크 제거 시작", key="doc_process_btn_visual"):
            if not rect_coords:
                st.warning("사각형 영역을 선택해주세요.")
            else:
                with st.spinner("PDF 처리 중..."):
                    output_path = input_path.replace(f'.{ext}', f'_fixed.{ext}')
                    
                    if ext == 'pdf':
                        safe_rect = None
                        if rect_coords:
                             if 'pil_image' in locals() and pil_image:
                                 nx = rect_coords[0] / img_w
                                 ny = rect_coords[1] / img_h
                                 nw = rect_coords[2] / img_w
                                 nh = rect_coords[3] / img_h
                                 safe_rect = (nx, ny, nw, nh)
                        
                        # Pass fill_color
                        success, msg = remove_watermark_from_pdf(input_path, output_path, rect=safe_rect, fill_color=fill_color)
                        
                        if success:
                            st.success(f"성공! {msg}")
                            with open(output_path, 'rb') as f:
                                st.download_button('결과 PDF 다운로드', f, file_name=f'fixed_document.pdf')
                        else:
                            st.error(f"실패: {msg}")
                    else:
                        st.error("지원하지 않는 파일 형식입니다.")
