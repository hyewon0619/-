import logging
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.exceptions import BadRequest
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
import openai
import spacy  # 명사 추출
import io
import re     # 숫자 추출
import random


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://admin:today0430@database-1.cva6yg8oenlg.ap-northeast-2.rds.amazonaws.com/mentosdb'
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_pre_ping': True}
db = SQLAlchemy(app)

openai.api_key = 'sk-mentos-qHLdPTiXoYsq42J13McDT3BlbkFJZvXpl4ImtXbSi1eUzFEb'

# spaCy 모델 로드
nlp = spacy.load("ko_core_news_sm")  # 한글 모델

@app.errorhandler(BadRequest)
def handle_bad_request(e):
    return jsonify({'message': 'Invalid JSON format'}), 400

# 로그 설정
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger('phpsignup')

class Guest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    gender = db.Column(db.Enum('male', 'female'))
    birthdate = db.Column(db.Date)
    name = db.Column(db.String(100), nullable=True)  # 이름 필드 추가


class Survey(db.Model):
    __tablename__ = 'survey'

    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    role = db.Column(db.String(20))
    activity = db.Column(db.String(20))
    gender = db.Column(db.Enum('male', 'female'))
    age_group = db.Column(db.Integer)
    location = db.Column(db.String(50))
    activity_level = db.Column(db.String(20))

    
class AIChatRoom(db.Model):
    __tablename__ = 'ai_chat_room'

    id = db.Column(db.Integer, primary_key=True)
    guest_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    activity = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class AIChatMessage(db.Model):
    __tablename__ = 'ai_chat_message'

    id = db.Column(db.Integer, primary_key=True)
    ai_chat_room_id = db.Column(db.Integer, nullable=False)  # 채팅방 ID
    role = db.Column(db.String(20))  # 'user' or 'assistant'
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class LevelTest(db.Model):
    __tablename__ = 'level_test'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    hobby = db.Column(db.String(50), nullable=False)
    question_number = db.Column(db.Integer, nullable=False)  # 문제 번호 추가
    question = db.Column(db.String(255), nullable=False)
    answer = db.Column(db.Integer, nullable=False)  # 정답 번호


class CookingPlan(db.Model):
    __tablename__ = 'cooking_plan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 기본 키, 자동 증가
    dish_name = db.Column(db.String(100), nullable=False)  # 요리 이름
    ingredients = db.Column(db.Text, nullable=False)  # 재료
    tools = db.Column(db.Text, nullable=False)  # 도구
    method = db.Column(db.Text, nullable=False)  # 방법
    step = db.Column(db.Numeric(8, 4), nullable=True)  # 단계, 소수점 아래 4자리까지

class Plan(db.Model):
    __tablename__ = 'plan'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cooking_plan_id = db.Column(db.Integer, db.ForeignKey('cooking_plan.id'), nullable=False)
    chat_room_id = db.Column(db.Integer, db.ForeignKey('ai_chat_room.id'), nullable=False)
    goal_number = db.Column(db.Integer, nullable=False)
    hobby = db.Column(db.String(100), nullable=True)  # 새로운 hobby 컬럼 추가


class Method(db.Model):
    __tablename__ = 'method'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    cooking_plan_id = db.Column(db.Integer, db.ForeignKey('cooking_plan.id'), nullable=False)
    step_number = db.Column(db.Integer, nullable=False)
    description = db.Column(db.Text, nullable=False)

class WeeklyTask(db.Model):
    __tablename__ = 'weekly_tasks'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 기본 키, 자동 증가
    chat_room_id = db.Column(db.Integer, nullable=False)  # 채팅방 ID
    week_number = db.Column(db.Integer, nullable=False)  # 주차 번호
    goal = db.Column(db.Text, nullable=False)  # 목표
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # 생성 시간

class WeeklyTaskDetail(db.Model):
    __tablename__ = 'WeeklyTaskDetail'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)  # 기본 키, 자동 증가
    chat_room_id = db.Column(db.Integer, nullable=False)  # 채팅방 ID
    week_number = db.Column(db.Integer, nullable=False)  # 주차 번호
    task = db.Column(db.Text, nullable=False)  # 소과제 설명
    created_at = db.Column(db.DateTime, server_default=db.func.current_timestamp())  # 생성 일시

class Matching(db.Model):
    __tablename__ = 'matching'

    id = db.Column(db.Integer, primary_key=True)  # 매칭 ID
    mentee_id = db.Column(db.Integer, db.ForeignKey('survey.guest_id'), nullable=False)  # 멘티 ID
    mentor_id = db.Column(db.Integer, db.ForeignKey('survey.guest_id'), nullable=False)  # 멘토 ID
    matched_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # 매칭 날짜

class MatchChatRoom(db.Model):
    __tablename__ = 'match_chat_room'

    id = db.Column(db.Integer, primary_key=True)
    mentee_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)
    mentor_id = db.Column(db.Integer, db.ForeignKey('guest.id'), nullable=False)  # 멘토 ID
    activity = db.Column(db.String(20))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

class MatchChatMessage(db.Model):
    __tablename__ = 'match_chat_message'

    id = db.Column(db.Integer, primary_key=True)
    match_chat_room_id = db.Column(db.Integer, db.ForeignKey('match_chat_room.id'), nullable=False)  # 채팅방 ID
    role = db.Column(db.String(20))  # mentee or mentor
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=db.func.current_timestamp())

class Lecture(db.Model):
    __tablename__ = 'lectures'
    
    lec_id = db.Column(db.Integer, primary_key=True)  # 기본 키
    hobby = db.Column(db.String(20), nullable=False)
    level = db.Column(db.String(20), nullable=False)
    name = db.Column(db.String(20), nullable=False)

class UserClick(db.Model):
    __tablename__ = 'user_clicks'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, nullable=False)
    lec_id = db.Column(db.Integer, db.ForeignKey('lectures.lec_id'), nullable=False)
    clicks = db.Column(db.Boolean, nullable=False, default=False)

class CommunityPost(db.Model):
    __tablename__ = 'community_post'

    id = db.Column(db.Integer, primary_key=True)  # 게시글 ID
    guest_id = db.Column(db.Integer, nullable=False)  # 게스트 또는 유저 ID
    question = db.Column(db.Text, nullable=False)  # 게시글의 질문 내용
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # 질문이 작성된 시간

class CommunityAnswer(db.Model):
    __tablename__ = 'community_answer'

    id = db.Column(db.Integer, primary_key=True)  # 답변 ID
    post_id = db.Column(db.Integer, db.ForeignKey('community_post.id', ondelete="CASCADE"), nullable=False)  # 질문 게시글의 ID
    guest_id = db.Column(db.Integer, nullable=True)  # 답변을 작성한 유저 또는 게스트의 ID
    answer = db.Column(db.Text, nullable=False)  # 답변 내용
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())  # 답변 작성 시간


## 라우트

# 회원가입 라우트
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        data = request.get_json()
        email = data['email']
        password = data['password']
        gender = data['gender']
        birthdate = data['birthdate']
        name = data['name']
        
        new_guest = Guest(email=email, password=password, gender=gender, birthdate=birthdate, name = name)
        db.session.add(new_guest)
        db.session.commit()
        
        logger.info('User created: %s', email)
        return jsonify({"message": "User created successfully!"}), 201
    else:  # 브라우저는 무조건 -> GET 요청에 대한 처리
        return jsonify({"message": "Please use POST to sign up."}), 200

# 로그인 라우트
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        # 이메일 및 비밀번호 존재 여부 확인
        if not email or not password:
            return jsonify({"message": "Email and password are required"}), 400
        
        # 데이터베이스에서 이메일로 사용자 검색
        user = Guest.query.filter_by(email=email).first()
        if user and user.password == password:
            logger.info('Login successful for user: %s', email)
            return jsonify({"message": "Login successful!", "guest_id": user.id}), 200  # 프론트한테 게스트 아이디 넘겨줌
        else:
            logger.warning('Login failed for user: %s', email)
            return jsonify({"message": "Invalid email or password"}), 401
    
    elif request.method == 'GET':
        # GET 요청에 대한 처리
        return jsonify({"message": "Please use POST to login."}), 200
    
# 설문조사 라우트
@app.route('/survey', methods=['GET', 'POST'])
def survey():
    if request.method == 'POST':
        data = request.get_json()
        guest_id = data['guest_id']
        role = data['role']
        activity = data['activity']
        gender = data['gender']
        age_group = data['age_group']
        location = data['location']
        activity_level = data['activity_level']
        
        new_survey = Survey(guest_id=guest_id, role=role, activity=activity,  gender=gender,
                            age_group=age_group, location=location, activity_level=activity_level)
        db.session.add(new_survey)
        db.session.commit()
        
        logger.info('Survey submitted: %s', guest_id)
        return jsonify({"message": "Survey submitted successfully!"}), 201
    else:  # GET 요청에 대한 처리
        return jsonify({"message": "Please use POST to submit a survey."}), 200



######## AI 멘토 ##########


def determine_level(difficulty_value):
    if difficulty_value == 1:  # '어렵다'
        return '초보자'
    elif difficulty_value == 2:  # '적당하다'
        return '중급자'
    elif difficulty_value == 3:  # '쉽다'
        return '고급자'
    return '초보자'  # 기본값


def identify_cuisine(text):
    text = text.lower()
    if '한식' in text:
        return '한식 요리'
    elif '양식' in text:
        return '양식 요리'
    return '요리'


def extract_learning_subject(text):
    # '을' 또는 '를' 조사 앞의 명사 추출
    match = re.search(r'(\b\w+)(?:을|를)\b', text)  # 조사 제거
    if match:
        noun = match.group(1)  # 명사만
        return noun
    return None

# 대화 히스토리 저장 함수    
def save_message(chat_room_id, role, content):
    new_message = AIChatMessage(ai_chat_room_id=chat_room_id, role=role, content=content)
    db.session.add(new_message)
    db.session.commit()

# 대화 히스토리 불러오기 함수
def get_chat_history(chat_room_id):
    return AIChatMessage.query.filter_by(ai_chat_room_id=chat_room_id).order_by(AIChatMessage.timestamp).all()


# 초반 개별화된 프롬프트 생성
def create_custom_prompt(hobby, weeks, level):
    if hobby == "요리":
        return (f"요리를 1주차부터 {weeks}주차까지의 과정으로 {level}단계에 맞게 주차별 요리 학습 계획을 제공하십시오. "
                "각 주차마다 하나의 대중적인 요리 이름만 포함해주세요."
                "라면이나 계란 후라이 같은 기본적인 음식은 제외해주세요."
                "음식에 관한 배경 설명은 안하셔도 됩니다. 한글만 사용하세요"
                "각 주차별 내용은 새로운 줄에서 시작하고, 주차별 내용 사이에 한 줄의 공백을 추가해 주세요. "
                "난이도는 현재 단계에 맞춰 점진적으로 어려워지게 해주세요.")
    else:
        return (f"{hobby}을(를) 1주차부터 {weeks}주차까지의 과정으로 {level}단계에 맞춰 주차별 학습 계획을 세워주세요. "
                "취미가 악기 연주와 관련된 것이라면, 악기 자체는 준비물 목록에서 제외해 주세요. "
                "필요한 준비물도 포함해주세요. "
                "각 주차별로 간단한 학습 계획을 1줄에서 2줄씩으로 설명해주세요."
                "각 주차별 내용은 새로운 줄에서 시작하고, 주차별 내용 사이에 한 줄의 공백을 추가해 주세요. ")

# 응답 생성
def get_response(user_input, chat_room_id):
    # 대화 히스토리 불러오기
    chat_history = get_chat_history(chat_room_id)
    messages = [{"role": message.role, "content": message.content} for message in chat_history]
    
    # 간결하게 대답하라는 지시 추가
    messages.append({"role": "system", "content": "간결하게 대답해줘"})

    # 사용자 입력 추가
    messages.append({"role": "user", "content": user_input})

    # OpenAI API 호출
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=messages
    )
    response_text = response['choices'][0]['message']['content']
    save_message(chat_room_id, "assistant", response_text)
    return response_text

def get_custom_prompt_response(custom_prompt):
    # OpenAI API 호출에 프롬프트 포함
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "assistant", "content": custom_prompt}
        ]
    )

    return response['choices'][0]['message']['content']


# AI 채팅방 생성 엔드포인트
@app.route('/create_ai_chat_room', methods=['POST'])
def create_ai_chat_room():
    data = request.get_json()
    guest_id = data.get('guest_id')
    is_ai_chatbot = data.get('is_ai_chatbot')

    if guest_id is None or is_ai_chatbot is None:
        return jsonify({'message': 'guest_id and is_ai_chatbot are required'}), 400

    if not is_ai_chatbot:
        return jsonify({'message': 'is_ai_chatbot must be true for this endpoint'}), 400

    new_chat_room = AIChatRoom(guest_id=guest_id)
    db.session.add(new_chat_room)
    db.session.commit()

    logger.info('AI chat room created for guest_id: %s', guest_id)
    
    return jsonify({'chat_room_id': new_chat_room.id}), 201


# 초기 질문 라우트
@app.route('/start_chat', methods=['POST'])
def start_chat():
    try:
        data = request.get_json()
        chat_room_id = data.get("chat_room_id")

        if not chat_room_id:    # Chat Room ID가 전달되었는지 확인
            return jsonify({"message": "Chat Room ID is required"}), 400

        chat_room = AIChatRoom.query.get(chat_room_id)
        if not chat_room:
            return jsonify({"message": "Chat Room ID does not exist"}), 404
        
        # 인사 메시지와 질문 메시지를 준비
        response = {
            "questions": [
                {"role": "assistant", "content": "안녕하세요, 반갑습니다. 당신의 AI 멘토입니다."},
                {"role": "assistant", "content": "무엇을 배우고 싶으신가요?"}
            ]
        }
        save_message(chat_room_id, "assistant", "안녕하세요, 반갑습니다. 당신의 AI 멘토입니다. 무엇을 배우고 싶으신가요?")

        return jsonify(response)
    except Exception as e:
        app.logger.error(f"Internal Server Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500



# 악기 관련 여부 판별
def classify_hobby(hobby):
    prompt = f"{hobby}은(는) 악기 관련 취미인가요? 네 또는 아니오로 대답해 주세요."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    answer = response['choices'][0]['message']['content'].strip().lower()
    return "네" in answer  # 악기 관련 여부를 판별

# 레벨 테스트 악보 설명 생성 함수
def create_sheet_music_description(hobby):
    prompt = f"{hobby}을(를) 보통 수준의 간단한 악보를 텍스트로 작성해 주세요. 음표와 간단한 연주 지침을 포함하며 , 4마디 정도의 클래식/포크(악기에 따라) 스타일로 작성해 주세요. 이 텍스트는 프론트엔드에서 실제 악보로 변환될 예정입니다."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']

# 악기 제외 나머지 레벨 테스트
def create_text_based_test(hobby):
    prompt = f"{hobby}에 대한 중간 난이도의 레벨 테스트 문제를 하나 작성해 주세요. 사용자가 혼자 해결할 수 있는 실습 과제 형식으로, 이 과제를 통해 사용자의 현재 수준을 평가할 수 있도록 해주세요."
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    return response['choices'][0]['message']['content']


# 챌린지 제공 함수
def create_plan_for_chat_room(level, chat_room_id, number):
    # 레벨에 따른 단계 범위 비율 정의

    # 레벨에 따른 단계 범위 비율 정의
    level_ranges = {
        1: (0, 0.40),  # 하
        2: (0.30, 0.70),  # 중
        3: (0.60, 1.00)   # 상
    }

    # 단계 비율을 가져옴
    if level not in level_ranges:
        return {"error": "잘못된 레벨입니다."}

    min_ratio, max_ratio = level_ranges[level]

    # 모든 요리 계획을 단계 기준으로 가져오고 스텝 값으로 오름차순 정렬
    all_plans = CookingPlan.query.order_by(CookingPlan.step).all()

    if not all_plans:
        return {"error": "요리 계획이 없습니다."}

    # 전체 단계 범위
    min_step = all_plans[0].step
    max_step = all_plans[-1].step

    # 레벨에 따른 단계 범위 설정
    min_step_value = min_step + (max_step - min_step) * min_ratio
    max_step_value = min_step + (max_step - min_step) * max_ratio

    # 단계 범위에 따라 필터링
    filtered_plans = [plan for plan in all_plans if min_step_value <= plan.step <= max_step_value]

    if not filtered_plans:
        return {"error": "선택된 단계 범위의 요리 계획이 없습니다."}

    # n개 항목을 랜덤으로 선택
    selected_plans = random.sample(filtered_plans, min(number, len(filtered_plans)))

    # 선택된 계획들을 step 값 기준으로 오름차순 정렬
    selected_plans.sort(key=lambda plan: plan.step)

    # 선택된 계획을 Plan 테이블에 추가
    for idx, plan in enumerate(selected_plans, start=1):
        new_plan = Plan(
            cooking_plan_id=plan.id,
            chat_room_id=chat_room_id,
            goal_number=idx,
            hobby='요리'
        )
        db.session.add(new_plan)

    db.session.commit()  # 선택된 계획들을 Plan 테이블에 저장

    return {"success": True}


# 사용자 응답 처리
@app.route('/chat', methods=['POST'])
def chat():
    data = request.get_json()
    chat_room_id = data.get("chat_room_id")
    user_message = data.get("message")

    if not chat_room_id:
        app.logger.error("Chat Room ID is missing in the request.")
        return jsonify({"message": "Chat Room ID is required"}), 400

    if not user_message:
        app.logger.error("Message is missing in the request.")
        return jsonify({"message": "Message is required"}), 400

    # 이전에 메시지를 저장하지 않고 검증
    chat_history = get_chat_history(chat_room_id)

    if len(chat_history) == 1:  # 첫 번째 질문에 대한 답변이 완료된 경우
        hobby = extract_learning_subject(user_message)
        if hobby:
            if hobby == '요리':
                # '요리'일 경우 '한식 요리' 또는 '양식 요리'로 세분화 / 이외는 '요리'
                cuisine = identify_cuisine(user_message)
                activity = cuisine
            else:
                activity = hobby

            # 챗룸의 activity 필드 업데이트
            chat_room = AIChatRoom.query.get(chat_room_id)
            if chat_room:
                chat_room.activity = activity
                db.session.commit()
                save_message(chat_room_id, "assistant", "레벨테스트를 진행하겠습니다. 시작 버튼을 눌러 진행해주세요.")  # 올바른 경우에만 저장
                return jsonify({"response": "레벨테스트를 진행하겠습니다. 시작 버튼을 눌러 진행해주세요."})

    #     # 난이도 테스트 문제 생성
    #         is_instrument = classify_hobby(hobby)  # 악기 관련 여부를 판별

    #         if is_instrument:
    #         # 악기 관련 레벨 테스트 (악보 생성)
    #             sheet_music_description = create_sheet_music_description(hobby)
    #             save_message(chat_room_id, "user", user_message)  # 올바른 경우에만 저장
    #             save_message(chat_room_id, "assistant", "아하! {hobby}을(를) 배우고 싶으시군요.\n 난이도 테스트를 해보시고 '어렵다', '적당하다', '쉽다' 중에 하나를 선택해 주세요.")
    #             return jsonify({"response": "아하! {hobby}을(를) 배우고 싶으시군요.\n 난이도 테스트를 해보시고 '어렵다', '적당하다', '쉽다' 중에 하나를 선택해 주세요.", "sheet_music_description": sheet_music_description})  # 프론트가 설명을 받아 악보로 전환
    #         else:
    #             # 악기가 아닌 경우 텍스트 기반 테스트 제공
    #             text_test =  " "   # 레시피에 대한 스텝 제공

    #             save_message(chat_room_id, "user", user_message)  # 올바른 경우에만 저장
    #             save_message(chat_room_id, "assistant", "아하! {hobby}을(를) 배우고 싶으시군요.\n 난이도 테스트를 해보시고 '어렵다', '적당하다', '쉽다' 중에 하나를 선택해 주세요.")
    #             return jsonify({"response": "아하! {hobby}을(를) 배우고 싶으시군요.\n 난이도 테스트를 해보시고 '어렵다', '적당하다', '쉽다' 중에 하나를 선택해 주세요.", "text_test": text_test})

    #     else:
    #         # 잘못된 입력 처리 (메시지를 저장하지 않음)
    #         return jsonify({"response": "취미를 정확하게 입력해 주세요."})


    # if len(chat_history) == 3:  # 두 번째 질문에 대한 답변이 완료된 경우
    #     try:
    #         difficulty_value = int(user_message)  # 난이도 값을 숫자로 변환
    #     except ValueError:
    #         return jsonify({"response": "유효한 난이도 값을 입력해 주세요. (1: 어렵다, 2: 적당하다, 3: 쉽다)"})
        
    #     difficulty_value = determine_level(difficulty_value)
    #     save_message(chat_room_id, "user", user_message)  # 올바른 경우에만 저장

    #     save_message(chat_room_id, "assistant","현재 상태는 %s입니다. 원하시는 챌린지의 갯수를 눌러주세요." %difficulty_value)
    #     return jsonify({"response": "현재 상태는 %s입니다. 원하시는 챌린지의 갯수를 눌러주세요." %difficulty_value})
       

    # if len(chat_history) == 5:  # 세 번째 질문에 대한 답변이 완료된 경우
    #     number = int(user_message)   # 챌린지 갯수
    #     if number is None:
    #         return jsonify({"response": "숫자를 입력해 주세요."})
       
    #     level = determine_level(difficulty_value)
    #     hobby = extract_learning_subject(chat_history[1].content)
    #     custom_prompt = create_custom_prompt(hobby, number, level)

    #     if hobby == '요리':

    #         # 해당 레벨과 주차 수에 맞는 랜덤 요리 계획 생성
    #         create_plan_for_chat_room(level, chat_room_id, number)

    #         # 해당 채팅룸에 속하는 모든 plan 항목 가져오기
    #         plans = Plan.query.filter_by(chat_room_id=chat_room_id).order_by(Plan.goal_number).all()

    #         response_data = []
    #         for plan in plans:
    #             # 각 plan의 외래키로 CookingPlan 항목 가져오기
    #             cooking_plan = CookingPlan.query.get(plan.cooking_plan_id)

    #             response_data.append({
    #                 "goal_number": plan.goal_number,
    #                 "dish_name": cooking_plan.dish_name,
    #             })

    #         save_message(chat_room_id, "user", user_message)
    #         save_message(chat_room_id, "assistant", response_data)

    #         return jsonify({"response": response_data})
            
        # 다른 취미(임시로)
        # else:
        #     # 프롬프트를 `assistant` 역할로서 응답 생성
        #     response_text = get_custom_prompt_response(custom_prompt)
        #     save_message(chat_room_id, "user", user_message) 
        #     save_message(chat_room_id, "assistant", response_text)
        #     return jsonify({"response": response_text})


    # 그 외의 경우: OpenAI API 호출
    response_text = get_response(user_message, chat_room_id)
    save_message(chat_room_id, "user", user_message)  # 기본적으로 사용자 메시지 저장
    save_message(chat_room_id, "assistant", response_text)
    return jsonify({"response": response_text})


# 레벨 테스트 문제 반환 라우터
@app.route('/get_level_test', methods=['GET'])
def get_level_test():
    chat_room_id = request.args.get('chat_room_id')
    if not chat_room_id:
        return jsonify({"message": "Chat Room ID is required"}), 400

    # 해당 chat_room_id의 activity (취미) 가져오기
    chat_room = AIChatRoom.query.get(chat_room_id)
    if not chat_room or not chat_room.activity:
        return jsonify({"message": "No activity found for the chat room"}), 404

    hobby = chat_room.activity

    # 해당 취미의 레벨 테스트 문제 5개 가져오기
    questions = LevelTest.query.filter_by(hobby=hobby).limit(5).all()
    if not questions:
        return jsonify({"message": f"No questions found for the hobby: {hobby}"}), 404

    response = []
    for question in questions:
        response.append({
            'question_number': question.question_number,
            'question': question.question
        })

    return jsonify({"questions": response})


# 레벨 테스트 채점 & 레벨 지정 라우트
@app.route('/submit_level_test', methods=['POST'])
def submit_level_test():
    data = request.get_json()
    chat_room_id = data.get('chat_room_id')
    user_answers = data.get('user_answers')  # 사용자가 선택한 답을 번호로 전달

    if not chat_room_id or not user_answers or len(user_answers) != 5:
        return jsonify({"message": "Invalid data"}), 400

    # 해당 chat_room_id의 activity (취미) 가져오기
    chat_room = AIChatRoom.query.get(chat_room_id)
    if not chat_room or not chat_room.activity:
        return jsonify({"message": "No activity found for the chat room"}), 404

    hobby = chat_room.activity

    # 해당 취미의 모든 레벨 테스트 문제 가져오기
    questions = LevelTest.query.filter_by(hobby=hobby).all()
    if not questions:
        return jsonify({"message": "No questions found for the selected hobby"}), 404

    score = 0
    for question in questions:
        question_num = question.question_number
        correct_answer = question.answer

        # 사용자가 제출한 답과 정답 비교
        if question_num in user_answers and user_answers[question_num] == correct_answer:
            score += 1

    # 레벨 매기기 (4~5 고급자, 2-3은 중급자, 0-1은 초급자)
    if score >= 4:
        level = "고급"
    elif 2 <= score < 4:
        level = "중급"
    else:
        level = "초급"

    return jsonify({"score": score, "level": level})


## 해당 채팅룸 챌린지 배정하기
@app.route('/goal', methods=['GET'])
def get_weekly_goal():
    chat_room_id = request.args.get("chat_room_id") 
    number = request.args.get("challenge_number", type=int)  # 챌린지 개수 받기
    level = request.args.get("level", type=int)   # 유저 레벨 

    if not chat_room_id:
        return jsonify({"message": "Chat Room ID is required"}), 400

    if number is None:
        return jsonify({"message": "number is required"}), 400

    if level is None:
        return jsonify({"message": "Level is required"}), 400

    
    # 해당 chat_room_id로 chat_room 레코드를 조회
    chat_room = db.session.query(AIChatRoom).filter_by(id=chat_room_id).first()

    # 조회된 chat_room의 activity가 '요리'인지 확인
    if chat_room and chat_room.activity in ['요리', '한식 요리', '양식 요리']:

        # 해당 레벨과 개수에 맞는 랜덤 요리 계획 생성
        create_plan_for_chat_room(level, chat_room_id, number)

        return jsonify({"message": "챌린지가 성공적으로 생성되었습니다."}), 200
    else:
        return jsonify({"message": "요리에 대한 챌린지만 존재합니다."}), 400
    
        

# 해당 챌린지에 대한 정보 반환
@app.route('/Challenge', methods=['GET'])
def get_goal_info():
    chat_room_id = request.args.get("chat_room_id")
    goal_number = request.args.get("goal_number", type=int)

    if not chat_room_id:
        return jsonify({"message": "Chat Room ID is required"}), 400

    if goal_number is None:
        return jsonify({"message": "Goal number is required"}), 400

    # 해당 채팅룸과 목표 번호에 해당하는 plan 항목 가져오기
    plan = Plan.query.filter_by(chat_room_id=chat_room_id, goal_number=goal_number).first()

    if not plan:
        return jsonify({"message": "해당 챌린지를 찾을 수 없습니다."}), 404
    
    # 해당 Plan에 대해 CookingPlan 정보 가져오기
    cooking_plan = CookingPlan.query.get(plan.cooking_plan_id)

    if not cooking_plan:
        return jsonify({"message": f"Plan ID {plan.id}에 해당하는 요리 계획을 찾을 수 없습니다."}), 404

    # 해당 CookingPlan에 연결된 Method 정보를 가져오기
    methods = Method.query.filter_by(cooking_plan_id=cooking_plan.id).order_by(Method.step_number).all()

    # Method 정보를 담을 리스트
    method_details = [{
        "step_number": method.step_number,
        "description": method.description
    } for method in methods]

    # CookingPlan의 정보와 그에 해당하는 Method 딕셔너리를 담은 리스트
    plan_detail = {       
        "plan_id": plan.id,
        "goal_number": plan.goal_number,
        "cooking_plan": {
            "id": cooking_plan.id,
            "dish_name": cooking_plan.dish_name,    # 요리 이름
            "ingredients": cooking_plan.ingredients,    # 재료
            "tools": cooking_plan.tools,    # 도구
            "methods": method_details  # Method 정보를 담은 리스트 
        }
    }

    # 특정 goal_number에 대한 plan 정보를 반환
    return jsonify({"plan": plan_detail}), 200



#### 다른 취미들 챌린지

def save_weekly_goals_and_tasks(chat_room_id, detailed_description):
    # 주차별 설명을 분리하는 정규 표현식
    week_sections = re.split(r'(\d+주차:)', detailed_description)

    # 주차 번호와 내용을 묶기
    it = iter(week_sections)
    week_sections = [(week.strip(), next(it).strip()) for week in it if week.strip()]

    for week_number_text, section in week_sections:
        week_number = int(week_number_text.replace('주차:', '').strip())

        # 첫 줄이 "N주차: 목표 설명" 같은 형태이므로 이를 기준으로 목표를 추출
        lines = section.split("\n")
        goal = lines[0].strip()  # 주차별 설명을 목표로 저장

        # weekly_tasks 테이블에 저장
        weekly_task = WeeklyTask(
            chat_room_id=chat_room_id,
            week_number=week_number,
            goal=goal
        )
        db.session.add(weekly_task)

    db.session.commit()

# 기존 설명에 대한 구체적인 설명 (화면 전환 되고나서 처음에 한번만 이거 쓰면 됨)
@app.route('/generate_detailed_description', methods=['POST'])
def generate_detailed_description():
    try:
        data = request.get_json()
        chat_room_id = data.get("chat_room_id")
        response_text = data.get("lastMessage")

        # chat_room_id 확인
        if chat_room_id is None:
            return jsonify({"message": "Chat Room ID is required"}), 400
        
        # response_text 확인
        if response_text is None:
            return jsonify({"message": "Response text is required"}), 400
        
        # 구체적인 설명을 위한 프롬프트 생성
        prompt = (
            f"기존 설명: {response_text}. "
            "이 설명을 바탕으로, 주차별로 추가적인 세부 사항과 구체적인 정보를 추가하여 자세한 설명을 작성해 주세요. "
            "각 주차별 목표는 기존 설명과 동일하게 유지되어야 합니다. "
            "방법이나 과정을 설명해주세요"
            "난이도와 몇 주차인지는 기존 설명에 맞춰 그대로 유지해 주세요."
            "각 주차별 내용은 새로운 줄에서 시작하고, 주차별 내용 사이에 한 줄의 공백을 추가해 주세요. "
        )
        
        detailed_description = get_custom_prompt_response(prompt)
        save_message(chat_room_id, "assistant", detailed_description)

        #  주차별로 설명 파싱 및 저장
        save_weekly_goals_and_tasks(chat_room_id, detailed_description)
        return jsonify({"detailed_description": detailed_description})
    
    except Exception as e:
        app.logger.error(f"Internal Server Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500


# 대화 기록 목록 라우트
@app.route('/ai_chat_history/<int:chat_room_id>', methods=['GET'])
def get_ai_chat_history(chat_room_id):
    messages = get_chat_history(chat_room_id)
    
    # 메시지를 JSON으로 변환
    chat_history = [
        {
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for message in messages
    ]
    
    # 클라이언트로 JSON 응답 반환
    return jsonify(chat_history)


# 취미 대상 반환 라우트
@app.route('/get_hobby_target', methods=['GET'])
def get_hobby_target():
    chat_room_id = request.args.get('chat_room_id')

    if not chat_room_id:
        return jsonify({"message": "Chat Room ID is required"}), 400

    chat_room = AIChatRoom.query.get(chat_room_id)
    
    if not chat_room:
        return jsonify({"message": "Chat Room not found"}), 404

    hobby_target = chat_room.activity

    return jsonify({"hobby_target": hobby_target})


######### 학습 파트 #############


@app.route('/weekly_task_description', methods=['GET'])
def get_weekly_task_description():
    chat_room_id = request.args.get("chat_room_id")
    week_number = request.args.get("week_number", type=int)
    
    if not chat_room_id or week_number is None:
        return jsonify({"message": "Chat Room ID and week number are required"}), 400

    weekly_task = WeeklyTask.query.filter_by(chat_room_id=chat_room_id, week_number=week_number).first()

    if not weekly_task:
        return jsonify({"message": "No tasks found for the given chat room ID and week number"}), 404

    # 주차별 목표에 대해 추가 설명을 요청하는 프롬프트 생성
    prompt = (
        f"주어진 주차별 목표: '{weekly_task.goal}'. "
        "이 목표를 달성하기 위한 과정이나 방법을 상세히 설명해 주세요."
    )

    # GPT에게 상세 설명 요청
    detailed_goal_description = get_custom_prompt_response(prompt)
    
    # 생성된 상세 설명을 저장
    save_message(chat_room_id, "assistant", detailed_goal_description)

    return jsonify({"weekly_task_description": detailed_goal_description})


@app.route('/tasks', methods=['POST'])
def assign_tasks():
    try:
        data = request.get_json()
        chat_room_id = data.get("chat_room_id")
        week_number = data.get("week_number", type=int)

        if chat_room_id is None or week_number is None:
            return jsonify({"message": "Chat Room ID and week number are required"}), 400

        # weekly_tasks 테이블에서 해당 주차의 목표와 설명을 가져오기
        weekly_task = WeeklyTask.query.filter_by(chat_room_id=chat_room_id, week_number=week_number).first()
        if not weekly_task:
            return jsonify({"message": "No tasks found for the given chat room ID and week number"}), 404

        # 주차별 설명에 기반하여 소과제 리스트 생성
        prompt = (
            f"주어진 주차별 목표: '{weekly_task.goal}'. "
            "이 설명을 바탕으로, 사용자가 목표를 달성하기 위해 수행할 수 있는 소과제들을 생성해 주세요. "
            "목표를 달성하는 데 필요한 단계를 포함해야 합니다. 소과제는 3개 이상에서 6개 이하로 작성해 주세요."
        )

        # GPT에게 소과제 생성 요청
        tasks_description = get_custom_prompt_response(prompt)
        tasks = [task.strip() for task in tasks_description.split('\n') if task.strip()]

        # 소과제를 weekly_tasks_details 테이블에 저장
        for task in tasks:
            if task:
                weekly_task_detail = WeeklyTaskDetail(
                    chat_room_id=chat_room_id,
                    week_number=week_number,
                    task=task
                )
                db.session.add(weekly_task_detail)

        db.session.commit()

        # 생성된 소과제들을 조회
        tasks = WeeklyTaskDetail.query.filter_by(chat_room_id=chat_room_id, week_number=week_number).all()
        tasks_list = [
            {
                'id': task.id,
                'task': task.task,
                'created_at': task.created_at.strftime("%Y-%m-%d %H:%M:%S")
            }
            for task in tasks
        ]

        return jsonify({"tasks": tasks_list})

    except Exception as e:
        app.logger.error(f"Internal Server Error: {e}")
        return jsonify({"message": "Internal Server Error"}), 500



###############   1:1 매칭 파트   ##############


# 멘토-멘티 데이터를 불러오는 함수
def load_data():
    try:
        # Survey와 Guest 테이블을 조인하여 필요한 데이터 가져오기
        results = db.session.query(Survey, Guest).join(Guest, Survey.guest_id == Guest.id).all()

        # Survey 객체를 딕셔너리로 변환
        survey_list = [
            {
                "id": survey.id,
                "guest_id": survey.guest_id,
                "role": survey.role,
                "activity": survey.activity,
                "gender": survey.gender,
                "age_group": survey.age_group,
                "location": survey.location,
                "activity_level": survey.activity_level,
                "name": guest.name  # Guest의 name 필드 추가
            }
            for survey, guest in results
        ]
        return survey_list
    except Exception as e:
        app.logger.error(f"Error loading data: {e}")
        return []

# 특정 멘티 정보를 불러오는 함수
def get_mentee_info(mentee_id):
    try:
       # Survey와 Guest 테이블을 조인하여 멘티 정보 쿼리
        result = db.session.query(Survey, Guest).join(Guest, Survey.guest_id == Guest.id).filter(Survey.guest_id == mentee_id, Survey.role == '멘티').first()

        # 멘티 정보가 존재하면 딕셔너리 형태로 변환
        if result:
            mentee, guest = result
            mentee_info = {
                "id": mentee.id,
                "guest_id": mentee.guest_id,
                "role": mentee.role,
                "activity": mentee.activity,
                "gender": mentee.gender,
                "age_group": mentee.age_group,
                "location": mentee.location,
                "activity_level": mentee.activity_level,
                "name": guest.name  # Guest의 name 필드 추가
            }
            return mentee_info
        else:
            return None
    except Exception as e:
        app.logger.error(f"Error retrieving mentee info: {e}")
        return None


# 매칭에 필요한 유틸리티 함수 추가
def is_match(value_list, target_value):
    return target_value in value_list


# 매칭 함수
def match_mentee(mentee, mentors):
    try:
        
        # 같은 활동을 가진 멘토들 필터링
        mentors = mentors[mentors['activity'].apply(lambda x: mentee['activity'] in x)]  # 취미가 같은 멘토 필터링
        if mentors.empty:
            return []

        mentors['score'] = 0

        # 성별 매칭
        mentors.loc[mentors['gender'] == mentee['gender'], 'score'] += 1

        # 나이대 매칭
        mentors.loc[mentors['age_group'] == mentee['age_group'], 'score'] += 1

        # 지역 매칭
        mentors['location_match'] = mentors['location'].apply(
            lambda mentor_locs: any(loc in mentee['location'] for loc in mentor_locs)
        )
        mentors.loc[mentors['location_match'], 'score'] += 1
        

        # 활동 수준 매칭
        for idx, mentor in mentors.iterrows():
            mentor_levels = mentor['activity_level']
            mentee_level = mentee['activity_level']
            
            if is_match(mentor_levels, '고급'):
                mentors.at[idx, 'score'] += 1
            elif is_match(mentor_levels, '중급') and mentee_level in ['초급', '중급']:
                mentors.at[idx, 'score'] += 1
            elif is_match(mentor_levels, '초급') and mentee_level == '초급':
                mentors.at[idx, 'score'] += 1


        # 점수 기준으로 정렬 후 상위 3명 선택
        top_mentors = mentors.sort_values(by='score', ascending=False).head(3)
        return top_mentors

    except Exception as e:
        app.logger.error(f"Error in matching mentee: {e}")
        return []


# 멘토 추천 라우트
@app.route('/recommend_match', methods=['POST'])
def recommend_match():
    data = request.get_json()
    guest_id = data.get('guest_id')  # 프론트 -> 멘토를 추천 받을 유저의 게스트 아이디를 줘야됨

    if not guest_id:
        return jsonify({"message": "guest_id is required"}), 400

    # 멘티 정보 불러오기
    mentee_info = get_mentee_info(guest_id)
    if not mentee_info:
        return jsonify({"message": f"Mentee with guest_id {guest_id} not found"}), 404
    
    # 전체 데이터 불러오기
    data = load_data()
    if not data:
        return jsonify({"message": "No data found"}), 500

    # 멘토 데이터 필터링
    mentors = [d for d in data if d['role'] == '멘토']

    # 매칭 수행
    top_mentors = match_mentee(mentee_info, mentors)
    if not top_mentors:
        return jsonify({"message": "No suitable mentors found"}), 404

    # 매칭된 멘토 정보를 포맷팅하여 반환
    return jsonify({"mentors": top_mentors}), 200


# 멘토-멘티 매칭 라우트
@app.route('/match', methods=['POST'])
def match():
    data = request.get_json()
    mentee_id = data.get('mentee_id')
    mentor_id = data.get('mentor_id')

    if not mentee_id or not mentor_id:
        return jsonify({"message": "Both mentee_id and mentor_id are required"}), 400

    try:
        # 매칭 데이터베이스에 저장
        new_matching = Matching(
            mentee_id=mentee_id,
            mentor_id=mentor_id
        )
        db.session.add(new_matching)
        db.session.commit()
        return jsonify({"message": "Matching successful"}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating match: {e}")
        return jsonify({"message": "An error occurred while creating the match"}), 500


# 멘토-멘티 채팅방 생성  
@app.route('/create_chat_room', methods=['POST'])
def create_chat_room():
    data = request.get_json()
    mentee_id = data.get('mentee_id')
    mentor_id = data.get('mentor_id')
    activity = data.get('activity')

    if not mentee_id or not mentor_id or not activity:
        return jsonify({'message': 'mentee_id, mentor_id, and activity are required'}), 400

    try:
        # 매칭 정보가 존재하는지 확인
        match = Matching.query.filter_by(mentee_id=mentee_id, mentor_id=mentor_id).first()
        if not match:
            return jsonify({'message': 'No matching found for the provided mentee_id and mentor_id'}), 404

        # 활동 정보 가져오기
        mentee_info = get_mentee_info(mentee_id)
        if not mentee_info:
            return jsonify({'message': 'Mentee information not found'}), 404
        activity = mentee_info['activity']

         # 새로운 채팅방 생성
        new_chat_room = MatchChatRoom(
            mentee_id=mentee_id,
            mentor_id=mentor_id,
            activity=activity,  # 활동 정보 저장
        )
        db.session.add(new_chat_room)
        db.session.commit()

        logger.info(f'New chat room created for mentee_id: {mentee_id}, mentor_id: {mentor_id}, activity: {activity}')

        return jsonify({'match_chat_room_id': new_chat_room.id}), 201
    except Exception as e:
        db.session.rollback()
        app.logger.error(f"Error creating chat room: {e}")
        return jsonify({'message': 'An error occurred while creating the chat room'}), 500


# 매칭방 메세지 저장 함수
def save_match_message(chat_room_id, role, content):
    new_message = MatchChatMessage(match_chat_room_id=chat_room_id, role=role, content=content)
    db.session.add(new_message)
    db.session.commit()

# 멘토-멘티 채팅 메시지 전송
@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.get_json()
    match_chat_room_id = data.get('match_chat_room_id')
    role = data.get('role')  # 멘티 or 멘토
    message_content = data.get('message')

    if not match_chat_room_id or not role or not message_content:
        return jsonify({'message': 'match_chat_room_id, role, and message are required'}), 400

    if role not in ['멘티', '멘토']:
        return jsonify({'message': 'Invalid role. Must be either "멘티" or "멘토".'}), 400
    
    # 메시지 저장
    save_match_message(match_chat_room_id, role, message_content)

    return jsonify({'message': 'Message sent successfully'}), 200


# 대화 기록 불러오기 함수
def get_match_chat_history(match_chat_room_id):
    return MatchChatMessage.query.filter_by(match_chat_room_id=match_chat_room_id).order_by(MatchChatMessage.timestamp).all()

# 대화 기록 목록 라우트
@app.route('/match_chat_history/<int:match_chat_room_id>', methods=['GET'])
def get_match_chat_history_route(match_chat_room_id):
    messages = get_match_chat_history(match_chat_room_id)
    
    # 메시지를 JSON으로 변환
    chat_history = [
        {
            'role': message.role,
            'content': message.content,
            'timestamp': message.timestamp.strftime("%Y-%m-%d %H:%M:%S")
        }
        for message in messages
    ]
    
    # 클라이언트로 JSON 응답 반환
    return jsonify(chat_history)


######## 부가적 기능 ##########


# 강의, 클릭 데이터 가져오기
def get_user_clicks_and_lectures(hobby, level):
    query = db.session.query(UserClick, Lecture).join(Lecture, UserClick.lec_id == Lecture.lec_id).filter(
        Lecture.hobby == hobby, Lecture.level == level
    ).all()
    
    clicks_data = [{'user_id': uc.user_id, 'clicks': uc.clicks, 'lec_id': uc.lec_id} for uc, _ in query]
    return clicks_data

# 매트릭스 생성
def create_user_video_matrix(clicks_data):
    user_dict = {}
    lec_dict = {}
    for data in clicks_data:
        user_dict.setdefault(data['user_id'], {})
        lec_dict.setdefault(data['lec_id'], {})
        user_dict[data['user_id']][data['lec_id']] = data['clicks']
    
    user_ids = list(user_dict.keys())
    lec_ids = list(lec_dict.keys())
    user_matrix = np.zeros((len(user_ids), len(lec_ids)))
    
    user_id_to_index = {user_id: idx for idx, user_id in enumerate(user_ids)}
    lec_id_to_index = {lec_id: idx for idx, lec_id in enumerate(lec_ids)}
    
    for user_id, lec_dict in user_dict.items():
        for lec_id, clicks in lec_dict.items():
            user_matrix[user_id_to_index[user_id], lec_id_to_index[lec_id]] = clicks
    
    return user_matrix, user_ids, lec_ids

# 유사도 계산
def calculate_similarity(user_matrix):
    user_similarity = cosine_similarity(user_matrix)
    return user_similarity

# 특정 사용자와 유사한 사용자 찾기
def get_similar_users(user_id, user_similarity, user_ids, n=5):
    if user_id not in user_ids:
        return []
    user_idx = user_ids.index(user_id)
    similar_users = np.argsort(-user_similarity[user_idx])[1:n+1]
    return [user_ids[idx] for idx in similar_users]

# 추천 강의
def recommend_videos_for_user(user_id, user_matrix, user_similarity, user_ids, lec_ids, n=5):
    if user_id not in user_ids:
        most_clicked_videos = np.sum(user_matrix, axis=0)
        return [lec_ids[idx] for idx in np.argsort(-most_clicked_videos)[:n]]
    
    similar_users = get_similar_users(user_id, user_similarity, user_ids, n)
    similar_users_idx = [user_ids.index(u) for u in similar_users]
    similar_users_videos = np.sum(user_matrix[similar_users_idx], axis=0)
    user_idx = user_ids.index(user_id)
    user_videos = user_matrix[user_idx]
    recommendations = [lec_ids[idx] for idx in np.argsort(-similar_users_videos) if user_videos[idx] == 0]
    
    return recommendations[:n]


## 강의 추천 라우트
@app.route('/recommend_course', methods=['POST'])
def recommend_course():
    data = request.json
    if 'user_id' not in data or 'hobby' not in data or 'level' not in data:
        return jsonify({'message': 'Missing fields'}), 400
    
    user_id = data['user_id']
    hobby = data['hobby']
    level = data['level']
    
    clicks_data = get_user_clicks_and_lectures(hobby, level)
    user_matrix, user_ids, lec_ids = create_user_video_matrix(clicks_data)
    
    if len(user_ids) == 0:
        return jsonify({'message': 'No data available for the given hobby and level'}), 404
    
    user_similarity = calculate_similarity(user_matrix)
    recommendations = recommend_videos_for_user(user_id, user_matrix, user_similarity, user_ids, lec_ids)
    
    return jsonify({'추천 강의': recommendations})


### 커뮤니티

# 질문 작성 라우트
@app.route('/community_post', methods=['POST'])
def create_post():
    data = request.get_json()
    question = data.get('question')
    guest_id = data.get('guest_id')  # 질문을 작성한 게스트의 ID

    if not question or not guest_id:
        return jsonify({"message": "Question or Guest ID is missing"}), 400

    # 질문을 커뮤니티 테이블에 저장
    new_post = CommunityPost(guest_id=guest_id, question=question)
    db.session.add(new_post)
    db.session.commit()

    return jsonify({"post_id": new_post.id, "message": "Question posted successfully"}), 201


# AI 답변 라우트
@app.route('/community_ai', methods=['POST'])
def ai_answer():
    data = request.get_json()
    post_id = data.get('post_id')

    if not post_id:
        return jsonify({"message": "post_id is missing"}), 400

    # DB에서 post_id로 질문 조회
    post = CommunityPost.query.get(post_id)
    
    if not post:
        return jsonify({"message": "Post not found"}), 404

    question = post.question  # 질문 내용 가져오기

    # OpenAI에게 질문 전달
    prompt = f"""
    사용자가 게시판에 올린 질문입니다. 아래 질문에 대해 간결하고 정확한 답변을 작성해주세요.

    질문: "{question}"

    답변은 간결하게 작성해 주시고, 필요하다면 추가적인 설명이나 배경 지식도 함께 제공해 주세요.
    """

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}]
    )
    
    answer = response['choices'][0]['message']['content']

    # AI 답변을 CommunityAnswer 테이블에 저장
    new_answer = CommunityAnswer(post_id=post.id, guest_id=None, answer=answer)
    db.session.add(new_answer)
    db.session.commit()

    # 답변을 반환하거나 저장된 정보를 전달
    return jsonify({"answer": answer})


# 유저 답변 작성 라우트
@app.route('/community_user', methods=['POST'])
def user_answer():
    data = request.get_json()
    post_id = data.get('post_id')
    guest_id = data.get('guest_id')  # 답변을 작성한 유저 또는 게스트의 ID
    answer = data.get('answer')  # 유저가 작성한 답변 내용

    if not post_id or not guest_id or not answer:
        return jsonify({"message": "post_id, guest_id or answer 중에 하나 없음"}), 400

    # DB에서 post_id로 질문 조회
    post = CommunityPost.query.get(post_id)

    if not post:
        return jsonify({"message": "Post not found"}), 404

    # 유저의 답변을 CommunityAnswer 테이블에 저장
    new_answer = CommunityAnswer(post_id=post_id, guest_id=guest_id, answer=answer)
    db.session.add(new_answer)
    db.session.commit()

    # 성공 메시지와 답변 ID 반환
    return jsonify({"answer_id": new_answer.id, "message": "Answer posted successfully"}), 201


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
