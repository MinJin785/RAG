"""
PDF를 고해상도 이미지로 변환 (배경화면용)
"""

from pdf2image import convert_from_path
import os

pdf_path = "ocr_exam/data/exams/omr_87D78766.pdf"
output_dir = "ocr_exam/data/exams/images"

# 출력 디렉토리 생성
os.makedirs(output_dir, exist_ok=True)

print("=" * 70)
print("PDF를 이미지로 변환 중...")
print("=" * 70)

# PDF를 고해상도 이미지로 변환 (300 DPI)
images = convert_from_path(
    pdf_path,
    dpi=300,  # 고해상도
    fmt='png'
)

print(f"\n총 {len(images)} 페이지 변환됨\n")

# 각 페이지 저장
for i, image in enumerate(images, 1):
    output_path = os.path.join(output_dir, f"omr_87D78766_page_{i}.png")
    image.save(output_path, 'PNG', quality=95)

    # 파일 크기 확인
    file_size = os.path.getsize(output_path) / 1024  # KB
    print(f"✅ 페이지 {i}: {output_path}")
    print(f"   크기: {image.width} x {image.height} 픽셀")
    print(f"   파일 크기: {file_size:.1f} KB\n")

print("=" * 70)
print("변환 완료!")
print("=" * 70)
print(f"\n📁 저장 위치: {output_dir}/")
print("\n💡 배경화면 설정 방법:")
print("   1. 생성된 PNG 파일 다운로드")
print("   2. 우클릭 > '배경화면으로 설정'")
print("   3. 또는 바탕화면 우클릭 > 개인 설정 > 배경")
