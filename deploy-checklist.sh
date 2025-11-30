#!/bin/bash
# 배포 체크리스트 스크립트

echo "🚀 AsKNU Backend 배포 체크리스트"
echo "=================================="
echo ""

# 1. 환경 변수 확인
echo "📋 1. 환경 변수 확인"
if [ -f .env ]; then
    echo "   ✅ .env 파일 존재"
    required_vars=("DATABASE_URL" "UPSTAGE_API_KEY" "UPSTAGE_MODEL" "BASE_BOARD")
    for var in "${required_vars[@]}"; do
        if grep -q "^$var=" .env; then
            echo "   ✅ $var 설정됨"
        else
            echo "   ❌ $var 누락!"
        fi
    done
else
    echo "   ❌ .env 파일 없음. .env.example을 복사하세요."
fi
echo ""

# 2. 의존성 확인
echo "📦 2. 의존성 확인"
if [ -f requirements.txt ]; then
    echo "   ✅ requirements.txt 존재"
    echo "   패키지 개수: $(cat requirements.txt | wc -l)"
else
    echo "   ❌ requirements.txt 없음"
fi
echo ""

# 3. Git 상태
echo "📝 3. Git 상태"
git_branch=$(git branch --show-current 2>/dev/null)
if [ $? -eq 0 ]; then
    echo "   현재 브랜치: $git_branch"
    uncommitted=$(git status --porcelain | wc -l)
    if [ $uncommitted -eq 0 ]; then
        echo "   ✅ 모든 변경사항 커밋됨"
    else
        echo "   ⚠️  커밋되지 않은 변경사항: $uncommitted개"
    fi
else
    echo "   ❌ Git 저장소가 아닙니다"
fi
echo ""

# 4. 필수 파일 확인
echo "📄 4. 배포 필수 파일"
files=("main.py" "requirements.txt" "render.yaml" "DEPLOYMENT.md" ".env.example" ".gitignore")
for file in "${files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✅ $file"
    else
        echo "   ❌ $file 누락"
    fi
done
echo ""

# 5. 로컬 서버 테스트
echo "🧪 5. 로컬 서버 테스트 (선택)"
echo "   다음 명령어로 로컬 테스트:"
echo "   uvicorn main:app --reload --port 8000"
echo "   http://localhost:8000/docs 접속 확인"
echo ""

# 6. 배포 준비 완료
echo "=================================="
echo "🎯 다음 단계:"
echo "1. GitHub에 푸시: git push origin $(git branch --show-current 2>/dev/null || echo 'main')"
echo "2. Render.com 접속 및 로그인"
echo "3. New Web Service 생성"
echo "4. GitHub 저장소 연결"
echo "5. 환경 변수 설정 (DEPLOYMENT.md 참조)"
echo "6. Deploy!"
echo ""
echo "📚 자세한 가이드: DEPLOYMENT.md"
echo "=================================="
