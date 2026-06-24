import streamlit as st
import fitz  # PyMuPDF
import os

st.set_page_config(page_title="PDF 날짜 변경기", page_icon="📅", layout="centered")

st.title("📅 PDF 수료증 날짜 일괄 변경기")
st.write("PDF 파일을 업로드하면 원래 있던 날짜를 가리고 지정한 날짜를 '굴림체 굵게' 아래쪽에 새로 입력해 줍니다.")

# 1. 사용자로부터 변경할 날짜 입력 받기
target_date = st.text_input("변경할 날짜를 입력하세요", value="2026년 07월 20일")

# 2. 파일 업로드 컴포넌트 (여러 파일 동시 업로드 가능)
uploaded_files = st.file_uploader("수정할 PDF 파일들을 선택하세요", type=["pdf"], accept_multiple_files=True)

# 윈도우 시스템 폰트가 없는 리눅스 서버 환경(배포 환경)을 위해 
# app.py 내의 폰트 경로 체크 부분을 아래와 같이 수정
font_path = "gulim.ttc"  # 깃허브에 같이 올린 폰트 파일을 우선 참조
if not os.path.exists(font_path):
    font_path = "C:/Windows/Fonts/gulim.ttc"  # 로컬 테스트용 백업
    font_path = None 

if uploaded_files and st.button("🚀 PDF 전체 변환 시작"):
    success_count = 0
    
    for uploaded_file in uploaded_files:
        try:
            # 업로드된 파일을 메모리 상에서 PDF로 열기
            file_bytes = uploaded_file.read()
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            page = doc[0]
            
            # 원본 PDF에서 바꿀 대상 텍스트 위치 찾기
            target_text = "2026년 06월 19일"
            text_instances = page.search_for(target_text)
            
            if not text_instances:
                st.warning(f"⚠️ {uploaded_file.name}: '{target_text}' 문구를 찾지 못해 건너뜁니다.")
                doc.close()
                continue
                
            original_rect = text_instances[0]
            
            # 흰색 네모박스로 가리기
            page.draw_rect(original_rect, color=(1, 1, 1), fill=(1, 1, 1))
            
            # Y축 하단 이동 (이전 설정값 18)
            shift_down = 18  
            text_rect = fitz.Rect(
                original_rect.x0 - 15,
                original_rect.y0 - 20 + shift_down,
                original_rect.x1 + 15,
                original_rect.y1 + 25 + shift_down
            )
            
            # 새로운 날짜 입력 (폰트 경로가 유효할 때만 지정)
            insert_kwargs = {
                "rect": text_rect,
                "text": target_date,
                "fontsize": 15,
                "color": (0, 0, 0),
                "align": 1,
                "stroke_opacity": 1,
                "fill_opacity": 1,
                "render_mode": 2
            }
            if font_path:
                insert_kwargs["fontname"] = "ko-gulim"
                insert_kwargs["fontfile"] = font_path
                
            page.insert_textbox(**insert_kwargs)
            
            # 변환된 PDF를 바이트 데이터로 저장
            output_bytes = doc.tobytes()
            doc.close()
            
            # 웹 화면에 개별 다운로드 버튼 생성
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
        st.balloons() # 축하 효과 애니메이션 표시
