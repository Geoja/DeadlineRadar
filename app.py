import streamlit as st
import pandas as pd
import pypdf
import google.generativeai as genai
import json
import datetime
import re
import calendar

# 1. Page Configuration & Custom CSS Injection
st.set_page_config(
    page_title="DeadlineRadar",
    page_icon="📅",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom premium styling with HSL colors and glassmorphism
st.markdown("""
<style>
    /* Main container background */
    .stApp {
        background: radial-gradient(circle at top left, #1a1b24, #0f1016);
        color: #e2e8f0;
    }
    
    /* Headers styling */
    h1, h2, h3, h4 {
        color: #f8fafc !important;
        font-family: 'Outfit', 'Inter', sans-serif;
        font-weight: 700;
        letter-spacing: -0.02em;
    }
    
    /* Glassmorphic Cards */
    .card {
        background: rgba(30, 41, 59, 0.45);
        backdrop-filter: blur(12px);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    
    .card:hover {
        border-color: rgba(99, 102, 241, 0.4);
        transform: translateY(-2px);
    }
    
    /* D-Day badge styles */
    .dday-badge {
        font-size: 0.85rem;
        font-weight: 700;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-right: 8px;
    }
    
    .dday-red {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
        border: 1px solid rgba(239, 68, 68, 0.4);
    }
    
    .dday-orange {
        background-color: rgba(245, 158, 11, 0.2);
        color: #fbbf24;
        border: 1px solid rgba(245, 158, 11, 0.4);
    }
    
    .dday-green {
        background-color: rgba(16, 185, 129, 0.2);
        color: #34d399;
        border: 1px solid rgba(16, 185, 129, 0.4);
    }
    
    .dday-gray {
        background-color: rgba(148, 163, 184, 0.15);
        color: #cbd5e1;
        border: 1px solid rgba(148, 163, 184, 0.3);
    }
    
    /* Clean custom alert banners */
    .alert-box {
        background: rgba(99, 102, 241, 0.15);
        border-left: 5px solid #6366f1;
        border-radius: 8px;
        padding: 15px;
        margin: 15px 0;
        color: #e2e8f0;
    }
</style>
""", unsafe_allow_html=True)

# 2. Helper Functions

def extract_text_from_pdf(pdf_file) -> str:
    """Extracts raw text from an uploaded PDF file."""
    try:
        reader = pypdf.PdfReader(pdf_file)
        text = ""
        for i, page in enumerate(reader.pages):
            page_text = page.extract_text()
            if page_text:
                text += f"\n--- PAGE {i+1} ---\n{page_text}"
        return text
    except Exception as e:
        st.error(f"PDF 텍스트 추출 중 오류가 발생했습니다: {e}")
        return ""

def call_gemini_to_extract_tasks(api_key: str, syllabus_text: str, model_name: str = "gemini-3.5-flash"):
    """Sends syllabus text to Gemini and parses the output JSON."""
    try:
        genai.configure(api_key=api_key)
        
        # System instructions optimized for parsing syllabus deadlines and exams
        prompt = f"""
전달된 대학교 강의계획서(Syllabus) 텍스트를 분석하여, 평가 항목(과제, 프로젝트, 중간고사/기말고사/시험, 토론, 퀴즈 등)의 마감 기한과 일정을 추출해주세요.

다음 규칙을 반드시 지켜주세요:
1. 각 과제 및 시험별로 '과목명(course)', '과제/시험명(task_name)', '마감일(due_date)', '세부설명(description)'을 추출해야 합니다.
2. 'due_date'는 반드시 'YYYY-MM-DD' 형식의 문자열이어야 합니다.
3. 만약 구체적인 날짜 대신 '14주차 제출', '15주차 시험' 등 주차만 나와 있는 경우, 2026학년도 1학기 개강일인 2026년 3월 2일(월요일)을 1주차 첫 날로 가정하여 날짜를 계산해주세요.
   - 예: 1주차(3/2~), 2주차(3/9~), 3주차(3/16~), 4주차(3/23~), 5주차(3/30~), 6주차(4/6~), 7주차(4/13~), 8주차(중간고사 주간: 4/20~), 9주차(4/27~), 10주차(5/4~), 11주차(5/11~), 12주차(5/18~), 13주차(5/25~), 14주차(6/1~), 15주차(6/8~), 16주차(기말고사 주간: 6/15~)
   - 주차 표기 시 마감 요일은 별도 명시가 없으면 해당 주차의 '일요일'로 설정합니다. 단, '중간고사'나 '기말고사' 등 시험 항목은 해당 주차의 '월요일~금요일' 중 타당한 시험 주간 일정으로 설정할 수 있습니다.
4. 반드시 valid한 JSON 배열 형태로만 답변해야 합니다. 마크업(```json ...)이나 불필요한 서문, 주석은 일절 포함하지 마세요.

형식 예시:
[
  {{
    "course": "SW프로그래밍의기초",
    "task_name": "중간고사 필기시험",
    "due_date": "2026-04-20",
    "description": "중간고사 대면 평가 (1주차~7주차 강의 범위)"
  }}
]

--- 강의계획서 텍스트 시작 ---
{syllabus_text}
--- 강의계획서 텍스트 끝 ---
"""
        
        model = genai.GenerativeModel(model_name)
        
        # Guarantee JSON response using config (supported in Gemini 1.5, 2.0, 2.5, 3.x and latest models)
        generation_config = {"response_mime_type": "application/json"}
            
        response = model.generate_content(
            prompt,
            generation_config=generation_config
        )
        
        # Clean any potential enclosing code blocks if output filter fails (fallback)
        raw_json = response.text.strip()
        if raw_json.startswith("```"):
            raw_json = re.sub(r"^```(?:json)?\n", "", raw_json)
            raw_json = re.sub(r"\n```$", "", raw_json)
            
        data = json.loads(raw_json)
        return data
    except Exception as e:
        try:
            available_models = [m.name for m in genai.list_models() if "generateContent" in m.supported_generation_methods]
            st.error(f"Gemini API 호출 중 오류가 발생했습니다: {e}\n\n**현재 API Key로 지원되는 모델 목록:**\n{available_models}")
        except Exception as list_err:
            st.error(f"Gemini API 호출 중 오류가 발생했습니다: {e} (지원 모델 리스트 확인 실패: {list_err})")
        return None

def generate_ics(tasks_list) -> str:
    """Generates standard iCalendar (.ics) string from tasks list."""
    ics_lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//DeadlineRadar//NONSGML v1.0//EN",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH"
    ]
    for task in tasks_list:
        due_date_str = str(task.get("due_date", "")).strip()
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", due_date_str):
            continue
            
        date_formatted = due_date_str.replace("-", "")
        
        course = task.get("course", "기타")
        task_name = task.get("task_name", "과제")
        description = task.get("description", "")
        
        try:
            start_dt = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
            end_dt = start_dt + datetime.timedelta(days=1)
            end_dt_str = end_dt.strftime("%Y%m%d")
        except Exception:
            continue
            
        ics_lines.extend([
            "BEGIN:VEVENT",
            f"SUMMARY:[{course}] {task_name}",
            f"DTSTART;VALUE=DATE:{date_formatted}",
            f"DTEND;VALUE=DATE:{end_dt_str}",
            f"DESCRIPTION:{description}",
            "STATUS:CONFIRMED",
            "SEQUENCE:0",
            "END:VEVENT"
        ])
        
    ics_lines.append("END:VCALENDAR")
    return "\r\n".join(ics_lines)

def get_dday_html(due_date_str: str) -> tuple[str, int]:
    """Calculates D-Day and returns styled HTML badge and days left."""
    try:
        today = datetime.date.today()
        due_date = datetime.datetime.strptime(due_date_str, "%Y-%m-%d").date()
        diff = (due_date - today).days
        
        if diff == 0:
            return '<span class="dday-badge dday-red">D-Day</span>', diff
        elif diff < 0:
            return f'<span class="dday-badge dday-gray">마감완료 (D{-diff})</span>', diff
        elif diff <= 3:
            return f'<span class="dday-badge dday-red">D-{diff}</span>', diff
        elif diff <= 7:
            return f'<span class="dday-badge dday-orange">D-{diff}</span>', diff
        else:
            return f'<span class="dday-badge dday-green">D-{diff}</span>', diff
    except Exception:
        return '<span class="dday-badge dday-gray">기한 없음</span>', 9999

def draw_html_calendar(tasks_list, year, month) -> str:
    """Generates visual HTML/CSS monthly calendar grid representing academic deadlines and exams."""
    # Set Sunday as first day of the week
    calendar.setfirstweekday(calendar.SUNDAY)
    month_matrix = calendar.monthcalendar(year, month)
    
    # Filter and map tasks to specific days of this year and month
    day_tasks = {}
    for task in tasks_list:
        due_str = str(task.get("due_date", "")).strip()
        if re.match(r"^\d{4}-\d{2}-\d{2}$", due_str):
            try:
                dt = datetime.datetime.strptime(due_str, "%Y-%m-%d").date()
                if dt.year == year and dt.month == month:
                    day_tasks.setdefault(dt.day, []).append(task)
            except Exception:
                continue
                
    # Generate distinct HSL colors for courses dynamically
    courses = list(set(task.get("course", "기타") for task in tasks_list if task.get("course")))
    color_map = {}
    for idx, c in enumerate(courses):
        hue = (idx * 137) % 360  # Golden ratio distribution
        color_map[c] = f"hsl({hue}, 60%, 42%)"
        
    html = f"""
    <div style="background: rgba(30, 41, 59, 0.25); border: 1px solid rgba(255, 255, 255, 0.08); border-radius: 16px; padding: 15px; margin-top: 15px; box-shadow: 0 4px 24px rgba(0,0,0,0.15); font-family: 'Outfit', sans-serif;">
        <!-- Calendar Grid -->
        <div style="display: grid; grid-template-columns: repeat(7, 1fr); gap: 6px; text-align: center;">
            <!-- Week Headers -->
            <div style="color: #f87171; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">일</div>
            <div style="color: #cbd5e1; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">월</div>
            <div style="color: #cbd5e1; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">화</div>
            <div style="color: #cbd5e1; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">수</div>
            <div style="color: #cbd5e1; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">목</div>
            <div style="color: #cbd5e1; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">금</div>
            <div style="color: #60a5fa; font-weight: 700; padding: 6px 0; border-bottom: 2px solid rgba(255, 255, 255, 0.1); font-size: 0.85rem;">토</div>
    """
    
    today = datetime.date.today()
    for week in month_matrix:
        for i, day in enumerate(week):
            if day == 0:
                # Empty cell outside the month
                html += '<div style="background: rgba(0, 0, 0, 0.12); border: 1px solid rgba(255, 255, 255, 0.03); border-radius: 8px; min-height: 110px; max-height: 110px;"></div>'
            else:
                is_today = (today.year == year and today.month == month and today.day == day)
                cell_style = "background: rgba(30, 41, 59, 0.3); border: 1px solid rgba(255, 255, 255, 0.06); border-radius: 8px; min-height: 110px; max-height: 110px; padding: 6px; display: flex; flex-direction: column; position: relative; overflow: hidden;"
                if is_today:
                    cell_style += "background: rgba(99, 102, 241, 0.12); box-shadow: inset 0 0 10px rgba(99, 102, 241, 0.25); border-color: rgba(99, 102, 241, 0.4);"
                
                day_color = "#f1f5f9"
                if i == 0:  # Sunday
                    day_color = "#f87171"
                elif i == 6:  # Saturday
                    day_color = "#60a5fa"
                
                html += f'<div style="{cell_style}">'
                
                # Day Label
                label_style = f"font-weight: 700; font-size: 0.85rem; color: {day_color}; margin-bottom: 4px; text-align: left; display: inline-block;"
                if is_today:
                    label_style += "background: #6366f1; color: white; border-radius: 50%; width: 18px; height: 18px; line-height: 18px; text-align: center; font-size: 0.75rem;"
                
                html += f'<div><span style="{label_style}">{day}</span></div>'
                
                # Render tasks inside this day cell
                if day in day_tasks:
                    # Scrollable tasks container with custom scrollbar hiding/styling
                    html += """
                    <div style="display: flex; flex-direction: column; gap: 4px; overflow-y: auto; flex-grow: 1; padding-right: 2px;
                                scrollbar-width: thin; scrollbar-color: rgba(255,255,255,0.15) transparent;">
                    """
                    for task in day_tasks[day]:
                        c_name = task.get("course", "기타")
                        color = color_map.get(c_name, "#6366f1")
                        title = task.get("task_name", "과제")
                        full_desc = task.get("description", "")
                        
                        # Identify exams (중간고사 / 기말고사 / 시험 / 고사) and style them specifically
                        is_exam = any(k in title for k in ["시험", "고사", "Exam", "Test", "Quiz", "중간", "기말"])
                        
                        border_style = "none"
                        font_weight = "500"
                        prefix = ""
                        if is_exam:
                            border_style = "1px solid #ef4444"
                            font_weight = "700"
                            prefix = "🚨 "
                            color = "rgba(239, 68, 68, 0.15)"  # Red background accent
                            
                        short_title = title if len(title) <= 12 else title[:10] + "..."
                        tooltip_text = f"[{c_name}] {title}\\n설명: {full_desc}" if full_desc else f"[{c_name}] {title}"
                        tooltip_text = tooltip_text.replace('"', '&quot;').replace("'", "&apos;")
                        
                        text_color = "#f87171" if is_exam else "white"
                        
                        html += f"""
                        <div style="background: {color}; border: {border_style}; color: {text_color}; font-size: 0.7rem; padding: 2px 4px; border-radius: 4px; text-align: left; font-weight: {font_weight}; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; cursor: pointer;" title="{tooltip_text}">
                            {prefix}{short_title}
                        </div>
                        """
                    html += '</div>'
                html += '</div>'
                
    html += """
        </div>
    </div>
    """
    return html

# 3. Session State Initialization
if "tasks" not in st.session_state:
    st.session_state.tasks = []

if "view_year" not in st.session_state or "view_month" not in st.session_state:
    st.session_state.view_year = datetime.date.today().year
    st.session_state.view_month = datetime.date.today().month

# Mock Demo Data
demo_data = [
    {
        "course": "SW프로그래밍의기초",
        "task_name": "PRD 과제 제출",
        "due_date": "2026-05-18",
        "description": "과제마감기한자동정리 프로그램 계획서(PRD) 작성 및 PDF 제출"
    },
    {
        "course": "SW프로그래밍의기초",
        "task_name": "기말 바이브코딩 실습 과제 제출",
        "due_date": "2026-06-21",
        "description": "antigravity 또는 타 도구를 이용한 바이브코딩 결과물 깃허브 링크 제출 (기말고사 대체)"
    },
    {
        "course": "자료구조",
        "task_name": "중간 프로젝트 과제",
        "due_date": "2026-04-20",
        "description": "BST 및 Red-Black Tree 알고리즘 분석 및 구현 코드 제출"
    },
    {
        "course": "자료구조",
        "task_name": "기말고사 시험",
        "due_date": "2026-06-16",
        "description": "기말 대면 필기 평가 (그래프 알고리즘, 해시테이블 범위)"
    },
    {
        "course": "인공지능개론",
        "task_name": "기말 팀 프로젝트 최종 발표",
        "due_date": "2026-06-12",
        "description": "머신러닝/딥러닝을 활용한 자유 주제 분류기 모델 발표 및 PPT 제출"
    }
]

# 4. UI Layout - Sidebar
with st.sidebar:
    st.image("https://img.icons8.com/color/96/calendar--v1.png", width=70)
    st.title("DeadlineRadar 설정")
    st.markdown("---")
    
    # API Key Configuration
    st.subheader("🔑 Gemini API 설정")
    api_key_input = st.text_input("Gemini API Key 입력", type="password", help="Google AI Studio에서 발급받은 API Key를 입력하세요.")
    
    # Model Selection
    model_option = st.selectbox(
        "🤖 사용할 AI 모델 선택",
        ["gemini-3.5-flash", "gemini-2.5-flash", "gemini-2.0-flash", "gemini-flash-latest", "gemini-pro-latest"],
        index=0,
        help="기본값인 gemini-3.5-flash가 가장 권장되며 빠르고 정확합니다. 오류 발생 시 다른 최신 모델을 선택해 보세요."
    )
    
    st.markdown("""
    **💡 무료 API Key 발급 방법**
    1. [Google AI Studio](https://aistudio.google.com/)에 접속
    2. 로그인 후 **Create API Key** 클릭
    3. 발급받은 키를 여기에 복사&붙여넣기
    """)
    
    st.markdown("---")
    
    # Demo Activation
    st.subheader("🧪 테스트용 데모 모드")
    if st.button("✨ 데모 데이터 로드", use_container_width=True):
        st.session_state.tasks = demo_data.copy()
        st.success("데모 데이터가 성공적으로 로드되었습니다!")
        st.rerun()
        
    if st.button("🗑️ 전체 데이터 초기화", use_container_width=True, type="secondary"):
        st.session_state.tasks = []
        st.success("데이터가 초기화되었습니다.")
        st.rerun()

# Main Screen Header
st.title("📅 DeadlineRadar : 과제 마감기한 자동 정리기")
st.markdown("다수의 강의계획서 PDF들을 한 번에 업로드하면, AI가 분석하여 하나의 통합 웹 캘린더에 일정을 시각화해 줍니다.")

# 5. File Upload & Processing Block
col1, col2 = st.columns([1, 1])

with col1:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📂 1단계: 다수의 강의계획서 PDF 업로드")
    uploaded_files = st.file_uploader("강의계획서 파일(.pdf)들을 끌어다 놓거나 다중 선택하세요.", type="pdf", accept_multiple_files=True)
    
    # Logic when files are uploaded
    if uploaded_files:
        st.info(f"업로드 완료: {len(uploaded_files)}개의 파일 대기 중")
        
        # Analyze button
        analyze_btn = st.button("🧠 AI로 마감일 자동 분석하기", type="primary", use_container_width=True)
        
        if analyze_btn:
            if not api_key_input:
                st.warning("⚠️ AI 분석을 사용하려면 좌측 사이드바에 **Gemini API Key**를 입력해 주세요. (또는 '데모 데이터 로드'를 활용하세요.)")
            else:
                all_new_tasks = []
                for uploaded_file in uploaded_files:
                    with st.spinner(f"[{uploaded_file.name}] 1. PDF 텍스트 추출 중..."):
                        pdf_text = extract_text_from_pdf(uploaded_file)
                        
                    if pdf_text:
                        with st.spinner(f"[{uploaded_file.name}] 2. Gemini AI 분석 중 ({model_option} 모델)..."):
                            extracted_tasks = call_gemini_to_extract_tasks(api_key_input, pdf_text, model_option)
                            if extracted_tasks:
                                all_new_tasks.extend(extracted_tasks)
                                
                if all_new_tasks:
                    # Append new tasks avoiding exact duplicates
                    existing_keys = {(t.get("course"), t.get("task_name"), t.get("due_date")) for t in st.session_state.tasks}
                    added_count = 0
                    for task in all_new_tasks:
                        key = (task.get("course"), task.get("task_name"), task.get("due_date"))
                        if key not in existing_keys:
                            st.session_state.tasks.append(task)
                            added_count += 1
                    
                    st.success(f"🎉 분석 완료! 새 일정 {added_count}개가 캘린더 대시보드에 추가되었습니다.")
                    st.rerun()
                else:
                    st.error("AI 분석 결과 파싱에 실패했습니다. API 키나 파일 상태를 다시 확인해 주세요.")
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📤 2단계: 캘린더 등록용 파일 내보내기")
    st.write("아래 버튼을 눌러 `.ics` 파일을 다운로드한 뒤, 구글/애플 캘린더에 간편하게 등록해 보세요.")
    
    if st.session_state.tasks:
        ics_data = generate_ics(st.session_state.tasks)
        st.download_button(
            label="📥 캘린더 파일(.ics) 다운로드",
            data=ics_data,
            file_name="DeadlineRadar_Calendar.ics",
            mime="text/calendar",
            use_container_width=True
        )
        st.caption("ℹ️ 다운로드한 ics 파일을 구글 캘린더(설정 -> 가져오기)에 업로드하면 일정이 자동으로 등록됩니다.")
    else:
        st.button("📥 캘린더 파일(.ics) 다운로드 (데이터 없음)", disabled=True, use_container_width=True)
        st.caption("먼저 1단계에서 분석을 진행하거나 데모 데이터를 불러오세요.")
    st.markdown('</div>', unsafe_allow_html=True)

# 6. Visual Monthly Calendar View (Site-native calendar)
if st.session_state.tasks:
    st.markdown("---")
    st.subheader("📅 3단계: 통합 월간 캘린더 뷰")
    
    # Calendar navigation
    c_prev, c_title, c_next = st.columns([1, 3, 1])
    
    with c_prev:
        if st.button("◀ 이전 달", use_container_width=True):
            if st.session_state.view_month == 1:
                st.session_state.view_month = 12
                st.session_state.view_year -= 1
            else:
                st.session_state.view_month -= 1
            st.rerun()
            
    with c_title:
        st.markdown(f"<h3 style='text-align: center; margin: 0; padding-top: 5px;'>{st.session_state.view_year}년 {st.session_state.view_month}월</h3>", unsafe_allow_html=True)
        
    with c_next:
        if st.button("다음 달 ▶", use_container_width=True):
            if st.session_state.view_month == 12:
                st.session_state.view_month = 1
                st.session_state.view_year += 1
            else:
                st.session_state.view_month += 1
            st.rerun()
            
    # Draw native monthly calendar
    calendar_html = draw_html_calendar(st.session_state.tasks, st.session_state.view_year, st.session_state.view_month)
    st.markdown(calendar_html, unsafe_allow_html=True)

# 7. Dashboard: Editable Table & Visual Schedule Grid
st.markdown("---")
st.subheader("📝 4단계: 일정 세부 조정 및 수동 추가/삭제")

if st.session_state.tasks:
    # Convert tasks to pandas DataFrame for editing
    df = pd.DataFrame(st.session_state.tasks)
    
    # Ensure correct columns exist
    required_cols = ["course", "task_name", "due_date", "description"]
    for col in required_cols:
        if col not in df.columns:
            df[col] = ""
            
    df = df[required_cols]
    
    st.markdown("""
    💡 **엑셀처럼 편집 가이드**:
    * 셀을 더블클릭하여 과목명, 과제명, 마감일을 **즉석에서 수정**할 수 있으며 수정사항은 위의 **월간 캘린더에 실시간 반영**됩니다.
    * 표 아래의 `+` 버튼을 눌러 **수동 일정을 추가**하거나, 행을 선택하고 `Del` 키를 눌러 **삭제**할 수 있습니다.
    """)
    
    # Interactive Data Editor
    edited_df = st.data_editor(
        df,
        num_rows="dynamic",
        column_config={
            "course": st.column_config.TextColumn("과목명", help="예: SW프로그래밍의기초", required=True),
            "task_name": st.column_config.TextColumn("과제/시험명", help="예: 기말 대체 과제 제출", required=True),
            "due_date": st.column_config.TextColumn("마감일 (YYYY-MM-DD)", help="YYYY-MM-DD 형식으로 입력하세요.", required=True),
            "description": st.column_config.TextColumn("설명", help="과제 세부 설명 및 제출 범위"),
        },
        use_container_width=True
    )
    
    # Sync edits back to session_state
    st.session_state.tasks = edited_df.to_dict(orient="records")
    
    # Visual D-Day Timeline
    st.markdown("---")
    st.subheader("🔔 다가오는 마감일 요약 (D-Day 순)")
    
    valid_tasks = []
    for task in st.session_state.tasks:
        if task.get("course") or task.get("task_name"):
            valid_tasks.append(task)
            
    if valid_tasks:
        sorted_tasks = []
        for task in valid_tasks:
            due_str = str(task.get("due_date", ""))
            badge, days_left = get_dday_html(due_str)
            sorted_tasks.append((task, badge, days_left))
            
        sorted_tasks.sort(key=lambda x: x[2])
        
        cols = st.columns(3)
        for idx, (task, badge, days_left) in enumerate(sorted_tasks):
            col_target = cols[idx % 3]
            with col_target:
                st.markdown(f"""
                <div class="card">
                    <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:10px;">
                        <span style="font-size:0.85rem; font-weight:bold; color:#818cf8; text-transform:uppercase;">{task.get('course', '기타')}</span>
                        {badge}
                    </div>
                    <h4 style="margin:5px 0 10px 0; font-size:1.15rem; color:#f1f5f9;">{task.get('task_name', '과제')}</h4>
                    <p style="font-size:0.9rem; color:#94a3b8; margin-bottom:5px;"><b>📅 마감일:</b> {task.get('due_date', '미정')}</p>
                    <p style="font-size:0.85rem; color:#64748b; line-height:1.4;">{task.get('description', '')}</p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.info("등록된 과제/시험 일정이 없습니다.")
else:
    # Empty State Guide
    st.markdown('<div class="alert-box">', unsafe_allow_html=True)
    st.markdown("""
    ### 🔔 시작하기 가이드
    1. **데모 데이터 체험**: 좌측 사이드바에서 **'✨ 데모 데이터 로드'** 버튼을 누르시면 준비된 여러 대학 과제 일정들이 캘린더와 표에 즉시 채워집니다.
    2. **내 파일 분석**: 본인의 **Gemini API Key**를 좌측 사이드바에 입력한 후, 위의 **1단계**에 여러 개의 강의계획서 PDF 파일들을 업로드하여 다중 파싱을 진행해 보세요.
    """)
    st.markdown('</div>', unsafe_allow_html=True)
