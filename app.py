import gradio as gr
import tempfile
import os
import cv2
import numpy as np
from PIL import Image
from processor import process_video_with_mask
from document_processor import remove_watermark_from_pdf, get_pdf_preview


# =====================
# Video Tab Functions
# =====================

def get_video_info(video_path):
    """동영상 업로드 시 정보와 첫 프레임 반환"""
    if video_path is None:
        return None, "", 0, 0, 0, 0, gr.Slider(maximum=0, value=0)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None, "프레임을 읽을 수 없습니다.", 0, 0, 0, 0, gr.Slider(maximum=0, value=0)

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    info_text = f"📹 비디오 정보: {width}x{height}, 총 {total_frames} 프레임"

    return (
        frame_rgb,
        info_text,
        width,
        height,
        1101,  # default x_start
        660,   # default y_start
        gr.Slider(maximum=max(total_frames - 1, 0), value=0),
    )


def update_frame_preview(video_path, frame_index, x_start, y_start, x_end, y_end):
    """프레임 슬라이더 변경 시 미리보기 업데이트"""
    if video_path is None:
        return None

    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_FRAMES, int(frame_index))
    ret, frame = cap.read()
    cap.release()

    if not ret or frame is None:
        return None

    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    preview = frame_rgb.copy()
    cv2.rectangle(preview, (int(x_start), int(y_start)), (int(x_end), int(y_end)), (255, 0, 0), 3)
    return preview


def process_video(video_path, x_start, y_start, x_end, y_end, progress=gr.Progress()):
    """동영상 워터마크 제거 실행"""
    if video_path is None:
        return "동영상을 먼저 업로드하세요.", None, gr.DownloadButton(visible=False)

    cap = cv2.VideoCapture(video_path)
    video_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    video_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    cap.release()

    x_start, y_start, x_end, y_end = int(x_start), int(y_start), int(x_end), int(y_end)

    mask = np.zeros((video_h, video_w), dtype=np.uint8)
    mask[y_start:y_end, x_start:x_end] = 255

    # 원본 파일명 기반 출력 파일명 생성
    original_name = os.path.splitext(os.path.basename(video_path))[0]
    output_dir = tempfile.mkdtemp()
    output_path = os.path.join(output_dir, f"{original_name}_fixed.mp4")

    def update_progress(p):
        progress(p, desc=f"처리 중... {int(p * 100)}%")

    success, message = process_video_with_mask(video_path, output_path, mask, progress_callback=update_progress)

    if success:
        download_name = f"{original_name}_fixed.mp4"
        return "✅ 워터마크 제거 완료!", output_path, gr.DownloadButton(value=output_path, label=f"📥 {download_name} 다운로드", visible=True)
    else:
        return f"❌ 오류: {message}", None, gr.DownloadButton(visible=False)


# =====================
# PDF Tab Functions
# =====================

def _resolve_pdf_path(pdf_path):
    """gr.File에서 실제 파일 경로 추출"""
    if pdf_path is None:
        return None
    if hasattr(pdf_path, "name"):
        return pdf_path.name
    return str(pdf_path)


def get_pdf_info(pdf_path, x_start, y_start, x_end, y_end):
    """PDF 업로드 시 빨간 사각형 포함 미리보기 반환"""
    path = _resolve_pdf_path(pdf_path)
    if path is None:
        return None, "", 0, 0

    pil_image, error_msg = get_pdf_preview(path, 0)

    if error_msg:
        return None, error_msg, 0, 0

    img_w, img_h = pil_image.size
    info_text = f"📄 PDF 크기: {img_w}x{img_h} 픽셀"

    preview = np.array(pil_image)
    cv2.rectangle(preview, (int(x_start), int(y_start)), (int(x_end), int(y_end)), (255, 0, 0), 3)
    return preview, info_text, img_w, img_h


def update_pdf_preview(pdf_path, x_start, y_start, x_end, y_end):
    """PDF 좌표 변경 시 미리보기 업데이트"""
    path = _resolve_pdf_path(pdf_path)
    if path is None:
        return None

    pil_image, error_msg = get_pdf_preview(path, 0)
    if error_msg or pil_image is None:
        return None

    preview = np.array(pil_image)
    cv2.rectangle(preview, (int(x_start), int(y_start)), (int(x_end), int(y_end)), (255, 0, 0), 3)
    return preview


def process_pdf(pdf_path, x_start, y_start, x_end, y_end):
    """PDF 워터마크 제거 실행"""
    path = _resolve_pdf_path(pdf_path)
    if path is None:
        return "PDF를 먼저 업로드하세요.", gr.DownloadButton(visible=False)

    pil_image, _ = get_pdf_preview(path, 0)
    if pil_image is None:
        return "PDF 미리보기 생성 실패", gr.DownloadButton(visible=False)

    img_w, img_h = pil_image.size
    x_start, y_start, x_end, y_end = int(x_start), int(y_start), int(x_end), int(y_end)

    nx = x_start / img_w
    ny = y_start / img_h
    nw = (x_end - x_start) / img_w
    nh = (y_end - y_start) / img_h
    rect_coords = (nx, ny, nw, nh)

    # 원본 파일명 기반 출력 파일명 생성
    original_name = os.path.splitext(os.path.basename(path))[0]
    output_dir = tempfile.mkdtemp()
    output_path = os.path.join(output_dir, f"{original_name}_fixed.pdf")

    success, msg = remove_watermark_from_pdf(path, output_path, rect=rect_coords, fill_color="auto")

    if success:
        download_name = f"{original_name}_fixed.pdf"
        return f"✅ {msg}", gr.DownloadButton(value=output_path, label=f"📥 {download_name} 다운로드", visible=True)
    else:
        return f"❌ 실패: {msg}", gr.DownloadButton(visible=False)


# =====================
# Build Gradio UI
# =====================

with gr.Blocks(title="Magic Remover", theme=gr.themes.Soft()) as demo:
    gr.Markdown("# 🪄 매직 워터마크 제거기 (All-in-One)")
    gr.Markdown("동영상과 문서의 워터마크를 손쉽게 제거하세요.")

    with gr.Tabs():
        # --- Video Tab ---
        with gr.TabItem("🎬 동영상 (Video)"):
            gr.Markdown("## 동영상 워터마크 제거")
            gr.Markdown("💡 기본값으로 오른쪽 하단 로고 좌표가 설정됩니다. 필요시 수정 가능합니다!")

            video_input = gr.Video(label="동영상 파일 업로드 (Upload Video)")
            video_info = gr.Textbox(label="비디오 정보", interactive=False)

            # Hidden state for video dimensions
            vid_width = gr.State(0)
            vid_height = gr.State(0)

            frame_slider = gr.Slider(label="프레임 선택 (워터마크 확인용)", minimum=0, maximum=0, step=1, value=0)
            frame_preview = gr.Image(label="미리보기 (빨간 사각형 = 제거 영역)")

            gr.Markdown("### 워터마크 영역 설정")
            gr.Markdown("좌표를 입력하세요. (0,0)은 좌측 상단입니다.")

            with gr.Row():
                vid_x_start = gr.Number(label="X 시작", value=1101, precision=0)
                vid_y_start = gr.Number(label="Y 시작", value=660, precision=0)
                vid_x_end = gr.Number(label="X 끝", value=1238, precision=0)
                vid_y_end = gr.Number(label="Y 끝", value=681, precision=0)

            video_btn = gr.Button("🎬 동영상 워터마크 제거 시작", variant="primary")
            video_status = gr.Textbox(label="상태", interactive=False)
            video_output = gr.Video(label="결과 미리보기")
            video_download = gr.DownloadButton("📥 결과 동영상 다운로드", visible=False, variant="secondary")

            # Events - video upload
            video_input.change(
                fn=get_video_info,
                inputs=[video_input],
                outputs=[frame_preview, video_info, vid_width, vid_height, vid_x_start, vid_y_start, frame_slider],
            )

            # Events - frame slider & coordinate changes
            for coord_input in [frame_slider, vid_x_start, vid_y_start, vid_x_end, vid_y_end]:
                coord_input.change(
                    fn=update_frame_preview,
                    inputs=[video_input, frame_slider, vid_x_start, vid_y_start, vid_x_end, vid_y_end],
                    outputs=[frame_preview],
                )

            # Events - process button
            video_btn.click(
                fn=process_video,
                inputs=[video_input, vid_x_start, vid_y_start, vid_x_end, vid_y_end],
                outputs=[video_status, video_output, video_download],
            )

        # --- PDF Tab ---
        with gr.TabItem("📄 문서 (PDF)"):
            gr.Markdown("## 📄 PDF 워터마크 제거")
            gr.Markdown(
                "**사용 가이드**: PDF 업로드 → 워터마크 좌표 입력 → 제거 시작"
            )

            pdf_input = gr.File(label="PDF 파일 업로드", file_types=[".pdf"])
            pdf_info = gr.Textbox(label="PDF 정보", interactive=False)

            pdf_img_w = gr.State(0)
            pdf_img_h = gr.State(0)

            pdf_preview = gr.Image(label="미리보기 (빨간 사각형 = 제거 영역)")

            gr.Markdown("### 워터마크 영역 설정")
            gr.Markdown("좌표를 입력하세요. (0,0)은 좌측 상단입니다.")

            with gr.Row():
                pdf_x_start = gr.Number(label="X 시작", value=1265, precision=0)
                pdf_y_start = gr.Number(label="Y 시작", value=745, precision=0)
                pdf_x_end = gr.Number(label="X 끝", value=1369, precision=0)
                pdf_y_end = gr.Number(label="Y 끝", value=762, precision=0)

            pdf_btn = gr.Button("📄 워터마크 제거 시작", variant="primary")
            pdf_status = gr.Textbox(label="상태", interactive=False)
            pdf_output = gr.DownloadButton("📥 결과 PDF 다운로드", visible=False, variant="secondary")

            # Events - PDF upload
            pdf_input.change(
                fn=get_pdf_info,
                inputs=[pdf_input, pdf_x_start, pdf_y_start, pdf_x_end, pdf_y_end],
                outputs=[pdf_preview, pdf_info, pdf_img_w, pdf_img_h],
            )

            # Events - coordinate changes
            for coord_input in [pdf_x_start, pdf_y_start, pdf_x_end, pdf_y_end]:
                coord_input.change(
                    fn=update_pdf_preview,
                    inputs=[pdf_input, pdf_x_start, pdf_y_start, pdf_x_end, pdf_y_end],
                    outputs=[pdf_preview],
                )

            # Events - process button
            pdf_btn.click(
                fn=process_pdf,
                inputs=[pdf_input, pdf_x_start, pdf_y_start, pdf_x_end, pdf_y_end],
                outputs=[pdf_status, pdf_output],
            )

    gr.Markdown("---")
    gr.Markdown("💡 팁: 좌표는 수정 가능합니다. 미리보기에서 빨간 사각형 위치를 확인하세요!")

if __name__ == "__main__":
    demo.launch()
