import streamlit as st
import tempfile
import os
import cv2
import numpy as np
from PIL import Image
from processor import process_video_with_mask
from document_processor import remove_watermark_from_pdf, get_pdf_preview

st.set_page_config(page_title="Magic Remover All-in-One", page_icon="🪄")

st.title("🪄 매직 워터마크 제거기 (All-in-One)")
st.markdown("동영상과 문서의 워터마크를 손쉽게 제거하세요.")

tab1, tab2 = st.tabs(["🎬 동영상 (Video)", "📄 문서 (PDF)"])

# --- TAB 1: Video Watermark Remover ---
with tab1:
    st.header("동영상 워터마크 제거")

    st.info("💡 워터마크가 있는 영역의 좌표를 입력하세요. 프레임에서 위치를 확인할 수 있습니다.")

    uploaded_file = st.file_uploader("동영상 파일 업로드 (Upload Video)", type=["mp4", "mov", "avi"], key="video_upload")

    if uploaded_file is not None:
        # Save uploaded file to temp directory
        tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
        tfile.write(uploaded_file.read())
        video_path = tfile.name

        # Video extraction for preview
        vid_cap = cv2.VideoCapture(video_path)
        total_frames = int(vid_cap.get(cv2.CAP_PROP_FRAME_COUNT))
        video_width = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        video_height = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        st.caption(f"📹 비디오 정보: {video_width}x{video_height}, 총 {total_frames} 프레임")

        # Frame selection
        frame_index = st.slider("프레임 선택 (워터마크 확인용)", 0, total_frames-1, 0, key="video_frame_slider")
        vid_cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = vid_cap.read()

        if ret and frame is not None:
            # Convert Frame (BGR) to RGB for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            pil_image = Image.fromarray(frame_rgb)

            # Display frame with coordinates overlay
            st.image(pil_image, caption=f"프레임 {frame_index}", use_container_width=True)

            st.markdown("### 워터마크 영역 설정")
            st.markdown("아래에 워터마크가 있는 사각형 영역의 좌표를 입력하세요.")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                x_start = st.number_input("X 시작", min_value=0, max_value=video_width, value=0, key="x_start")
            with col2:
                y_start = st.number_input("Y 시작", min_value=0, max_value=video_height, value=0, key="y_start")
            with col3:
                x_end = st.number_input("X 끝", min_value=0, max_value=video_width, value=min(200, video_width), key="x_end")
            with col4:
                y_end = st.number_input("Y 끝", min_value=0, max_value=video_height, value=min(100, video_height), key="y_end")

            # Preview rectangle on frame
            if x_end > x_start and y_end > y_start:
                preview_frame = frame_rgb.copy()
                cv2.rectangle(preview_frame, (x_start, y_start), (x_end, y_end), (255, 0, 0), 2)
                st.image(preview_frame, caption="미리보기: 빨간 사각형이 제거될 영역", use_container_width=True)

                st.success(f"✅ 선택된 영역: {x_end-x_start}x{y_end-y_start} 픽셀")
            else:
                st.warning("⚠️ 올바른 좌표를 입력하세요 (끝 좌표 > 시작 좌표)")

            if st.button("🎬 동영상 워터마크 제거 시작", key="video_process_btn", type="primary"):
                if x_end > x_start and y_end > y_start:
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    status_text.text("준비 중...")

                    def update_progress(p):
                        progress_int = int(p * 100)
                        progress_bar.progress(min(progress_int, 100))
                        status_text.text(f"처리 중... {progress_int}% 완료")

                    # Create mask from coordinates
                    mask = np.zeros((video_height, video_width), dtype=np.uint8)
                    mask[y_start:y_end, x_start:x_end] = 255

                    output_file = tempfile.NamedTemporaryFile(delete=False, suffix='_fixed.mp4')
                    output_path = output_file.name
                    output_file.close()

                    success, message = process_video_with_mask(video_path, output_path, mask, progress_callback=update_progress)

                    if success:
                        progress_bar.progress(100)
                        status_text.text("작업 완료!")
                        st.success("✅ 워터마크 제거 완료!")
                        st.video(output_path)
                        with open(output_path, 'rb') as f:
                            st.download_button('📥 결과 동영상 다운로드', f, file_name='fixed_video.mp4')
                    else:
                        st.error(f"❌ 오류: {message}")
                else:
                    st.warning("⚠️ 먼저 올바른 워터마크 영역을 설정해주세요.")

        vid_cap.release()

# --- TAB 2: PDF Watermark Remover ---
with tab2:
    st.header("📄 PDF 워터마크 제거")
    st.markdown("""
    **사용 가이드**:
    1. PDF 파일을 업로드하세요
    2. 첫 페이지에서 워터마크 위치를 확인하세요
    3. 워터마크 영역의 좌표를 입력하세요
    4. '제거 시작'을 누르면 모든 페이지의 해당 위치가 지워집니다
    """)

    pdf_file = st.file_uploader("PDF 파일 업로드", type=["pdf"], key="pdf_upload")

    if pdf_file:
        # Save temp input first to generate preview
        input_tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
        input_tfile.write(pdf_file.read())
        input_path = input_tfile.name
        input_tfile.close()

        # Get Preview of Page 0
        pil_image, error_msg = get_pdf_preview(input_path, 0)

        if error_msg:
            st.error(error_msg)
        elif pil_image:
            img_w, img_h = pil_image.size
            st.caption(f"📄 PDF 크기: {img_w}x{img_h} 픽셀")

            st.image(pil_image, caption="첫 페이지 미리보기", use_container_width=True)

            st.markdown("### 워터마크 영역 설정")

            col1, col2, col3, col4 = st.columns(4)
            with col1:
                pdf_x_start = st.number_input("X 시작", min_value=0, max_value=img_w, value=0, key="pdf_x_start")
            with col2:
                pdf_y_start = st.number_input("Y 시작", min_value=0, max_value=img_h, value=0, key="pdf_y_start")
            with col3:
                pdf_x_end = st.number_input("X 끝", min_value=0, max_value=img_w, value=min(200, img_w), key="pdf_x_end")
            with col4:
                pdf_y_end = st.number_input("Y 끝", min_value=0, max_value=img_h, value=min(100, img_h), key="pdf_y_end")

            # Preview rectangle
            if pdf_x_end > pdf_x_start and pdf_y_end > pdf_y_start:
                preview_img = np.array(pil_image)
                cv2.rectangle(preview_img, (pdf_x_start, pdf_y_start), (pdf_x_end, pdf_y_end), (255, 0, 0), 3)
                st.image(preview_img, caption="미리보기: 빨간 사각형이 제거될 영역", use_container_width=True)

                st.success(f"✅ 선택된 영역: {pdf_x_end-pdf_x_start}x{pdf_y_end-pdf_y_start} 픽셀")
            else:
                st.warning("⚠️ 올바른 좌표를 입력하세요")

            if st.button("📄 워터마크 제거 시작", key="pdf_process_btn", type="primary"):
                if pdf_x_end > pdf_x_start and pdf_y_end > pdf_y_start:
                    with st.spinner("PDF 처리 중..."):
                        # Convert to normalized coordinates
                        nx = pdf_x_start / img_w
                        ny = pdf_y_start / img_h
                        nw = (pdf_x_end - pdf_x_start) / img_w
                        nh = (pdf_y_end - pdf_y_start) / img_h
                        rect_coords = (nx, ny, nw, nh)

                        output_path = input_path.replace('.pdf', '_fixed.pdf')
                        if output_path == input_path:
                            output_path = tempfile.NamedTemporaryFile(delete=False, suffix='_fixed.pdf').name

                        success, msg = remove_watermark_from_pdf(
                            input_path,
                            output_path,
                            rect=rect_coords,
                            fill_color="auto"
                        )

                        if success:
                            st.success(f"✅ {msg}")
                            with open(output_path, 'rb') as f:
                                st.download_button('📥 결과 PDF 다운로드', f, file_name='fixed_document.pdf')
                        else:
                            st.error(f"❌ 실패: {msg}")
                else:
                    st.warning("⚠️ 먼저 올바른 워터마크 영역을 설정해주세요.")

st.markdown("---")
st.caption("💡 팁: 좌표 입력이 어려우면 ngrok으로 로컬에서 실행하세요. 로컬에서는 마우스로 그릴 수 있습니다!")
