import openai

# 테스트

openai.api_key = 'sk-mentos-qHLdPTiXoYsq42J13McDT3BlbkFJZvXpl4ImtXbSi1eUzFEb'  # 우리 키
# 모델로 간단한 질문 테스트
response = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",  # 또는 gpt-4
    messages=[
        {"role": "system", "content": "당신은 전문적인 지식을 가진 멘토입니다."},  # 목적 
        {"role": "user", "content": "기타 초보자가 연습할 곡을 추천해 주고 각 곡마다 몇 번 연습해야 적합할지 알려줘"} # 질문
    ],
    temperature=0.7,  # 창의성
    max_tokens=300,   # 최대 토큰수 제한
    n=1 
)

# 응답 출력
print(response.choices[0].message['content'])   # 대답들 중 첫번째
