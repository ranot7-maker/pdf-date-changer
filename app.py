import streamlit as st
import fitz  # PyMuPDF
import os
import zipfile
import io

st.set_page_config(page_title="PDF 날짜 변경기", page_icon="📅", layout="centered")

st.title("📅 PDF 수료증 날짜 일괄 변경기")
st.write("'이를 수여합니다.' 문구를 기준으로 하단 날짜를 자동 인식하여 '굴림체 굵게' 새로 입력합니다.")

# 1. 사용자로부터 변경할 날짜 입력 받기
target_date = st.text_input("변경할 날짜를 입력하세요", value="2026년 07월 20일")

# 2. 파일 업로드 컴포넌트
uploaded_files = st.file_uploader("수정할 PDF 파일들을 선택하세요", type=["pdf"], accept_multiple_files=True)

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
                page = doc[0]
                
                # "이를 수여합니다." 고정 문구 위치 찾기
                base_text = "이를 수여합니다."
                base_instances = page.search_for(base_text)
                
                if not base_instances:
                    st.warning(f"⚠️ {uploaded_file.name}: '{base_text}' 문구를 찾지 못해 건너뜁니다.")
                    doc.close()
                    continue
                    
                # "이를 수여합니다."의 좌표 구하기
                base_rect = base_instances[0]
                
                # ⭐️ [위치 조정 핵심 가이드] ⭐️
                # 글씨 위치를 바꾸고 싶다면 여기 두 숫자를 조절하세요!
                # +35: "수여합니다" 글자 밑변에서 아래로 35만큼 떨어진 지점부터 흰 상자가 시작됩니다.
                # +95: "수여합니다" 글자 밑변에서 아래로 95만큼 떨어진 지점까지 흰 상자가 쳐집니다.
                y_top = base_rect.y1 + 80 
                y_bottom = base_rect.y1 + 150
                
                # 가로 영역 (좌우 50씩 넉넉하게 확장)
                x_left = base_rect.x0 + 95
                x_right = base_rect.x1 + 150
                
                # 최종 직사각형 정의
                text_rect = fitz.Rect(x_left, y_top, x_right, y_bottom)
                
                # ⭐️ [에러 해결] 속성 에러가 발생하는 구문을 안전한 표준 검사로 변경 ⭐️
                if text_rect.is_empty:
                    st.error(f"❌ {uploaded_file.name}: 날짜 상자 영역이 비어있습니다.")
                    doc.close()
                    continue

                # 3. 자동 계산된 원래 날짜 위치를 흰색 네모박스로 깔끔하게 지우기
                page.draw_rect(text_rect, color=(1, 1, 1), fill=(1, 1, 1))
                
                # 4. 새로운 날짜 입력 설정 (굴림체 굵게)
                # 가운데(1)보다 약간만 더 오른쪽으로 밀고 싶다면 아래 숫자를 10, 15, 20 등으로 조금씩 바꿔보세요!
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
                    
                # 안전하게 자동 계산된 상자 안에 글자 입력
                page.insert_textbox(rect_text, target_date, **insert_kwargs)
                
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
