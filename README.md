# 무신사 가격 추적

좋아요한 무신사 상품의 가격을 매일 기록하고 선그래프로 보여주는 사이트예요.
GitHub Actions가 매일 한국 시간 오전 9시쯤 가격을 가져오고, GitHub Pages가 그래프를 보여줘요.

## 처음 설정 (한 번만)

1. GitHub에서 **New repository**로 새 저장소를 만들어요. (예: `musinsa-price-tracker`, **Public**)
2. 이 폴더의 파일을 모두 올려요.
   - 저장소 화면에서 **Add file → Upload files** → 압축을 푼 폴더 안의 파일과 폴더를 통째로 끌어다 놓고 **Commit changes**.
   - `.github` 폴더는 숨김 폴더라 안 보일 수 있어요. 안 올라갔다면 아래 "`.github` 폴더가 안 올라갈 때"를 보세요.
3. **Settings → Actions → General** 맨 아래 **Workflow permissions**에서 **Read and write permissions** 선택 → Save.
4. **Settings → Pages**에서 Source를 **Deploy from a branch**, Branch를 **main / (root)** 로 선택 → Save.
   1~2분 뒤 `https://<내아이디>.github.io/musinsa-price-tracker/` 주소로 사이트가 열려요.
5. **Actions** 탭 → **무신사 가격 수집** → **Run workflow** 를 눌러 첫 수집을 바로 해봐요.
   초록 체크가 뜨면 성공이에요. 사이트를 새로고침하면 반영돼요.

## 상품 추가·삭제

`products.txt` 를 열고 연필 아이콘(편집)을 눌러 링크를 한 줄에 하나씩 붙여 넣고 저장하면 끝이에요.
저장하면 자동으로 한 번 수집이 돌아가요.

- 앱의 공유 링크(`musinsa.onelink.me/...`), 긴 공유 링크, `musinsa.com/products/숫자` 모두 돼요.
- 줄을 지우거나 맨 앞에 `#` 을 붙이면 추적이 멈춰요. 그동안의 기록은 사이트 아래쪽에 보관돼요.

## 시간 바꾸기

`.github/workflows/track.yml` 의 `cron: "17 0 * * *"` 를 고쳐요. UTC 기준이라 한국 시간에서 9시간을 빼야 해요.
예) 오후 9시 = UTC 12시 → `"17 12 * * *"`

## 잘 안 될 때

- **Actions 실행이 빨간 X**: 실행 기록을 눌러 '가격 수집' 단계의 메시지를 보세요.
  `가격 정보를 못 찾음` 이나 `열기 실패` 가 모든 상품에 뜨면 무신사가 GitHub 서버 접속을 막은 거예요.
- **기록 저장 단계에서 실패(403)**: 3번(Read and write permissions) 설정을 확인하세요.
- **60일 넘게 저장소에 변화가 없으면** GitHub가 예약 실행을 멈출 수 있어요. 가격이 매일 기록되면 그럴 일은 없어요.

## `.github` 폴더가 안 올라갈 때

저장소에서 **Add file → Create new file** → 파일 이름 칸에 `.github/workflows/track.yml` 을 그대로 입력하고,
`track.yml` 내용을 복사해 붙여 넣은 뒤 **Commit changes**.

## 파일 구성

| 파일 | 역할 |
|---|---|
| `products.txt` | 추적할 상품 링크 목록 |
| `scripts/fetch_prices.py` | 상품 페이지에서 판매가·정가·할인율을 읽어 기록 |
| `data/prices.json` | 날짜별 가격 기록 (자동으로 쌓임) |
| `index.html` | 선그래프 사이트 |
| `.github/workflows/track.yml` | 매일 자동 실행 설정 |
