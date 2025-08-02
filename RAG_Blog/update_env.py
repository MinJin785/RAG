"""
.env 파일에 새로운 RAG_Blog 전용 API 키 업데이트
"""

# 새로운 .env 파일 내용
new_env_content = """# RAG_Blog 전용 구글 API (새로 생성)
GOOGLE_API_KEY_RAG_BLOG=AIzaSyBIBZNgGd_i_aG2IhlqFQqhl0MP3-J5CCA
GOOGLE_SEARCH_ENGINE_ID=2149f2d26311449a4

# 기존 AI민진용 구글 API 키들 (참고용)
GOOGLE_API_KEY_1=AIzaSyCBqTFHJ9gLhUBygCA6bOjR1eCDSTXHES4
GOOGLE_API_KEY_2=AIzaSyDMJSWkF2PEM-Z6tJzVSRxD69xk3mXtL_A

# Perplexity API (결제했지만 사용 안함)
PERPLEXITY_API_KEY=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
"""

# .env 파일 업데이트
with open('.env', 'w', encoding='utf-8') as f:
    f.write(new_env_content)

print("✅ .env 파일 업데이트 완료!")
print("🔑 RAG_Blog 전용 API 키 설정됨")
print("🚀 30번 하이브리드 검색 준비 완료!")