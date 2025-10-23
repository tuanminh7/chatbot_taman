import os
import io
import json
import re
import random
import base64
from PIL import Image
from datetime import datetime
from flask import send_file
from werkzeug.utils import secure_filename
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash, current_app

# ReportLab để tạo PDF
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


import google.generativeai as genai
import PyPDF2
import pytz

from google.cloud import texttospeech
from utils.ocr import extract_text_from_image
from utils.gemini_api import analyze_text_with_gemini
from datetime import datetime, timezone


datetime.now(timezone.utc)

app = Flask(__name__)
app.secret_key = "phuonganh2403"

vn_timezone = pytz.timezone('Asia/Ho_Chi_Minh')
timestamp = datetime.now(vn_timezone).strftime("%Y-%m-%d %H:%M:%S")
#AIzaSyCviosQe-qIKt_MhseTVXO7GEYzmCkVSmE
os.environ["GOOGLE_API_KEY"] = "AIzaSyDx4KnyXaBKZIVHiFuiDjBUwkX8tPY8XuQ"
genai.configure(api_key=os.environ["GOOGLE_API_KEY"])

# Dùng model Gemini 2.0
model = genai.GenerativeModel("models/gemini-2.0-flash")
#
app.config['UPLOAD_FOLDER'] = 'uploads'
################

# Hàm đọc dữ liệu theo chủ đề
def load_context(topic):
    file_map = {
        "tam_li": "data_tam_li.txt",
        "stress": "stress.txt",
        "nghe_nghiep": "nghe_nghiep.txt"
    }
    file_path = file_map.get(topic, "data_tam_li.txt")
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return "Không tìm thấy dữ liệu phù hợp."

# Hàm tạo prompt theo chủ đề
def build_prompt(topic, context_data, user_input):
    if topic == "tam_li":
        return (
            f"Bạn là một trợ lý AI thân thiện, chuyên tư vấn tâm lý cho học sinh.\n"
            f"Dưới đây là dữ liệu liên quan đến tâm lý học sinh:\n{context_data}\n\n"
            f"Hãy kết hợp dữ liệu này với kiến thức bạn đã học để trả lời câu hỏi sau "
            f"một cách nhẹ nhàng, đồng cảm, tránh từ ngữ tiêu cực:\n\n"
            f"Câu hỏi của học sinh: {user_input}\nTrợ lý:"
        )
    elif topic == "stress":
        return (
            f"Bạn là một trợ lý AI giúp học sinh vượt qua căng thẳng và áp lực học tập.\n"
            f"Dưới đây là dữ liệu liên quan đến stress:\n{context_data}\n\n"
            f"Hãy trả lời câu hỏi sau với giọng điệu trấn an, đưa ra lời khuyên giúp học sinh bình tĩnh:\n\n"
            f"Câu hỏi của học sinh: {user_input}\nTrợ lý:"
        )
    elif topic == "nghe_nghiep":
        return (
            f"Bạn là một trợ lý AI chuyên tư vấn định hướng nghề nghiệp cho học sinh.\n"
            f"Dưới đây là dữ liệu liên quan đến lựa chọn nghề nghiệp:\n{context_data}\n\n"
            f"Hãy trả lời câu hỏi sau với giọng điệu khích lệ, giúp học sinh khám phá bản thân và đưa ra lời khuyên phù hợp:\n\n"
            f"Câu hỏi của học sinh: {user_input}\nTrợ lý:"
        )
    else:
        return (
            f"Bạn là một trợ lý AI thân thiện, chuyên tư vấn cho học sinh.\n"
            f"Dưới đây là dữ liệu liên quan đến chủ đề '{topic}':\n{context_data}\n\n"
            f"Hãy trả lời câu hỏi sau một cách nhẹ nhàng và có tính hỗ trợ tâm lý:\n\n"
            f"Câu hỏi của học sinh: {user_input}\nTrợ lý:"
        )

@app.route("/tro_chuyen_tam_li_cung_tro_ly_ai_pham_hang", methods=["GET", "POST"])
def tam_li_chat():
    topic = request.args.get("topic", "tam_li")
    context_data = load_context(topic)
    response_text = ""
    if request.method == "POST":
        user_input = request.form.get("user_input")
        if user_input:
            prompt = build_prompt(topic, context_data, user_input)
            response = model.generate_content(prompt)
            response_text = response.text
    return render_template("tam_li.html", response=response_text, topic=topic)



####################
def read_pdf(file_path):
    text = ""
    try:
        with open(file_path, "rb") as f:
            reader = PyPDF2.PdfReader(f)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        print(f"Lỗi đọc PDF {file_path}: {e}")
    return text

custom_data = ""

if os.path.exists("data.txt"):
    with open("data.txt", "r", encoding="utf-8") as f:
        custom_data += f.read() + "\n"
pdf_folder = "data"
if os.path.exists(pdf_folder):
    for file_name in os.listdir(pdf_folder):
        if file_name.lower().endswith(".pdf"):
            file_path = os.path.join(pdf_folder, file_name)
            custom_data += read_pdf(file_path) + "\n"




docs_list = [
    {
        "title": "Tài liệu Anh 12",
        "link": "https://docs.google.com/document/d/1_pXGbZQHw_OeWcpYwQYw1Yu4vKxBMV6fZWxm4dmsXLg/edit?usp=sharing"
    },
    {
        "title": "Tài liệu Lý 12",
        "link": "https://docs.google.com/document/d/1_pXGbZQHw_OeWcpYwQYw1Yu4vKxBMV6fZWxm4dmsXLg/edit?usp=sharing"
    },
    {
        "title": "Tài liệu Toán 12",
        "link": ""
    },
    {
        "title": "Tài liệu Lý 12",
        "link": ""
    },
    {
        "title": "Tài liệu Toán 12",
        "link": ""
    },
    {
        "title": "Tài liệu Lý 12",
        "link": ""
    },
    {
        "title": "Tài liệu Toán 12",
        "link": ""
    },
    {
        "title": "Tài liệu Lý 12",
        "link": ""
    },
    {
        "title": "Tài liệu Hóa 12",
        "link": ""
    }
]

@app.route('/')
def menu():
    return render_template('menu.html')

@app.route('/stress_test', methods=['GET', 'POST'])
def stress_test():
    if request.method == 'POST':
        answers = {int(k): int(v) for k, v in request.form.items()}
        group_D = [3, 5, 10, 13, 16, 17, 21]  
        group_A = [2, 4, 7, 9, 15, 19, 20]    
        group_S = [1, 6, 8, 11, 12, 14, 18]   # Stress

      
        score_D = sum(answers[q] for q in group_D) * 2
        score_A = sum(answers[q] for q in group_A) * 2
        score_S = sum(answers[q] for q in group_S) * 2

     
        def classify_D(score):
            if score <= 9: return "Bình thường"
            elif score <= 13: return "Nhẹ"
            elif score <= 20: return "Vừa"
            elif score <= 27: return "Nặng"
            else: return "Rất nặng"

        def classify_A(score):
            if score <= 7: return "Bình thường"
            elif score <= 9: return "Nhẹ"
            elif score <= 14: return "Vừa"
            elif score <= 19: return "Nặng"
            else: return "Rất nặng"

        def classify_S(score):
            if score <= 14: return "Bình thường"
            elif score <= 18: return "Nhẹ"
            elif score <= 25: return "Vừa"
            elif score <= 33: return "Nặng"
            else: return "Rất nặng"

        return render_template(
            'stress_result.html',
            score_D=score_D, score_A=score_A, score_S=score_S,
            level_D=classify_D(score_D),
            level_A=classify_A(score_A),
            level_S=classify_S(score_S)
        )

  
    questions = [
        "Tôi thấy khó mà thoải mái được",
        "Tôi bị khô miệng",
        "Tôi dường như chẳng có chút cảm xúc tích cực nào",
        "Tôi bị rối loạn nhịp thở (thở gấp, khó thở dù chẳng làm việc gì nặng)",
        "Tôi thấy khó bắt tay vào công việc",
        "Tôi có xu hướng phản ứng thái quá với mọi tình huống",
        "Tôi bị ra mồ hôi (chẳng hạn như mồ hôi tay...)",
        "Tôi thấy mình đang suy nghĩ quá nhiều",
        "Tôi lo lắng về những tình huống có thể làm tôi hoảng sợ hoặc biến tôi thành trò cười",
        "Tôi thấy mình chẳng có gì để mong đợi cả",
        "Tôi thấy bản thân dễ bị kích động",
        "Tôi thấy khó thư giãn được",
        "Tôi cảm thấy chán nản, thất vọng",
        "Tôi không chấp nhận được việc có cái gì đó xen vào cản trở việc tôi đang làm",
        "Tôi thấy mình gần như hoảng loạn",
        "Tôi không thấy hứng thú với bất kỳ việc gì nữa",
        "Tôi cảm thấy mình chẳng đáng làm người",
        "Tôi thấy mình khá dễ phật ý, tự ái",
        "Tôi nghe thấy rõ tiếng nhịp tim dù chẳng làm việc gì",
        "Tôi hay sợ vô cớ",
        "Tôi thấy cuộc sống vô nghĩa"
    ]
    return render_template('stress_test.html', questions=questions)

questions_holland = [
    {"text": "Tôi thích sửa chữa máy móc, thiết bị.", "type": "R"},
    {"text": "Tôi thích nghiên cứu, tìm hiểu hiện tượng tự nhiên.", "type": "I"},
    {"text": "Tôi thích vẽ, viết hoặc sáng tạo nghệ thuật.", "type": "A"},
    {"text": "Tôi thích làm việc nhóm và giúp đỡ người khác.", "type": "S"},
    {"text": "Tôi thích thuyết phục và lãnh đạo người khác.", "type": "E"},
    {"text": "Tôi thích làm việc với số liệu, giấy tờ và sắp xếp hồ sơ.", "type": "C"},
    {"text": "Tôi thích làm việc ngoài trời.", "type": "R"},
    {"text": "Tôi tò mò về cách mọi thứ hoạt động.", "type": "I"},
    {"text": "Tôi yêu thích âm nhạc, hội họa hoặc sân khấu.", "type": "A"},
    {"text": "Tôi dễ dàng kết bạn và trò chuyện với người lạ.", "type": "S"},
    {"text": "Tôi thích điều hành dự án hoặc quản lý một nhóm.", "type": "E"},
    {"text": "Tôi thích nhập dữ liệu hoặc làm việc hành chính.", "type": "C"},
    {"text": "Tôi thích vận hành máy móc hoặc công cụ.", "type": "R"},
    {"text": "Tôi thích giải quyết các bài toán hoặc vấn đề phức tạp.", "type": "I"},
    {"text": "Tôi thích thiết kế hoặc tạo ra sản phẩm sáng tạo.", "type": "A"},
    {"text": "Tôi thích giúp đỡ người khác giải quyết vấn đề cá nhân.", "type": "S"},
    {"text": "Tôi thích bán hàng hoặc tiếp thị sản phẩm.", "type": "E"},
    {"text": "Tôi thích theo dõi và lưu trữ hồ sơ cẩn thận.", "type": "C"},
    {"text": "Tôi thích sửa chữa xe cộ hoặc đồ điện tử.", "type": "R"},
    {"text": "Tôi thích tìm hiểu về khoa học hoặc công nghệ mới.", "type": "I"},
    {"text": "Tôi thích viết truyện, thơ hoặc kịch bản.", "type": "A"},
    {"text": "Tôi thích giảng dạy hoặc huấn luyện người khác.", "type": "S"},
    {"text": "Tôi thích lập kế hoạch kinh doanh.", "type": "E"},
    {"text": "Tôi thích quản lý dữ liệu và hồ sơ.", "type": "C"},
    {"text": "Tôi thích làm công việc xây dựng hoặc sửa chữa nhà cửa.", "type": "R"},
    {"text": "Tôi thích thực hiện thí nghiệm.", "type": "I"},
    {"text": "Tôi thích sáng tác nhạc hoặc viết lời bài hát.", "type": "A"},
    {"text": "Tôi thích làm công tác xã hội hoặc tình nguyện.", "type": "S"},
    {"text": "Tôi thích lãnh đạo chiến dịch hoặc dự án.", "type": "E"},
    {"text": "Tôi thích lập bảng tính hoặc tài liệu thống kê.", "type": "C"},
    {"text": "Tôi thích đi bộ đường dài hoặc các hoạt động ngoài trời.", "type": "R"},
    {"text": "Tôi thích phân tích dữ liệu hoặc nghiên cứu thị trường.", "type": "I"},
    {"text": "Tôi thích chụp ảnh hoặc quay phim.", "type": "A"},
    {"text": "Tôi thích chăm sóc sức khỏe cho người khác.", "type": "S"},
    {"text": "Tôi thích phát triển chiến lược tiếp thị.", "type": "E"},
    {"text": "Tôi thích thực hiện công việc kế toán hoặc tài chính.", "type": "C"},
    {"text": "Tôi thích lắp ráp hoặc tháo rời thiết bị.", "type": "R"},
    {"text": "Tôi thích đọc sách khoa học hoặc tài liệu chuyên môn.", "type": "I"},
    {"text": "Tôi thích tham gia vào các hoạt động nghệ thuật cộng đồng.", "type": "A"},
    {"text": "Tôi thích hỗ trợ tâm lý cho người gặp khó khăn.", "type": "S"},
    {"text": "Tôi thích đàm phán hợp đồng hoặc thỏa thuận.", "type": "E"},
    {"text": "Tôi thích kiểm tra lỗi trong dữ liệu.", "type": "C"},
    {"text": "Tôi thích chế tạo hoặc lắp ráp thủ công.", "type": "R"},
    {"text": "Tôi thích đặt câu hỏi và tìm hiểu nguyên nhân sự việc.", "type": "I"},
    {"text": "Tôi thích làm đồ thủ công mỹ nghệ.", "type": "A"},
    {"text": "Tôi thích tổ chức các sự kiện cộng đồng.", "type": "S"},
    {"text": "Tôi thích khởi nghiệp kinh doanh.", "type": "E"},
    {"text": "Tôi thích làm việc theo quy trình rõ ràng.", "type": "C"},
    {"text": "Tôi thích sử dụng công cụ hoặc máy móc nặng.", "type": "R"},
    {"text": "Tôi thích nghiên cứu công nghệ mới.", "type": "I"},
    {"text": "Tôi thích biểu diễn trước khán giả.", "type": "A"},
    {"text": "Tôi thích đào tạo và phát triển kỹ năng cho người khác.", "type": "S"},
    {"text": "Tôi thích thuyết phục người khác mua sản phẩm.", "type": "E"},
    {"text": "Tôi thích sắp xếp và phân loại tài liệu.", "type": "C"},
    {"text": "Tôi thích sửa chữa các thiết bị điện gia dụng.", "type": "R"},
    {"text": "Tôi thích khám phá và nghiên cứu những điều mới lạ.", "type": "I"},
    {"text": "Tôi thích viết kịch bản hoặc đạo diễn phim.", "type": "A"},
    {"text": "Tôi thích hỗ trợ người khuyết tật.", "type": "S"},
    {"text": "Tôi thích quản lý nhân sự.", "type": "E"},
    {"text": "Tôi thích theo dõi sổ sách và ngân sách.", "type": "C"}
]

holland_types = {
    "R": {
        "name": "Realistic (Kỹ thuật, thực tế)",
        "desc": "Thích làm việc tay chân, máy móc, kỹ thuật, ngoài trời.",
        "jobs": [
            "Kỹ sư cơ khí",
            "Thợ điện",
            "Kỹ thuật viên ô tô",
            "Công nhân xây dựng",
            "Kỹ sư nông nghiệp"
        ]
    },
    "I": {
        "name": "Investigative (Nghiên cứu)",
        "desc": "Thích phân tích, tìm tòi, khám phá, làm việc khoa học.",
        "jobs": [
            "Nhà khoa học",
            "Bác sĩ",
            "Kỹ sư phần mềm",
            "Nhà nghiên cứu y sinh",
            "Chuyên gia dữ liệu"
        ]
    },
    "A": {
        "name": "Artistic (Nghệ thuật)",
        "desc": "Thích sáng tạo, tự do, nghệ thuật, biểu diễn.",
        "jobs": [
            "Họa sĩ",
            "Nhà thiết kế đồ họa",
            "Nhạc sĩ",
            "Đạo diễn",
            "Nhiếp ảnh gia"
        ]
    },
    "S": {
        "name": "Social (Xã hội)",
        "desc": "Thích giúp đỡ, giao tiếp, dạy học, hỗ trợ cộng đồng.",
        "jobs": [
            "Giáo viên",
            "Nhân viên xã hội",
            "Nhà tâm lý học",
            "Điều dưỡng",
            "Hướng dẫn viên du lịch"
        ]
    },
    "E": {
        "name": "Enterprising (Quản lý, kinh doanh)",
        "desc": "Thích lãnh đạo, kinh doanh, thuyết phục, mạo hiểm.",
        "jobs": [
            "Doanh nhân",
            "Nhà quản lý dự án",
            "Chuyên viên marketing",
            "Luật sư",
            "Nhân viên bán hàng"
        ]
    },
    "C": {
        "name": "Conventional (Hành chính)",
        "desc": "Thích công việc văn phòng, chi tiết, tuân thủ quy trình.",
        "jobs": [
            "Nhân viên kế toán",
            "Thư ký",
            "Nhân viên nhập liệu",
            "Nhân viên hành chính",
            "Chuyên viên tài chính"
        ]
    }
}

@app.route("/relax/<mode>")
def relax_page(mode):
    valid_modes = ["menu", "music", "yoga", "meditation", "breathing"]
    if mode not in valid_modes:
        return "Trang không tồn tại", 404
    return render_template(f"relax_{mode}.html")



@app.route("/holland", methods=["GET", "POST"])
def holland_test():
    if request.method == "POST":
        
        scores = {key: 0 for key in holland_types.keys()}
        for idx in range(1, len(questions_holland) + 1):
            ans = request.form.get(str(idx))
            if ans and ans.isdigit():
                scores[questions_holland[idx - 1]["type"]] += int(ans) - 1
        sorted_types = sorted(scores.items(), key=lambda x: x[1], reverse=True)

        top3_details = [
            {
                "code": t[0],
                "name": holland_types[t[0]]["name"],
                "desc": holland_types[t[0]]["desc"],
                "jobs": holland_types[t[0]]["jobs"],
                "score": t[1]
            }
            for t in sorted_types[:3]
        ]

        return render_template(
            "holland_result.html",
            top3_details=top3_details
        )

    return render_template("holland.html", questions=questions_holland)

USERS_FILE = 'users.json'
def load_users():
    if not os.path.exists(USERS_FILE):
        return {}
    with open(USERS_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_users(data):
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        users = load_users()

        if username in users and users[username]['password'] == password:
            session['username'] = username
            return redirect(url_for('emotion_journal'))
        else:
            return render_template('login.html', message="Sai tên đăng nhập hoặc mật khẩu")
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password').strip()
        users = load_users()

        if username in users:
            return render_template('register.html', message="Tên đăng nhập đã tồn tại")
        if len(users) >= 20:
            return render_template('register.html', message="Đã đủ 20 tài khoản test")

        users[username] = {"password": password, "logs": []}
        save_users(users)
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/emotion_journal', methods=['GET', 'POST'])
def emotion_journal():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    users = load_users()
    history = users.get(username, {}).get('logs', [])

    # Danh sách nhạc cho từng lựa chọn
    music_videos = {
        "Đom Đóm": "https://www.youtube.com/embed/HTwrVZ0eExvuE05p",
        "Nàng Thơ": "https://www.youtube.com/embed/HTwrVZ0eExvuE05p",
        "Nevada": "https://www.youtube.com/embed/d9MyW72ELq0"
    }

    
    tz_vn = pytz.timezone('Asia/Ho_Chi_Minh')

    if request.method == 'POST':
        emotion = request.form.get('emotion')
        note = request.form.get('note', '').strip()
        activities = request.form.getlist('activities')
        
        timestamp = datetime.now(tz_vn).strftime("%d/%m/%Y %H:%M:%S")

        
        new_entry = {
            'datetime': timestamp,
            'emotion': emotion,
            'note': note,
            'activities': activities
        }
        history.append(new_entry)
        users[username]['logs'] = history
        save_users(users)

        message = "Ghi lại cảm xúc thành công!"
        return render_template('emotion_journal.html',
                               message=message,
                               history=history,
                               music_videos=music_videos)

    return render_template('emotion_journal.html',
                           history=history,
                           music_videos=music_videos)


@app.route('/export_pdf')
def export_pdf():
    if 'username' not in session:
        return redirect(url_for('login'))

    username = session['username']
    users = load_users()
    history = users.get(username, {}).get('logs', [])

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()

    # 🔤 Đăng ký font Roboto từ thư mục fonts/
    font_path = os.path.join('fonts', 'Roboto-VariableFont_wdth,wght.ttf')
    pdfmetrics.registerFont(TTFont('Roboto', font_path))

    # 🎨 Gán font Roboto cho tất cả các style
    for style_name in styles.byName:
        styles[style_name].fontName = 'Roboto'

    elements = []
    elements.append(Paragraph(f"📓 Nhật ký cảm xúc của {username}", styles['Title']))
    elements.append(Spacer(1, 20))

    if not history:
        elements.append(Paragraph("Không có dữ liệu cảm xúc.", styles['Normal']))
    else:
        for i, entry in enumerate(history, start=1):
            elements.append(Paragraph(f"<b>#{i}</b> - {entry['datetime']}", styles['Heading3']))
            elements.append(Paragraph(f"Cảm xúc: {entry['emotion']}", styles['Normal']))
            elements.append(Paragraph(f"Hoạt động: {', '.join(entry['activities'])}", styles['Normal']))
            elements.append(Paragraph(f"Ghi chú: {entry['note']}", styles['Normal']))
            elements.append(Spacer(1, 10))

    doc.build(elements)
    buffer.seek(0)

    return send_file(buffer, as_attachment=True,
                     download_name=f"nhat_ky_cam_xuc_{username}.pdf",
                     mimetype='application/pdf')


###############
@app.route("/")
def main_menu():  # Đổi tên hàm từ 'home' sang 'main_menu'
    return render_template("menu.html")

@app.route("/docs")
def docs():
    return render_template("docs.html", docs=docs_list)

@app.route("/chatbot")
def chatbot_page():
    return render_template("index.html")  

@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message", "")
    prompt = f"""
    Bạn là trợ lý AI thông minh. Bạn có dữ liệu sau:
    {custom_data}

    Hãy trả lời câu hỏi của người dùng dựa trên dữ liệu trên,
    và nếu không tìm thấy thì trả lời bằng kiến thức chung của bạn.
    nếu họ nói chuyện bằng tiếng việt thì hãy nói lại bằng tiếng việt

    Câu hỏi: {user_message}
    """
    model = genai.GenerativeModel("models/gemini-2.0-flash")##########################
    response = model.generate_content(prompt)
    return jsonify({"reply": response.text})

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "static", "replies")
os.makedirs(AUDIO_DIR, exist_ok=True)
#chat voice bị lỗi
# Hàm đọc dữ liệu người dùng
def load_user_data():
    try:
        with open("data.txt", "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        return ""

def random_filename(prefix="reply", ext="mp3", n=8):
    s = "".join(random.choices(string.ascii_lowercase + string.digits, k=n))
    return f"{prefix}_{s}.{ext}"

def contains_english(text):
    return bool(re.search(r'[A-Za-z]', text))

@app.route("/")
def index():
    return render_template("voice_chat.html")  ###################

@app.route("/replies/<path:filename>")
def serve_reply_audio(filename):
    return send_from_directory(AUDIO_DIR, filename, as_attachment=False)

@app.route("/chat_tam_an", methods=["POST"])
def chat_tam_an():
    data = request.get_json() or {}
    user_message = data.get("message", "").strip()
    if not user_message:
        return jsonify({"error": "Không có message"}), 400

    user_data = load_user_data()
    prompt = f"""Dưới đây là dữ liệu cá nhân của người dùng:
{json.dumps(user_data, ensure_ascii=False, indent=2)}

QUY TẮC BẮT BUỘC:
- Chỉ trả lời bằng tiếng Việt, không dùng từ/cụm từ tiếng Anh.
- Nếu mô hình dự định dùng từ tiếng Anh, hãy thay bằng từ tiếng Việt tương đương.
- Giọng thân thiện, tự nhiên như một người bạn.
- Câu trả lời ngắn gọn, dưới 3 câu.

Người dùng hỏi: {user_message}
"""
    try:
        model = genai.GenerativeModel("models/gemini-2.0-flash")##########################
        resp = model.generate_content(prompt)
        text_reply = resp.text.strip()
    except Exception as e:
        print("Lỗi khi gọi Gemini:", e)
        text_reply = "Xin lỗi, hiện tại tôi không thể trả lời ngay. Bạn thử lại sau nhé."

    if contains_english(text_reply):
        try:
            follow_prompt = prompt + "\n\nBạn đã sử dụng từ tiếng Anh, hãy trả lời lại hoàn toàn bằng tiếng Việt."
            resp2 = model.generate_content(follow_prompt)
            text_reply = resp2.text.strip()
        except Exception as e:
            print("Lỗi follow-up Gemini:", e)

    audio_filename = None
    try:
        tts_client = texttospeech.TextToSpeechClient()
        synthesis_input = texttospeech.SynthesisInput(text=text_reply)
        voice = texttospeech.VoiceSelectionParams(
            language_code="vi-VN",
            name="vi-VN-Wavenet-A",  
            ssml_gender=texttospeech.SsmlVoiceGender.FEMALE
        )
        audio_config = texttospeech.AudioConfig(
            audio_encoding=texttospeech.AudioEncoding.MP3,
            speaking_rate=1.0,
            pitch=0.0
        )

        tts_response = tts_client.synthesize_speech(
            input=synthesis_input,
            voice=voice,
            audio_config=audio_config
        )

        audio_filename = random_filename()
        audio_path = os.path.join(AUDIO_DIR, audio_filename)
        with open(audio_path, "wb") as f:
            f.write(tts_response.audio_content)
    except Exception as e:
        print("Lỗi Google TTS:", e)
        audio_filename = None

    result = {"reply": text_reply}
    if audio_filename:
        result["audio_url"] = f"/replies/{audio_filename}"
    else:
        result["audio_url"] = None

    return jsonify(result)

def load_exam(de_id):
    with open('exam_data.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data.get(de_id)

@app.route('/index_td')
def index_td():
    return render_template('index_tn.html')


@app.route('/exam/<de_id>')
def exam(de_id):
    questions = load_exam(de_id)
    if not questions:
        return "Không tìm thấy đề thi."

    video_url = questions.get("video")  
    return render_template('exam.html', questions=questions, de_id=de_id, video_url=video_url)

@app.route('/submit/<de_id>', methods=['GET', 'POST'])
def submit(de_id):
    if request.method != 'POST':
        return redirect(url_for('exam', de_id=de_id))

    questions = load_exam(de_id)
    if not questions:
        return "Không tìm thấy đề thi."

    correct_count = 0
    total_questions = 0
    feedback = []
    results = [] 


    for i, q in enumerate(questions.get("multiple_choice", [])):
        user_answer = request.form.get(f"mc_{i}")
        correct = q["answer"]
        total_questions += 1
        if user_answer and user_answer.strip().lower() == correct.strip().lower():
            correct_count += 1
            results.append({"status": "Đúng", "note": ""})
        else:
            msg = f"Câu {i+1} sai. Đáp án đúng là: {correct}"
            results.append({"status": "Sai", "note": msg})
            feedback.append(msg)

    # Đúng sai
    for i, tf in enumerate(questions.get("true_false", [])):
        for j, correct_tf in enumerate(tf["answers"]):
            user_tf_raw = request.form.get(f"tf_{i}_{j}", "").lower()
            user_tf = user_tf_raw == "true"
            total_questions += 1
            if user_tf == correct_tf:
                correct_count += 1
                results.append({"status": "Đúng", "note": ""})
            else:
                msg = f"Câu {i+1+len(questions['multiple_choice'])}, ý {j+1} sai."
                results.append({"status": "Sai", "note": msg})
                feedback.append(msg)

    score = correct_count  
    summary = f"Học sinh làm đúng {correct_count} / {total_questions} câu."
    try:
        prompt = (
            f"{summary}\n\n"
            "Dưới đây là danh sách các lỗi học sinh mắc phải:\n"
            + "\n".join(feedback) + "\n\n"
            "Bạn là giáo viên lịch sử. Hãy:\n"
            "1. Nhận xét tổng thể bài làm\n"
            "2. Phân tích từng lỗi sai (nêu lý do sai, giải thích kiến thức liên quan)\n"
            "3. Đề xuất ít nhất 3 dạng bài tập cụ thể để học sinh luyện tập đúng phần bị sai"
        )
        response = model.generate_content([prompt])
        ai_feedback = response.text
    except Exception as e:
        ai_feedback = f"❌ Lỗi khi gọi AI: {str(e)}"
    return render_template(
        'result.html',
        score=score,
        feedback=feedback,
        ai_feedback=ai_feedback,
        total_questions=total_questions,
        results=results
    )

@app.route('/upload_image', methods=['GET', 'POST'])
def upload_image():
    ai_feedback = None

    if request.method == 'POST':
        image = request.files.get('image')
        if not image or image.filename == '':
            return render_template('upload_image.html', feedback="❌ Không có ảnh được chọn.")

        image_path = os.path.join(app.config['UPLOAD_FOLDER'], image.filename)
        image.save(image_path)

        try:
            img = Image.open(image_path)
            response = model.generate_content([
                img,
                "Đây là ảnh bài làm của học sinh. Hãy phân tích nội dung, chỉ ra lỗi sai nếu có, và đề xuất cải thiện."
            ])
            ai_feedback = response.text
        except Exception as e:
            ai_feedback = f"❌ Lỗi khi xử lý ảnh: {str(e)}"

    return render_template('upload_image.html', feedback=ai_feedback)
######
@app.route("/tam_an")
def tam_an():
    return render_template("chat_tam_an.html")
##### game
@app.route("/")
def home():
    return render_template("menu.html")

@app.route("/enter_nickname")
def enter_nickname():
    return render_template("nickname.html")

@app.route("/start_game", methods=["POST"])
def start_game():
    nickname = request.form["nickname"]
    bai = request.form["bai"]
    session["nickname"] = nickname
    session["bai"] = bai
    return redirect("/game")

@app.route("/game")
def game():
    return render_template("game.html")

@app.route("/get_questions")
def get_questions_quiz():
    import random
    bai = session.get("bai", "bai_1")
    with open("questions.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    questions = data.get(bai, [])
    random.shuffle(questions)
    for q in questions:
        random.shuffle(q["options"])
    return jsonify(questions[:20])

@app.route("/submit_score", methods=["POST"])
def submit_score():
    nickname = session.get("nickname")
    bai = session.get("bai")  
    score = request.json["score"]

    if not nickname:
        return jsonify({"status": "error", "message": "No nickname found"})
    if not bai:
        return jsonify({"status": "error", "message": "No bai found"})

    if not os.path.exists("scores.json"):
        with open("scores.json", "w", encoding="utf-8") as f:
            json.dump([], f)

    with open("scores.json", "r+", encoding="utf-8") as f:
        scores = json.load(f)
        now = datetime.now().strftime("%d/%m/%Y %H:%M")

        existing = next((s for s in scores if s["nickname"] == nickname and s.get("bai") == bai), None)

        if existing:
            if score > existing["score"]:
                existing["score"] = score
                existing["time"] = now
        else:
            scores.append({
                "nickname": nickname,
                "score": score,
                "time": now,
                "bai": bai  
            })
        filtered = [s for s in scores if s.get("bai") == bai]
        top50 = sorted(filtered, key=lambda x: x["score"], reverse=True)[:50]
        others = [s for s in scores if s.get("bai") != bai]
        final_scores = others + top50

        f.seek(0)
        json.dump(final_scores, f, ensure_ascii=False, indent=2)
        f.truncate()

    return jsonify({"status": "ok"})


@app.route("/leaderboard")
def leaderboard():
    bai = session.get("bai")  

    if not bai:
        bai = "bai_1"  

    if not os.path.exists("scores.json"):
        top5 = []
    else:
        with open("scores.json", "r", encoding="utf-8") as f:
            scores = json.load(f)

        # ✅ lọc điểm theo bài
        filtered = [s for s in scores if s.get("bai") == bai]
        top5 = sorted(filtered, key=lambda x: x["score"], reverse=True)[:5]

    return render_template("leaderboard.html", players=top5, bai=bai)

@app.route("/get_questions")
def get_questions():
    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)
    selected = random.sample(questions, min(10, len(questions)))
    return jsonify(selected)

####if __name__ == '__main__':
   ### app.run(debug=True)
