import streamlit as st
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="PDF 날짜 변경기", page_icon="📅", layout="centered")

st.title("📅 PDF 수료증 날짜 일괄 변경기 (절대 좌표 모드)")
st.write("PDF의 특정 위치를 무조건 흰색 박스로 가리고 지정한 날짜를 '굴림체 굵게' 새로 입력합니다.")

# 1. 사용자로부터 변경할 날짜 입력 받기
target_date = st.text_input("변경할 날짜를 입력하세요", value="2026년 07월 20일")

# 2. 파일 업로드 컴포넌트
uploaded_files = st.file_uploader("수정할 PDF 파일들을 선택하세요", type=["pdf"], accept_multiple_files=True)

# 폰트 경로 설정
font_path = "gulim.ttc"
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/gulim.ttc"

if uploaded_files and st.button("🚀 PDF 전체 변환 시작"):
    success_count = 0
    
    for uploaded_file in uploaded_files:
        try:
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            
            # ⭐️ [핵심] 절대 좌표 기준 설정 (픽셀 단위)
            # 기준 해상도: 2480 x 3509
            # 이전 대화에서 잡았던 날짜 부근의 픽셀 좌표를 절대 기준으로 고정합니다.
            img_width = 2480
            img_height = 3509
            
            # 원래 날짜가 있던 대략적인 픽셀 영역
            pixel_x0, pixel_y0 = 1530, 2500
            pixel_x1, pixel_y1 = 2210, 2560
            
            # ⭐️ [보완] 사용자가 요청한 "하단으로 이동" 효과를 절대 좌표에 아예 반영
            # 원래 위치보다 Y축을 아래로 18픽셀(포인트 비율 계산 전 픽셀 환산 적용 약 80px) 더 내려서 잡습니다.
            pixel_y0 += 80
            pixel_y1 += 80

            # PDF 실제 포인트 크기에 맞추기 위한 비율 계산
            pdf_width = page.rect.width
            pdf_height = page.rect.height
            x_scale = pdf_width / img_width
            y_scale = pdf_height / img_height
            
            # 픽셀 좌표 -> PDF 포인트 좌표로 변환하여 사각형 정의
            text_rect = fitz.Rect(
                pixel_x0 * x_scale,
                pixel_y0 * y_scale,
                pixel_x1 * x_scale,
                pixel_y1 * y_scale
            )
            
            # 3. 흰색 네모박스로 해당 영역 무조건 가리기
            page.draw_rect(text_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # 4. 새로운 날짜 입력 설정
            insert_kwargs = {
                "fontsize": 15,
                "color": (0, 0, 0),
                "align": 1,
                "stroke_opacity": 1,
                "fill_opacity": 1,
                "render_mode": 2
            }
            if os.path.exists(font_path if font_path else ""):
                insert_kwargs["fontname"] = "ko-gulim"
                insert_kwargs["fontfile"] = font_path
                
            # 지정된 절대 좌표 상자에 글자 입력
            page.insert_textbox(text_rect, target_date, **insert_kwargs)
            
            output_bytes = doc.tobytes()
            doc.close()
            
            st.success(f"✅ {uploaded_file.name} 변환 성공!")
            st.download_button(
                label=f"📥 [다운로드] {uploaded_file.name}",
                data=output_bytes,
                file_name=f"[수정완료]_{uploaded_file.name}",
                mime="application/pdf",
                key=uploaded_file.name
            )
            success_count += 1
            
        except Exception as e:
            st.error(f"❌ {uploaded_file.name} 처리 중 에러 발생: {e}")
            
    if success_count > 0:
        st.balloons()
