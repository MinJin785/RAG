import random
import json
from typing import Dict, List, Tuple, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GrammarGenerator:
    """한국어 문법 문제 생성기"""
    
    def __init__(self):
        self.question_types = [
            "문법_선택형",
            "조사_완성",
            "어미_활용",
            "문장_교정",
            "문법_설명",
            "어순_배열",
            "띄어쓰기",
            "맞춤법_교정"
        ]
        
        self.difficulty_levels = ["초급", "중급", "고급"]
        
        # 문법 데이터베이스
        self.grammar_db = {
            "조사": {
                "은/는": {
                    "설명": "주제를 나타내는 보조사",
                    "예시": ["나는 학생이다", "책은 책상 위에 있다"],
                    "오답": ["나를", "책을", "나에게", "책으로"]
                },
                "이/가": {
                    "설명": "주어를 나타내는 주격조사",
                    "예시": ["새가 날아간다", "학교가 크다"],
                    "오답": ["새를", "학교를", "새에게", "학교로"]
                },
                "을/를": {
                    "설명": "목적어를 나타내는 목적격조사",
                    "예시": ["책을 읽는다", "음식을 먹는다"],
                    "오답": ["책이", "음식이", "책에게", "음식으로"]
                }
            },
            "어미": {
                "ㄴ다/는다": {
                    "설명": "현재 시제를 나타내는 종결어미",
                    "예시": ["간다", "먹는다", "본다"],
                    "불규칙": {"ㄷ": "걷다 → 걷는다", "ㅂ": "덥다 → 덥다"}
                },
                "았/었": {
                    "설명": "과거 시제를 나타내는 선어말어미",
                    "예시": ["갔다", "먹었다", "봤다"],
                    "불규칙": {"ㄷ": "걷다 → 걸었다", "ㅂ": "덥다 → 더웠다"}
                }
            },
            "맞춤법": {
                "안/않": {
                    "설명": "'안'은 부사, '않'은 어미",
                    "예시": ["안 간다", "가지 않는다"],
                    "오답_패턴": ["않 간다", "가지 안는다"]
                },
                "되/돼": {
                    "설명": "'되다'의 활용형 구분",
                    "예시": ["되다", "돼라", "됐다"],
                    "오답_패턴": ["돼다", "되라", "되었다"]
                }
            }
        }
        
        # 예문 템플릿
        self.sentence_templates = [
            "오늘 학교{조사} 갑니다.",
            "친구{조사} 만났습니다.",
            "책{조사} 읽고 있어요.",
            "음식{조사} 맛있습니다.",
            "날씨{조사} 좋네요."
        ]
        
    def generate_question(self, question_type: str = None, difficulty: str = "중급") -> Dict[str, Any]:
        """문법 문제 생성"""
        try:
            if not question_type:
                question_type = random.choice(self.question_types)
            
            if question_type == "문법_선택형":
                return self._generate_multiple_choice()
            elif question_type == "조사_완성":
                return self._generate_particle_completion()
            elif question_type == "어미_활용":
                return self._generate_ending_conjugation()
            elif question_type == "문장_교정":
                return self._generate_sentence_correction()
            elif question_type == "문법_설명":
                return self._generate_grammar_explanation()
            elif question_type == "어순_배열":
                return self._generate_word_order()
            elif question_type == "띄어쓰기":
                return self._generate_spacing()
            elif question_type == "맞춤법_교정":
                return self._generate_spelling_correction()
            else:
                return self._generate_multiple_choice()
                
        except Exception as e:
            logger.error(f"문법 문제 생성 오류: {e}")
            return self._generate_fallback_question()
    
    def _generate_multiple_choice(self) -> Dict[str, Any]:
        """객관식 문법 문제 생성"""
        particle_data = random.choice(list(self.grammar_db["조사"].items()))
        particle, data = particle_data
        
        template = random.choice(self.sentence_templates)
        question_sentence = template.format(조사="____")
        
        correct_answer = particle
        wrong_answers = random.sample(data["오답"], 2)
        
        all_choices = [correct_answer] + wrong_answers
        random.shuffle(all_choices)
        
        return {
            "type": "객관식",
            "question": f"다음 문장의 빈칸에 들어갈 가장 적절한 조사는?\n\n{question_sentence}",
            "choices": all_choices,
            "correct_answer": correct_answer,
            "explanation": f"{data['설명']}\n예시: {', '.join(data['예시'])}",
            "difficulty": "중급",
            "category": "조사"
        }
    
    def _generate_particle_completion(self) -> Dict[str, Any]:
        """조사 완성 문제 생성"""
        sentences = [
            ("학교___ 갑니다.", "에", "장소를 나타내는 부사격조사 '에'"),
            ("친구___ 선물을 줬어요.", "에게", "사람을 나타내는 부사격조사 '에게'"),
            ("버스___ 타고 왔어요.", "를", "목적어를 나타내는 목적격조사 '를'"),
            ("오늘___ 날씨가 좋아요.", "은", "주제를 나타내는 보조사 '은'"),
            ("새___ 하늘을 날아요.", "가", "주어를 나타내는 주격조사 '가'")
        ]
        
        sentence, answer, explanation = random.choice(sentences)
        
        return {
            "type": "단답형",
            "question": f"다음 문장의 빈칸에 알맞은 조사를 써 넣으세요.\n\n{sentence}",
            "correct_answer": answer,
            "explanation": explanation,
            "difficulty": "초급",
            "category": "조사_완성"
        }
    
    def _generate_ending_conjugation(self) -> Dict[str, Any]:
        """어미 활용 문제 생성"""
        verbs = [
            ("가다", "간다", "가 + ㄴ다"),
            ("먹다", "먹는다", "먹 + 는다"),
            ("보다", "본다", "보 + ㄴ다"),
            ("읽다", "읽는다", "읽 + 는다"),
            ("쓰다", "쓴다", "쓰 + ㄴ다")
        ]
        
        base_form, conjugated, process = random.choice(verbs)
        
        return {
            "type": "단답형",
            "question": f"다음 동사를 현재 시제로 활용하세요.\n\n{base_form} → ______",
            "correct_answer": conjugated,
            "explanation": f"활용 과정: {process}",
            "difficulty": "중급",
            "category": "어미_활용"
        }
    
    def _generate_sentence_correction(self) -> Dict[str, Any]:
        """문장 교정 문제 생성"""
        wrong_sentences = [
            ("학교를 갑니다.", "학교에 갑니다.", "'갑니다'는 이동 동사이므로 목적지에는 '에'를 사용"),
            ("친구가 만났어요.", "친구를 만났어요.", "'만나다'는 타동사이므로 목적어에 '를'을 사용"),
            ("책이 읽어요.", "책을 읽어요.", "'읽다'는 타동사이므로 목적어에 '을'을 사용"),
            ("음식이 먹었어요.", "음식을 먹었어요.", "'먹다'는 타동사이므로 목적어에 '을'을 사용")
        ]
        
        wrong, correct, explanation = random.choice(wrong_sentences)
        
        return {
            "type": "교정",
            "question": f"다음 문장에서 잘못된 부분을 찾아 올바르게 고치세요.\n\n{wrong}",
            "correct_answer": correct,
            "explanation": explanation,
            "difficulty": "중급",
            "category": "문장_교정"
        }
    
    def _generate_grammar_explanation(self) -> Dict[str, Any]:
        """문법 설명 문제 생성"""
        explanations = [
            ("주격조사 '이/가'의 용법을 설명하세요.", 
             "주어를 나타내는 격조사로, 받침이 있는 명사 뒤에는 '이', 받침이 없는 명사 뒤에는 '가'가 온다.",
             "문법_용법"),
            ("목적격조사 '을/를'의 용법을 설명하세요.",
             "목적어를 나타내는 격조사로, 받침이 있는 명사 뒤에는 '을', 받침이 없는 명사 뒤에는 '를'이 온다.",
             "문법_용법"),
            ("보조사 '은/는'과 주격조사 '이/가'의 차이점을 설명하세요.",
             "'은/는'은 주제를 나타내고 대조의 의미가 있으며, '이/가'는 주어를 나타내고 새로운 정보를 제시한다.",
             "문법_비교")
        ]
        
        question, answer, category = random.choice(explanations)
        
        return {
            "type": "서술형",
            "question": question,
            "correct_answer": answer,
            "explanation": "문법 용법에 대한 정확한 이해가 필요합니다.",
            "difficulty": "고급",
            "category": category
        }
    
    def _generate_word_order(self) -> Dict[str, Any]:
        """어순 배열 문제 생성"""
        scrambled_sentences = [
            (["나는", "학교에", "간다"], "나는 학교에 간다"),
            (["친구가", "책을", "읽는다"], "친구가 책을 읽는다"),
            (["오늘", "날씨가", "좋다"], "오늘 날씨가 좋다"),
            (["엄마가", "음식을", "만드신다"], "엄마가 음식을 만드신다"),
            (["학생들이", "공부를", "열심히", "한다"], "학생들이 열심히 공부를 한다")
        ]
        
        words, correct_sentence = random.choice(scrambled_sentences)
        shuffled_words = words.copy()
        random.shuffle(shuffled_words)
        
        return {
            "type": "배열",
            "question": f"다음 단어들을 올바른 순서로 배열하여 문장을 만드세요.\n\n{' / '.join(shuffled_words)}",
            "correct_answer": correct_sentence,
            "explanation": "한국어의 기본 어순은 주어-목적어-서술어(SOV) 순입니다.",
            "difficulty": "초급",
            "category": "어순"
        }
    
    def _generate_spacing(self) -> Dict[str, Any]:
        """띄어쓰기 문제 생성"""
        spacing_examples = [
            ("나는학교에간다", "나는 학교에 간다"),
            ("친구와함께놀았다", "친구와 함께 놀았다"),
            ("오늘밤에영화를본다", "오늘 밤에 영화를 본다"),
            ("어머니께서요리를하신다", "어머니께서 요리를 하신다"),
            ("우리는공원에서산책했다", "우리는 공원에서 산책했다")
        ]
        
        wrong_spacing, correct_spacing = random.choice(spacing_examples)
        
        return {
            "type": "띄어쓰기",
            "question": f"다음 문장의 띄어쓰기를 올바르게 고치세요.\n\n{wrong_spacing}",
            "correct_answer": correct_spacing,
            "explanation": "각 단어는 띄어써야 하며, 조사는 앞 명사와 붙여씁니다.",
            "difficulty": "중급",
            "category": "띄어쓰기"
        }
    
    def _generate_spelling_correction(self) -> Dict[str, Any]:
        """맞춤법 교정 문제 생성"""
        spelling_errors = [
            ("않 갑니다", "안 갑니다", "'안'은 부사로 용언 앞에서 부정의 뜻을 나타냅니다"),
            ("가지 안아요", "가지 않아요", "'않'은 '아니하다'의 준말로 용언 뒤에 옵니다"),
            ("돼다", "되다", "기본형은 '되다'입니다"),
            ("되라", "돼라", "명령형은 '돼라'입니다"),
            ("설레임", "설렘", "'설레다'의 명사형은 '설렘'입니다")
        ]
        
        wrong_spelling, correct_spelling, explanation = random.choice(spelling_errors)
        
        return {
            "type": "맞춤법",
            "question": f"다음 단어나 표현의 맞춤법을 올바르게 고치세요.\n\n{wrong_spelling}",
            "correct_answer": correct_spelling,
            "explanation": explanation,
            "difficulty": "고급",
            "category": "맞춤법"
        }
    
    def _generate_fallback_question(self) -> Dict[str, Any]:
        """기본 문제 (오류 시 사용)"""
        return {
            "type": "객관식",
            "question": "다음 중 올바른 표현은?\n\n1) 학교를 갑니다\n2) 학교에 갑니다\n3) 학교로 갑니다\n4) 학교는 갑니다",
            "choices": ["학교를 갑니다", "학교에 갑니다", "학교로 갑니다", "학교는 갑니다"],
            "correct_answer": "학교에 갑니다",
            "explanation": "목적지를 나타낼 때는 부사격조사 '에'를 사용합니다.",
            "difficulty": "초급",
            "category": "기본_문법"
        }
    
    def generate_quiz_set(self, count: int = 5, difficulty: str = "중급") -> List[Dict[str, Any]]:
        """문법 문제 세트 생성"""
        questions = []
        used_types = set()
        
        for i in range(count):
            # 중복되지 않는 문제 유형 선택
            available_types = [t for t in self.question_types if t not in used_types]
            if not available_types:
                available_types = self.question_types
                used_types.clear()
            
            question_type = random.choice(available_types)
            used_types.add(question_type)
            
            question = self.generate_question(question_type, difficulty)
            question["question_number"] = i + 1
            questions.append(question)
        
        return questions
    
    def get_statistics(self) -> Dict[str, Any]:
        """문법 문제 통계 정보"""
        return {
            "총_문제_유형": len(self.question_types),
            "문제_유형_목록": self.question_types,
            "난이도_수준": self.difficulty_levels,
            "문법_항목": list(self.grammar_db.keys()),
            "생성_가능_문제수": "무제한",
            "지원_언어": "한국어",
            "마지막_업데이트": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }