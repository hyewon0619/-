import openai
import pandas as pd
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String, Text, Numeric
import re

# OpenAI API 키 설정
openai.api_key = 'sk-mentos-qHLdPTiXoYsq42J13McDT3BlbkFJZvXpl4ImtXbSi1eUzFEb'

# 데이터베이스 설정
DATABASE_URI = 'mysql+pymysql://admin:today0430@database-1.cva6yg8oenlg.ap-northeast-2.rds.amazonaws.com/mentosdb'
engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

Base = declarative_base()

class CookingPlan(Base):
    __tablename__ = 'cooking_plan'

    id = Column(Integer, primary_key=True, autoincrement=True)
    dish_name = Column(String(100), nullable=False)
    ingredients = Column(Text, nullable=False)
    tools = Column(Text, nullable=False)
    method = Column(Text, nullable=False)
    step = Column(Numeric(8, 4), nullable=True)

# OpenAI API를 통해 요리 정보 가져오기
def get_recipe_info(dish_name):
    prompt = f"요리 이름은 {dish_name} 입니다. 이 요리에 대한 재료, 도구, 방법을 각각 알려주세요. "\
              "출력 형식은 다음과 같아야 합니다:\n"\
              "재료:\n[재료 목록]\n"\
              "도구:\n[도구 목록]\n"\
              "방법:\n[조리 방법]"
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "요리에 대한 정보를 제공합니다."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            temperature=0.5
        )
    except Exception as e:
        print(f"Error with OpenAI API request: {e}")
        return "Unknown", "Unknown", "Unknown"

    answer = response.choices[0].message['content'].strip()
    
    # 데이터 파싱
    ingredients_match = re.search(r'재료:\n(.*?)(?=\n도구:|\n방법:|$)', answer, re.DOTALL)
    tools_match = re.search(r'도구:\n(.*?)(?=\n방법:|$)', answer, re.DOTALL)
    method_match = re.search(r'방법:\n(.*)', answer, re.DOTALL)
    
    ingredients = ingredients_match.group(1).strip() if ingredients_match else "Unknown"
    tools = tools_match.group(1).strip() if tools_match else "Unknown"
    method = method_match.group(1).strip() if method_match else "Unknown"

    # 불필요한 '-' 제거 및 쉼표로 구분
    ingredients = re.sub(r'^\s*-\s*', '', ingredients, flags=re.MULTILINE).strip()
    tools = re.sub(r'^\s*-\s*', '', tools, flags=re.MULTILINE).strip()
    method = method.strip()
    
    # 쉼표로 구분된 문자열로 변환
    ingredients = ', '.join(ingredient.strip() for ingredient in ingredients.split('\n') if ingredient.strip())
    tools = ', '.join(tool.strip() for tool in tools.split('\n') if tool.strip())
    
    return ingredients, tools, method

# 현재까지 처리된 행 수 조회
def get_processed_row_count(session):
    return session.query(CookingPlan).count()

# Excel 파일에서 요리 이름 읽고 데이터베이스에 저장
def process_file(file_path):
    try:
        df = pd.read_excel(file_path)
    except Exception as e:
        print(f"Error reading Excel file: {e}")
        return

    session = Session()  # 세션 시작
    
    try:
        processed_row_count = get_processed_row_count(session)
        start_index = processed_row_count
        total_rows = len(df)
        
        for index, row in df.iloc[start_index:].iterrows():
            dish_name = row['요리 이름']

            try:
                ingredients, tools, method = get_recipe_info(dish_name)

                new_plan = CookingPlan(
                    dish_name=dish_name,
                    ingredients=ingredients,
                    tools=tools,
                    method=method,
                    step=None
                )

                session.add(new_plan)
            except Exception as e:
                print(f"Error processing dish {dish_name}: {e}")
                
        session.commit()
        print("Recipes updated successfully")
    except Exception as e:
        print(f"Error committing to database: {e}")
        session.rollback()
    finally:
        session.close()  # 세션 닫기

if __name__ == '__main__':
    file_path = '/Users/SAMSUNG/Desktop/한이음/파싱/spoonacular_recipes_serving_final.xlsx' 
    process_file(file_path)
