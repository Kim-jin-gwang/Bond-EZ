# 서비스 기획
---
## 1단계 : 디자인 띵킹
- [What] **채권 정보 제공 서비스**
    - 채권 구매 시 기업의 정보 확인 및 현재 어떤 채권을 사는게 이득인지 추천
    - 3개의 사이트에서 크롤링
        - 한국 신용정보 : 회사의 신용등급 확인(왜 이렇게 평가했는가)
        - KRX Data Marketplace : call옵션 확인 등 자세한 채권 정보 확인
        - DART 공시 : 채권을 발행했을 때 발행 목적 등 채권 발행 개요
- [Who] 채권 매수 시 어떤 채권이 좋을지 고민하는 사람들
- [Why] 채권 매수 전 기업의 정보가 여러 사이트에 나뉘어져 있어 한 눈에 확인이 어려움
    - 해당 기업의 사업 구조, 비전, 관련 리서치, 공시 정보, 재무 정보 등
    - 해당 채권의 신용 등급, 발행 정보, 신용 스프레드, 표면금리, 옵션 정보 등
    
    → 채권 투자 시 필요한 정보가 흩어져 있음
## 2단계 : 시장 조사
현재 채권 구매 전 기업의 정보가 분할되어 확인이 불편함

- [한국신용평가](https://www.kisrating.com/ratingsSearch/corp_overview.do?kiscd=H48428) → 해당 회사 채권의 신용 등급, 평가 리포트, 관련 리서치
- [KRX Data MarketPlace](https://data.krx.co.kr/contents/MDC/MDI/mdiLoader/index.cmd?menuId=MDC0201) → 해당 채권 상세 정보(옵션, 발행 정보, 선후순위구분, 이자선후급구분 등)
- [DART](https://dart.fss.or.kr/dsab007/main.do?option=corp) → 해당 기업 공시 정보
- [NICE 신용평가](https://www.nicerating.com/disclosure/spreadRates.do?strDate=2024-10-16) → 금리 및 스프레드
- [장내채권시세](https://www.shinhansec.com/siw/wealth-management/bond-rp/590401/view.do)

## 3단계 : 구체화
- 최종 목표: 채권 투자 시 필요한 정보 제공
### 필요 데이터
- HTS에서 제공하는 기본적인 채권 정보
    - 표면이율
    - 신용등급
    - 발행일자
    - 만기일자
    - 이자지급유형
    - 세금(법인세, 소득세, 지방소득세, 농특세 등)
- 한국신용평가 정보
    - 해당 채권 신용 정보
    - 평가 리포트 → 해당 신용 평가를 한 이유(등급 사유)
    - 관련 리서치
- KRX DataMarketPlace → 해당 채권 정보
    - 채권분류
    - 선후순위구분
    - 신종자본증권여부
    - 이자지급방법
    - 이자지급단위월수
    - 이자선후급구분
    - 이자지급기준
    - 옵션 여부(CALL/PUT)
    - 옵션행사개시일
    - 대표주관회사
- DART → 공시 정보 (토글 정보로 개요 긴 것들을 보여주는 용도)
    - 개요 → 사실 나열
## 4단계 : 와이어프레임
![와이어프레임](/images/wireframe.png)

## 5단계 : 스프린트 계획
![프로덕트 백로그](/images/product_backlog.png)
![스프린트 계획](/images/sprint20260515.png)

## 6단계 : ERD
![ERD](/images/ERD.jpg)

## 협업 자료
- [Notion](https://www.notion.so/pastjung/SSAFY-2026-05-08-2026-06-26-35aef948eae48060bccddfae31b7f6a5?source=copy_link)