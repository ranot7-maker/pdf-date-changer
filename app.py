import streamlit as st
import fitz  # PyMuPDF
import os
import zipfile
import io

st.set_page_config(page_title="PDF 날짜 변경기", page_icon="📅", layout="centered")

st.title("📅 PDF 수료증 날짜 일괄 변경기")
st.write("파일 내의 모든 페이지를 돌며 '이를 수여합니다.' 문구 기준 하단 날짜를 전부 찾아 새로 입력합니다.")

# 1. 사용자로부터 변경할 날짜 입력 받기
target_date = st.text_input("변경할 날짜를 입력하세요", value="2026년 07월 20일")

# 2. 파일 업로드 컴포넌트
uploaded_files = st.file_uploader("수정할 PDF 파일들을 선택하세요 (한 파일 내 여러 페이지 자동 지원)", type=["pdf"], accept_multiple_files=True)

# 폰트 경로 설정
font_path = "gulim.ttc"
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/gulim.ttc"

# 세션 상태 초기화
if "zip_buffer" not in st.session_state:
    st.session_state.zip_buffer = None
if "converted_count" not in st.session_state:
    st.session_state.converted_count = 0

# 파일이 새로 업로드되면 이전 변환 기록 초기화
if not uploaded_files:
    st.session_state.zip_buffer = None
    st.session_state.converted_count = 0

if uploaded_files and st.button("🚀 PDF 전체 변환 시작"):
    zip_buffer = io.BytesIO()
    success_count = 0
    
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for uploaded_file in uploaded_files:
            try:
                file_bytes = uploaded_file.read()
                doc = fitz.open(stream=file_bytes, filetype="pdf")
                
                # ⭐️ [핵심 변경 포인트] 파일 내의 모든 페이지를 순서대로 탐색합니다. ⭐️
                for page_num in range(len(doc)):
                    page = doc[page_num]
                    
                    # "이를 수여합니다." 고정 문구 위치 찾기
                    base_text = "이를 수여합니다."
                    base_instances = page.search_for(base_text)
                    
                    # 만약 이 페이지에 해당 문구가 없다면 (예: 표지나 안내장) 다음 페이지로 패스
                    if not base_instances:
                        continue
                        
                    # "이를 수여합니다."의 좌표 구하기
                    base_rect = base_instances[0]
                    
                    # 잡아두신 황금 좌표 비율 그대로 유지
                    y_top = base_rect.y1 + 80 
                    y_bottom = base_rect.y1 + 150
                    x_left = base_rect.x0 + 95
                    x_right = base_rect.x1 + 150
                    
                    # 1. 기존 날짜 가리는 흰 박스 상자
                    text_rect = fitz.Rect(x_left, y_top, x_right, y_bottom)
                    if text_rect.is_empty:
                        continue
                    page.draw_rect(text_rect, color=(1, 1, 1), fill=(1, 1, 1))
                    
                    # 2. 새로 글씨 쓸 상자 (오른쪽 미세 이동 반영)
                    shift_right = 40
                    rect_text = fitz.Rect(x_left + shift_right, y_top, x_right + shift_right, y_bottom)
                    
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
                        
                    # 글씨 새기기
                    page.insert_textbox(rect_text, target_date, **insert_kwargs)
                
                # 모든 페이지 수정이 끝난 파일 저장
                output_bytes = doc.tobytes()
                doc.close()
                
                # 압축 파일 안에 PDF 추가
                new_filename = f"[수정완료]_{uploaded_file.name}"
                zip_file.writestr(new_filename, output_bytes)
                success_count += 1
                
            except Exception as e:
                st.error(f"❌ {uploaded_file.name} 처리 중 에러 발생: {e}")
                
    if success_count > 0:
        zip_buffer.seek(0)
        st.session_state.zip_buffer = zip_buffer.getvalue()
        st.session_state.converted_count = success_count
        st.balloons()

# 일괄 다운로드 버튼
if st.session_state.zip_buffer is not None:
    st.success(f"🎉 총 {st.session_state.converted_count}개의 파일이 성공적으로 변환되었습니다!")
    
    st.download_button(
        label="📥 변환된 모든 PDF 일괄 다운로드 (ZIP)",
        data=st.session_state.zip_buffer,
        file_name="[수정완료]_PDF_파일목록.zip",
        mime="application/zip",
        use_container_width=True
    )
