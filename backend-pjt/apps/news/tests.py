from unittest.mock import Mock, patch

from bs4 import BeautifulSoup
from django.test import SimpleTestCase

from .article_fetcher import normalize_content, remove_noise
from .services import normalize_cached_summary
from .summarizer import news_summary_metric, summarize_news_content


class NewsSummarizerTests(SimpleTestCase):
    def test_replaces_incomplete_model_output_with_article_sentence(self):
        content = "황성엽 금융투자협회장은 ETF 시장의 과열 경쟁을 우려한다고 밝혔다."

        with patch(
            "apps.news.summarizer.generate_llm_summary",
            return_value="황성엽 금투협회장은 ETF 시장 과열과 삼",
        ):
            summary = summarize_news_content("ETF 시장 과열 우려", content)

        self.assertEqual(summary, content)

    def test_rejects_incomplete_cached_summary(self):
        self.assertEqual(normalize_cached_summary("황성엽 금투협회장은 ETF 시장 과열과 삼"), "")

    def test_accepts_complete_cached_summary(self):
        summary = "황성엽 금융투자협회장은 ETF 시장의 과열 경쟁을 우려한다고 밝혔다."

        self.assertEqual(normalize_cached_summary(summary), summary)

    def test_accepts_two_sentence_cached_summary(self):
        summary = "해외 주식의 강제 교환에도 국내 투자자에게 양도세가 부과됐다. 전문가들은 국내외 기업 간 과세 형평성을 위해 세법 개정이 필요하다고 지적했다."

        self.assertEqual(normalize_cached_summary(summary), summary)

    def test_accepts_summary_ending_with_ida(self):
        summary = "국민연금의 국내 주식 매도 자금은 국내외 채권으로 이동할 전망이다."

        self.assertEqual(normalize_cached_summary(summary), summary)

    def test_rejects_anchor_script_as_cached_summary(self):
        summary = "<앵커> 미국 주식 갖고 계신 분들 많으실 텐데요. 실제로 벌어진 일입니다."

        self.assertEqual(normalize_cached_summary(summary), "")

    def test_rejects_interview_quote_as_cached_summary(self):
        summary = "[이 모씨/개인투자자: 양도세를 내야 할 현금을 마련해야 한다고 말했습니다."

        self.assertEqual(normalize_cached_summary(summary), "")

    def test_metric_prefers_focused_gold_aligned_summary(self):
        example = Mock(
            title="단일종목 레버리지 상품 우려",
            content="금감원장이 단일종목 레버리지 상품의 개인투자자 위험을 지적했다.",
            summary="금감원장은 단일종목 레버리지 상품이 개인투자자 위험을 키운다고 지적했다.",
        )
        focused = Mock(summary=example.summary)
        unfocused = Mock(
            summary=(
                "금감원장은 단일종목 레버리지 상품이 개인투자자 위험을 키운다고 지적했다. "
                "스페이스X 공모주와 스튜어드십코드에 대한 입장도 밝혔다."
            )
        )

        self.assertGreater(news_summary_metric(example, focused), news_summary_metric(example, unfocused))


class ArticleFetcherTests(SimpleTestCase):
    def test_removes_naver_summary_and_photo_caption(self):
        soup = BeautifulSoup(
            """
            <div id="dic_area">
              <strong class="media_end_summary">문장 구분 없는 서브헤드</strong>
              <table class="nbd_table"><tr><td>사진 설명</td></tr></table>
              <p>실제 기사 본문이다.</p>
            </div>
            """,
            "html.parser",
        )

        remove_noise(soup)

        self.assertEqual(soup.select_one("#dic_area").get_text(" ", strip=True), "실제 기사 본문이다.")

    def test_uses_reporter_segment_for_broadcast_article(self):
        content = "<앵커> 시청자 도입 멘트입니다. <기자> 실제 세금 문제를 취재했습니다."

        self.assertEqual(normalize_content(content), "실제 세금 문제를 취재했습니다.")
