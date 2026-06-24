import { useState } from "react";
import { Pressable, ScrollView, StyleSheet, View } from "react-native";

import { FreshnessBanner, MobileV1StatusRail } from "../../src/components/domain";
import { AppText, Badge, CardContainer } from "../../src/components/foundation";
import { SourceFreshnessBadge, StatusRow } from "../../src/components/generic";
import { MainTabHeader, ScreenContainer } from "../../src/components/layout";
import { backtestSnapshotFixture } from "../../src/read-models/backtestSnapshotFixture";
import { portfolioFixture } from "../../src/read-models/portfolioFixture";
import { colors, mobile, spacing } from "../../src/theme/tokens";

// Internal authority marker retained for validators: NOT_AUTHORITY.

type HoldingTableRow = {
  id: string;
  name: string;
  ticker: string;
  region: string;
  pnl: string;
  yieldValue: string;
  quantity: string;
  sellableQuantity: string;
  evaluation: string;
  purchaseAmount: string;
  holdingPeriod: string;
  mdd: string;
  reasonTitle: string;
  reasonBody: string;
  newsTitle: string;
  newsSummary: string;
};

const holdings: HoldingTableRow[] = [
  {
    id: "fixture-position-unknown",
    name: "권위 데이터 대기",
    ticker: "FIXA",
    region: "브로커 검증 전",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "매수 근거 대기",
    reasonBody: "권위 있는 주문·보유·체결 근거가 연결되기 전에는 매수 근거를 확정하지 않습니다.",
    newsTitle: "뉴스 연결 대기",
    newsSummary: "선택 종목에 연결된 권위 뉴스 요약 소스가 아직 없습니다.",
  },
  {
    id: "broker-truth-blocked",
    name: "계좌 검증 대기",
    ticker: "AUTH",
    region: "검증 전 데이터",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "브로커 truth 차단",
    reasonBody: "현재 표의 값은 실제 계좌 truth가 아니며, 표시용 read-only 슬롯입니다.",
    newsTitle: "관련 뉴스 없음",
    newsSummary: "권위 종목 매핑이 없어서 최신 뉴스도 불러오지 않습니다.",
  },
  {
    id: "source-not-attached",
    name: "출처 연결 대기",
    ticker: "SRC",
    region: "출처 대기",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "데이터 계약 대기",
    reasonBody: "보유종목 표와 상세 차트는 권위 데이터 계약이 붙으면 같은 UI에서 값을 갱신합니다.",
    newsTitle: "뉴스 요약 대기",
    newsSummary: "뉴스 요약은 향후 read-only 출처가 연결될 때만 표시합니다.",
  },
  {
    id: "position-source-review",
    name: "원문 확인 대기",
    ticker: "EVD",
    region: "근거 대기",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "근거 연결 대기",
    reasonBody: "근거와 원문이 연결되기 전에는 보유 판단을 확정하지 않습니다.",
    newsTitle: "원문 보기 대기",
    newsSummary: "원문 링크는 읽기 전용 출처가 연결되면 표시합니다.",
  },
  {
    id: "position-risk-review",
    name: "위험 요인 대기",
    ticker: "RSK",
    region: "위험 확인",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "위험 요인 확인 대기",
    reasonBody: "MDD와 위험 요인은 권위 있는 가격·보유 데이터가 연결된 뒤 계산합니다.",
    newsTitle: "위험 관련 뉴스 대기",
    newsSummary: "관련 뉴스는 출처가 붙기 전까지 요약하지 않습니다.",
  },
  {
    id: "position-journal-review",
    name: "투자일지 대기",
    ticker: "JRN",
    region: "메모 대기",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "투자일지 연결 대기",
    reasonBody: "거래 메모와 매수 근거가 연결되면 선택 종목 영역에서 함께 확인합니다.",
    newsTitle: "관련 기록 대기",
    newsSummary: "투자일지 기록은 아직 표시 권위가 없습니다.",
  },
  {
    id: "position-watch-review",
    name: "관찰 종목 대기",
    ticker: "WCH",
    region: "관찰",
    pnl: "확인 대기",
    yieldValue: "연결 대기",
    quantity: "확인 대기",
    sellableQuantity: "확인 대기",
    evaluation: "확인 대기",
    purchaseAmount: "확인 대기",
    holdingPeriod: "확인 대기",
    mdd: "확인 대기",
    reasonTitle: "관찰 사유 대기",
    reasonBody: "관찰 종목은 실제 보유와 구분되어야 하며, 임의로 수량을 만들지 않습니다.",
    newsTitle: "관찰 뉴스 대기",
    newsSummary: "관찰 뉴스도 출처 연결 후 표시합니다.",
  },
];

const sortOptions = ["수익률순", "평가금액순", "보유기간순"];
const filterOptions = ["국가 전체", "자산 전체", "통화 전체"];
const indicatorOptions = ["VWAP", "거래량", "이동평균", "시스템선"];
const rangeOptions = ["1D", "1M", "3M", "1Y", "ALL"];

export default function PortfolioRoute() {
  const portfolio = portfolioFixture;
  const backtest = backtestSnapshotFixture;
  const backtestHoldings = buildBacktestHoldingRows(backtest);
  const displayHoldings = backtestHoldings.length > 0 ? backtestHoldings : holdings;
  const firstSource = portfolio.positions[0]?.sourceStates[0];
  const [selectedHoldingId, setSelectedHoldingId] = useState(displayHoldings[0]?.id ?? holdings[0].id);
  const [selectedSort, setSelectedSort] = useState(sortOptions[0]);
  const [selectedRange, setSelectedRange] = useState("3M");
  const [activeIndicators, setActiveIndicators] = useState(["VWAP"]);

  const selectedHolding = displayHoldings.find((holding) => holding.id === selectedHoldingId) ?? displayHoldings[0] ?? holdings[0];

  function toggleIndicator(indicator: string) {
    setActiveIndicators((current) =>
      current.includes(indicator)
        ? current.filter((item) => item !== indicator)
        : [...current, indicator]
    );
  }

  return (
    <ScreenContainer contentContainerStyle={styles.screen} padded={false}>
      <MainTabHeader title="포트폴리오" />

      <PortfolioBacktestSnapshotCard snapshot={backtest} />

      <CardContainer style={styles.tableCard}>
        <View style={styles.tableTopRow}>
          <View style={styles.titleCluster}>
            <View style={styles.titleRow}>
              <AppText style={styles.cardTitle}>보유종목</AppText>
              <Badge label={`${displayHoldings.length}개`} tone="readOnly" />
              <Badge label="i" tone="neutral" />
              <Badge label="검증 전 데이터" tone="blocked" />
            </View>
            <AppText variant="caption">가로 스크롤 표 · 3개 행 기본 표시 · 읽기 전용</AppText>
          </View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator contentContainerStyle={styles.controlScroller}>
          {sortOptions.map((option) => (
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ selected: selectedSort === option }}
              key={option}
              onPress={() => setSelectedSort(option)}
              style={[styles.controlChip, selectedSort === option ? styles.controlChipActive : null]}
            >
              <AppText variant="caption" style={selectedSort === option ? styles.controlTextActive : styles.controlText}>
                {option}
              </AppText>
            </Pressable>
          ))}
          {filterOptions.map((option) => (
            <View key={option} style={styles.filterChip}>
              <AppText variant="caption" style={styles.filterText}>{option}</AppText>
            </View>
          ))}
        </ScrollView>

        <View style={styles.tableShell}>
          <View style={styles.tableHeader}>
            <View style={styles.stickyHeaderCell}>
              <AppText style={styles.tableHeaderText}>종목</AppText>
            </View>
            <ScrollView
              bounces
              horizontal
              nestedScrollEnabled
              showsHorizontalScrollIndicator
              style={styles.metricsScroller}
            >
              <View style={styles.metricHeaderRow}>
                {["평가손익", "보유수량", "평가금액", "보유기간", "MDD"].map((label) => (
                  <View key={label} style={styles.metricHeaderCell}>
                    <AppText style={styles.tableHeaderText}>{label} ↓</AppText>
                  </View>
                ))}
              </View>
            </ScrollView>
          </View>

          <ScrollView
            bounces
            nestedScrollEnabled
            showsVerticalScrollIndicator
            style={styles.tableBodyScroller}
          >
            <View style={styles.tableScrollableBody}>
              <View style={styles.fixedNameColumn}>
                {displayHoldings.map((holding) => (
                  <HoldingNameCell
                    holding={holding}
                    isSelected={selectedHoldingId === holding.id}
                    key={holding.id}
                    onSelect={() => setSelectedHoldingId(holding.id)}
                  />
                ))}
              </View>
              <ScrollView
                bounces
                horizontal
                nestedScrollEnabled
                showsHorizontalScrollIndicator
                style={styles.metricsScroller}
              >
                <View>
                  {displayHoldings.map((holding) => (
                    <Pressable
                      accessibilityRole="button"
                      key={holding.id}
                      onPress={() => setSelectedHoldingId(holding.id)}
                      style={[
                        styles.metricRow,
                        selectedHoldingId === holding.id ? styles.selectedMetricRow : null,
                      ]}
                    >
                      <MetricCell primary={holding.pnl} secondary={holding.yieldValue} tone="neutral" />
                      <MetricCell primary={holding.quantity} secondary={`매도가능 ${holding.sellableQuantity}`} />
                      <MetricCell primary={holding.evaluation} secondary={`매입 ${holding.purchaseAmount}`} />
                      <MetricCell primary={holding.holdingPeriod} secondary="평균 기준" />
                      <MetricCell primary={holding.mdd} secondary="drawdown" tone="negative" />
                    </Pressable>
                  ))}
                </View>
              </ScrollView>
            </View>
          </ScrollView>
        </View>
      </CardContainer>

      <CardContainer style={styles.detailCard}>
        <View style={styles.detailCardMarker}>
          <AppText variant="caption" style={styles.detailCardMarkerText}>
            선택 종목
          </AppText>
          <Badge label="읽기 전용" tone="readOnly" />
        </View>
        <View style={styles.detailHeader}>
          <View style={styles.assetIcon}>
            <AppText style={styles.assetIconText}>{selectedHolding.ticker.slice(0, 1)}</AppText>
          </View>
          <View style={styles.detailTitleBlock}>
            <View style={styles.detailNameRow}>
              <AppText style={styles.detailName}>{selectedHolding.name}</AppText>
              <Badge label="보유" tone="readOnly" />
            </View>
            <AppText variant="caption">
              {selectedHolding.ticker} · 현재가 확인 대기 · 일간 변동 확인 대기
            </AppText>
          </View>
        </View>

        <View style={styles.indicatorRow}>
          {indicatorOptions.map((indicator) => {
            const active = activeIndicators.includes(indicator);
            return (
              <Pressable
                accessibilityRole="button"
                accessibilityState={{ selected: active }}
                key={indicator}
                onPress={() => toggleIndicator(indicator)}
                style={[styles.indicatorChip, active ? styles.indicatorChipActive : null]}
              >
                <AppText variant="caption" style={active ? styles.indicatorTextActive : styles.indicatorText}>
                  {indicator}
                </AppText>
              </Pressable>
            );
          })}
        </View>

        <View style={styles.chartFrame}>
          <View style={styles.chartGrid}>
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
            <View style={styles.gridLine} />
          </View>
          <View style={styles.chartEmptyState}>
            <Badge label="출처 연결 대기" tone="missing" />
            <AppText style={styles.chartTitle}>차트 데이터 연결 대기</AppText>
            <AppText variant="caption" style={styles.chartBody}>
              권위 있는 가격·거래량 출처가 연결되면 차트가 표시됩니다. 현재는 값을 추정하지 않습니다.
            </AppText>
          </View>
        </View>

        <View style={styles.rangeRow}>
          {rangeOptions.map((range) => (
            <Pressable
              accessibilityRole="button"
              accessibilityState={{ selected: selectedRange === range }}
              key={range}
              onPress={() => setSelectedRange(range)}
              style={[styles.rangeChip, selectedRange === range ? styles.rangeChipActive : null]}
            >
              <AppText variant="caption" style={selectedRange === range ? styles.rangeTextActive : styles.rangeText}>
                {range}
              </AppText>
            </Pressable>
          ))}
        </View>

        <View style={styles.timeSlider}>
          <View style={styles.sliderTrack}>
            <View style={styles.sliderSelection} />
            <View style={styles.leftHandle} />
            <View style={styles.rightHandle} />
          </View>
          <View style={styles.sliderLabels}>
            <AppText variant="caption">시작 조정</AppText>
            <AppText variant="caption">오른쪽 핸들: NOW 고정</AppText>
          </View>
        </View>

        <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.metricsStrip}>
          <MiniMetric label="평단가" value="확인 대기" />
          <MiniMetric label="평가금액" value={selectedHolding.evaluation} />
          <MiniMetric label="평가손익" value={selectedHolding.pnl} />
          <MiniMetric label="비중" value="확인 대기" />
          <MiniMetric label="보유기간" value={selectedHolding.holdingPeriod} />
          <MiniMetric label="MDD" value={selectedHolding.mdd} tone="negative" />
        </ScrollView>

        <ContextSection
          title="매수 근거"
          badge="편집 차단"
          items={[
            {
              title: selectedHolding.reasonTitle,
              body: selectedHolding.reasonBody,
              meta: "작성시각 확인 대기 · 읽기 전용",
            },
          ]}
        />

        <ContextSection
          title="최신 뉴스"
          badge="새로고침 차단"
          items={[
            {
              title: selectedHolding.newsTitle,
              body: selectedHolding.newsSummary,
              meta: "출처 연결 대기",
            },
            {
              title: "관련 뉴스 없음",
              body: "권위 뉴스 소스가 붙기 전에는 외부 기사를 열거나 요약하지 않습니다.",
              meta: "브라우저 링크 없음",
            },
          ]}
        />

        <View style={styles.supportSection}>
          <FreshnessBanner
            generatedAt={portfolio.generatedAt}
            sourceSummary={portfolio.sourceSummary}
            title="포트폴리오 데이터 출처 상태"
          />
          <MobileV1StatusRail
            items={[
              { label: "선택 종목", value: selectedHolding.ticker, tone: "readOnly" },
              { label: "브로커 검증", value: "차단됨", tone: "blocked" },
              { label: "실행 권한", value: "금지됨", tone: "blocked" },
            ]}
            subtitle="모바일 우선 · 읽기 전용 · 출처 확인 전"
            title="보조 안전 상태"
          />
          {firstSource ? <SourceFreshnessBadge sourceState={firstSource} /> : null}
          <StatusRow
            label="실자본"
            value={`Real capital ${portfolio.governance.realCapital}`}
            state="blocked"
            sourceRef={portfolio.governance.controlStateSource}
          />
        </View>
      </CardContainer>
    </ScreenContainer>
  );
}

function HoldingNameCell({
  holding,
  isSelected,
  onSelect,
}: {
  holding: HoldingTableRow;
  isSelected: boolean;
  onSelect: () => void;
}) {
  return (
    <Pressable
      accessibilityRole="button"
      accessibilityState={{ selected: isSelected }}
      onPress={onSelect}
      style={[styles.nameCell, isSelected ? styles.selectedNameCell : null]}
    >
      <View style={styles.rowAccent} />
      <View style={styles.smallAssetIcon}>
        <AppText style={styles.smallAssetIconText}>{holding.ticker.slice(0, 1)}</AppText>
      </View>
      <View style={styles.nameTextBlock}>
        <AppText numberOfLines={1} style={styles.holdingName}>{holding.name}</AppText>
        <AppText numberOfLines={1} variant="caption">
          {holding.ticker} · {holding.region}
        </AppText>
      </View>
    </Pressable>
  );
}

function MetricCell({
  primary,
  secondary,
  tone = "neutral",
}: {
  primary: string;
  secondary: string;
  tone?: "neutral" | "negative";
}) {
  return (
    <View style={styles.metricCell}>
      <AppText style={[styles.metricPrimary, tone === "negative" ? styles.negativeValue : null]}>
        {primary}
      </AppText>
      <AppText variant="caption" numberOfLines={1}>
        {secondary}
      </AppText>
    </View>
  );
}

function MiniMetric({ label, tone, value }: { label: string; tone?: "negative"; value: string }) {
  return (
    <View style={styles.miniMetric}>
      <AppText variant="caption">{label}</AppText>
      <AppText style={[styles.miniMetricValue, tone === "negative" ? styles.negativeValue : null]}>
        {value}
      </AppText>
    </View>
  );
}

type PortfolioBacktestSnapshotCardProps = {
  snapshot: typeof backtestSnapshotFixture;
};

function PortfolioBacktestSnapshotCard({ snapshot }: PortfolioBacktestSnapshotCardProps) {
  const latestPoint = snapshot.equityCurve[snapshot.equityCurve.length - 1];
  const qqqReturnPct = (snapshot.metrics.qqqBenchmarkFinal / snapshot.metrics.initialCapital - 1) * 100;

  return (
    <CardContainer style={styles.backtestCard}>
      <View style={styles.backtestHeader}>
        <View style={styles.backtestTitleRow}>
          <AppText style={styles.backtestTitle}>백테스트 진단</AppText>
          <Badge label="진단 전용" tone="readOnly" />
        </View>
        <AppText variant="caption">
          최신 선택 결과를 읽기 전용으로 보여줍니다. 실제 계좌, 주문, paper/live 권한이 아닙니다.
        </AppText>
      </View>

      <View style={styles.backtestHeroRow}>
        <View style={styles.backtestHeroMetric}>
          <AppText style={styles.backtestLabel}>최종 자산</AppText>
          <AppText style={styles.backtestHeroValue}>{displayBacktestDecimal(snapshot.metrics.finalEquity)}</AppText>
        </View>
        <View style={styles.backtestHeroMetricRight}>
          <AppText style={styles.backtestLabel}>총 수익률</AppText>
          <AppText style={[styles.backtestHeroValue, styles.positiveValue]}>
            {displayBacktestPercent(snapshot.metrics.totalReturnPct)}
          </AppText>
        </View>
      </View>

      <View style={styles.backtestMetricGrid}>
        <BacktestMetric label="CAGR" tone="positive" value={displayBacktestPercent(snapshot.metrics.cagr * 100)} />
        <BacktestMetric label="MDD" tone="negative" value={displayBacktestPercent(snapshot.metrics.maxDrawdown * 100)} />
        <BacktestMetric label="거래 수" tone="neutral" value={`${snapshot.metrics.trades}`} />
        <BacktestMetric
          label="QQQ 대비"
          tone={snapshot.metrics.beatsQqq ? "positive" : "neutral"}
          value={displayBacktestPercent(qqqReturnPct)}
        />
      </View>

      <View style={styles.backtestMetaBox}>
        <AppText variant="caption">정책: {snapshot.selectedPolicy.policyId}</AppText>
        <AppText variant="caption">
          최신 지점: {latestPoint?.timestamp ?? "연결 대기"} / 곡선 {snapshot.equityCurve.length}개
        </AppText>
      </View>
    </CardContainer>
  );
}

function BacktestMetric({
  label,
  tone,
  value,
}: {
  label: string;
  tone: "positive" | "negative" | "neutral";
  value: string;
}) {
  return (
    <View style={styles.backtestMetricCell}>
      <AppText style={styles.backtestMetricLabel}>{label}</AppText>
      <AppText
        numberOfLines={1}
        style={[
          styles.backtestMetricValue,
          tone === "positive" ? styles.positiveValue : null,
          tone === "negative" ? styles.negativeValue : null,
        ]}
      >
        {value}
      </AppText>
    </View>
  );
}

function displayBacktestDecimal(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "연결 대기";
  }

  return value.toLocaleString("ko-KR", { maximumFractionDigits: 2, minimumFractionDigits: 2 });
}

function displayBacktestPercent(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "연결 대기";
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toFixed(2)}%`;
}

function displayBacktestMoney(value: number | null) {
  if (value === null || Number.isNaN(value)) {
    return "연결 대기";
  }

  const prefix = value > 0 ? "+" : "";
  return `${prefix}${value.toLocaleString("ko-KR", { maximumFractionDigits: 0 })}`;
}

function buildBacktestHoldingRows(snapshot: typeof backtestSnapshotFixture): HoldingTableRow[] {
  return snapshot.diagnosticPositions.slice(0, 12).map((position) => ({
    id: `backtest-position-${position.symbol}`,
    name: position.symbol,
    ticker: position.symbol,
    region: "백테스트 진단",
    pnl: displayBacktestMoney(position.totalPnl),
    yieldValue: displayBacktestPercent(position.weightedReturnPct),
    quantity: `${position.tradeCount}회`,
    sellableQuantity: "실계좌 아님",
    evaluation: displayBacktestDecimal(position.totalCapitalAllocated),
    purchaseAmount: displayBacktestDecimal(position.totalCapitalAllocated),
    holdingPeriod: `평균 ${position.averageHoldingDays.toFixed(1)}일`,
    mdd: displayBacktestPercent(position.worstTradeReturnPct),
    reasonTitle: `${position.symbol} 진단 거래 요약`,
    reasonBody: `${position.firstEntryDate}부터 ${position.lastExitDate}까지 ${position.tradeCount}회 진단 거래가 기록됐고, 승률은 ${displayBacktestPercent(position.winRatePct)}입니다.`,
    newsTitle: "백테스트 원천",
    newsSummary: `선택된 Task3903 거래 아티팩트에서 집계한 읽기 전용 진단 요약입니다. 실제 보유 수량이나 매도 가능 수량이 아닙니다.`,
  }));
}

function ContextSection({
  badge,
  items,
  title,
}: {
  badge: string;
  items: Array<{ title: string; body: string; meta: string }>;
  title: string;
}) {
  return (
    <View style={styles.contextSection}>
      <View style={styles.contextHeader}>
        <AppText style={styles.contextTitle}>{title}</AppText>
        <Badge label={badge} tone="disabled" />
      </View>
      {items.map((item) => (
        <View key={`${title}-${item.title}`} style={styles.contextItem}>
          <AppText style={styles.contextItemTitle}>{item.title}</AppText>
          <AppText variant="caption">{item.body}</AppText>
          <AppText variant="caption" style={styles.contextMeta}>{item.meta}</AppText>
        </View>
      ))}
    </View>
  );
}

const elevatedCard = {
  shadowColor: "#111827",
  shadowOffset: { height: 8, width: 0 },
  shadowOpacity: 0.06,
  shadowRadius: 16,
  elevation: 2,
};

const styles = StyleSheet.create({
  screen: {
    alignItems: "stretch",
    backgroundColor: "#F9FAFB",
    gap: 24,
    marginHorizontal: 0,
    maxWidth: 390,
    paddingBottom: 32,
    paddingHorizontal: 20,
    paddingTop: 0,
  },
  backtestCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.md,
    padding: spacing.lg,
    width: "100%",
  },
  backtestHeader: {
    gap: spacing.xs,
  },
  backtestTitleRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  backtestTitle: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "900",
    lineHeight: 24,
  },
  backtestHeroRow: {
    flexDirection: "row",
    gap: spacing.md,
  },
  backtestHeroMetric: {
    flex: 1,
    gap: spacing.xs,
  },
  backtestHeroMetricRight: {
    alignItems: "flex-end",
    flex: 1,
    gap: spacing.xs,
  },
  backtestLabel: {
    color: "#6C6C6C",
    fontSize: 13,
    fontWeight: "700",
    lineHeight: 18,
  },
  backtestHeroValue: {
    color: "#1A1A1A",
    fontSize: 24,
    fontWeight: "900",
    lineHeight: 30,
  },
  backtestMetricGrid: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  backtestMetricCell: {
    backgroundColor: "#F6F7F9",
    borderColor: "#E0E0E0",
    borderRadius: 10,
    borderWidth: 1,
    flex: 1,
    gap: spacing.xs,
    minWidth: 0,
    padding: spacing.sm,
  },
  backtestMetricLabel: {
    color: "#6C6C6C",
    fontSize: 12,
    fontWeight: "700",
    lineHeight: 16,
  },
  backtestMetricValue: {
    color: "#1A1A1A",
    fontSize: 14,
    fontWeight: "900",
    lineHeight: 18,
  },
  backtestMetaBox: {
    backgroundColor: "#F6F7F9",
    borderRadius: 12,
    gap: spacing.xs,
    padding: spacing.md,
  },
  tableCard: {
    ...elevatedCard,
    borderRadius: 16,
    gap: spacing.md,
    height: 360,
    overflow: "hidden",
    padding: spacing.lg,
    width: "100%",
  },
  tableTopRow: {
    alignItems: "flex-start",
    flexDirection: "column",
    gap: spacing.sm,
    justifyContent: "flex-start",
  },
  titleCluster: {
    flex: 1,
    gap: spacing.xs,
  },
  titleRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  cardTitle: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "900",
    lineHeight: 24,
  },
  controlScroller: {
    gap: spacing.sm,
    paddingRight: spacing.lg,
  },
  controlChip: {
    alignItems: "center",
    borderColor: "#E0E0E0",
    borderRadius: 999,
    borderWidth: 1,
    height: 32,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  controlChipActive: {
    backgroundColor: "#DFF8F5",
    borderColor: "#00C4B3",
  },
  controlText: {
    color: "#6C6C6C",
    fontWeight: "700",
  },
  controlTextActive: {
    color: "#008A80",
    fontWeight: "900",
  },
  filterChip: {
    alignItems: "center",
    backgroundColor: "#F6F7F9",
    borderRadius: 999,
    height: 32,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  filterText: {
    color: "#6C6C6C",
    fontWeight: "700",
  },
  tableShell: {
    borderColor: "#E0E0E0",
    borderRadius: 12,
    borderWidth: 1,
    minWidth: 0,
    overflow: "hidden",
  },
  tableHeader: {
    flexDirection: "row",
    height: 48,
  },
  stickyHeaderCell: {
    backgroundColor: "#F6F7F9",
    borderBottomColor: "#E0E0E0",
    borderBottomWidth: 1,
    height: 48,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    width: 148,
  },
  metricsScroller: {
    flex: 1,
    minWidth: 0,
  },
  tableBodyScroller: {
    height: 228,
  },
  tableScrollableBody: {
    flexDirection: "row",
  },
  fixedNameColumn: {
    width: 148,
  },
  tableHeaderText: {
    color: "#1A1A1A",
    fontSize: 13,
    fontWeight: "900",
    lineHeight: 18,
  },
  nameCell: {
    alignItems: "center",
    borderBottomColor: "#E0E0E0",
    borderBottomWidth: 1,
    flexDirection: "row",
    gap: spacing.sm,
    height: 76,
    paddingHorizontal: spacing.sm,
    width: 148,
  },
  selectedNameCell: {
    backgroundColor: "#F0F8F7",
  },
  rowAccent: {
    backgroundColor: "#00C4B3",
    borderRadius: 999,
    height: 30,
    width: 3,
  },
  smallAssetIcon: {
    alignItems: "center",
    backgroundColor: "#DFF8F5",
    borderRadius: 16,
    height: 32,
    justifyContent: "center",
    width: 32,
  },
  smallAssetIconText: {
    color: "#008A80",
    fontSize: 14,
    fontWeight: "900",
    lineHeight: 18,
  },
  nameTextBlock: {
    flex: 1,
  },
  holdingName: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "800",
    lineHeight: 20,
  },
  metricHeaderRow: {
    backgroundColor: "#F6F7F9",
    flexDirection: "row",
    height: 48,
  },
  metricHeaderCell: {
    borderBottomColor: "#E0E0E0",
    borderBottomWidth: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
    width: 104,
  },
  metricRow: {
    borderBottomColor: "#E0E0E0",
    borderBottomWidth: 1,
    flexDirection: "row",
    height: 76,
  },
  selectedMetricRow: {
    backgroundColor: "#F0F8F7",
  },
  metricCell: {
    borderLeftColor: "#E0E0E0",
    borderLeftWidth: 1,
    justifyContent: "center",
    paddingHorizontal: spacing.sm,
    width: 104,
  },
  metricPrimary: {
    color: "#1A1A1A",
    fontSize: 14,
    fontWeight: "900",
    lineHeight: 20,
  },
  negativeValue: {
    color: "#E01E5A",
  },
  positiveValue: {
    color: "#008A00",
  },
  detailCard: {
    ...elevatedCard,
    borderRadius: 24,
    gap: spacing.md,
    padding: 20,
  },
  detailCardMarker: {
    alignItems: "flex-start",
    flexDirection: "column",
    justifyContent: "flex-start",
    gap: spacing.md,
  },
  detailCardMarkerText: {
    color: "#6C6C6C",
    fontWeight: "800",
  },
  detailHeader: {
    alignItems: "center",
    flexDirection: "row",
    gap: spacing.md,
  },
  assetIcon: {
    alignItems: "center",
    backgroundColor: "#DFF8F5",
    borderRadius: 16,
    height: 32,
    justifyContent: "center",
    width: 32,
  },
  assetIconText: {
    color: "#008A80",
    fontSize: 16,
    fontWeight: "900",
    lineHeight: 20,
  },
  detailTitleBlock: {
    flex: 1,
    gap: spacing.xs,
  },
  detailNameRow: {
    alignItems: "center",
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  detailName: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "900",
    lineHeight: 24,
  },
  indicatorRow: {
    flexDirection: "row",
    flexWrap: "wrap",
    gap: spacing.sm,
  },
  indicatorChip: {
    alignItems: "center",
    borderColor: "#D5D5D5",
    borderRadius: 8,
    borderWidth: 1,
    height: 32,
    justifyContent: "center",
    paddingHorizontal: spacing.md,
  },
  indicatorChipActive: {
    backgroundColor: "#00C4B3",
    borderColor: "#00C4B3",
  },
  indicatorText: {
    color: "#6C6C6C",
    fontWeight: "800",
  },
  indicatorTextActive: {
    color: "#FFFFFF",
    fontWeight: "900",
  },
  chartFrame: {
    backgroundColor: "#101827",
    borderRadius: 16,
    minHeight: 196,
    overflow: "hidden",
    padding: spacing.lg,
  },
  chartGrid: {
    bottom: 0,
    justifyContent: "space-evenly",
    left: 0,
    padding: spacing.lg,
    position: "absolute",
    right: 0,
    top: 0,
  },
  gridLine: {
    backgroundColor: "#273449",
    height: 1,
  },
  chartEmptyState: {
    alignItems: "center",
    flex: 1,
    gap: spacing.sm,
    justifyContent: "center",
    minHeight: 164,
  },
  chartTitle: {
    color: "#FFFFFF",
    fontSize: 18,
    fontWeight: "900",
    lineHeight: 24,
    textAlign: "center",
  },
  chartBody: {
    color: "#AFAFAF",
    maxWidth: 280,
    textAlign: "center",
  },
  rangeRow: {
    flexDirection: "row",
    gap: spacing.sm,
  },
  rangeChip: {
    alignItems: "center",
    borderColor: "#E0E0E0",
    borderRadius: 8,
    borderWidth: 1,
    flex: 1,
    minHeight: mobile.touchTarget,
    justifyContent: "center",
  },
  rangeChipActive: {
    backgroundColor: "#DFF8F5",
    borderColor: "#00C4B3",
  },
  rangeText: {
    color: "#6C6C6C",
    fontWeight: "800",
  },
  rangeTextActive: {
    color: "#008A80",
    fontWeight: "900",
  },
  timeSlider: {
    gap: spacing.sm,
  },
  sliderTrack: {
    backgroundColor: "#E0E0E0",
    borderRadius: 999,
    height: 18,
    justifyContent: "center",
    overflow: "hidden",
  },
  sliderSelection: {
    alignSelf: "flex-end",
    backgroundColor: "#BDEDE8",
    height: 18,
    width: "68%",
  },
  leftHandle: {
    backgroundColor: "#00C4B3",
    borderRadius: 7,
    height: 14,
    left: "30%",
    position: "absolute",
    width: 14,
  },
  rightHandle: {
    backgroundColor: "#00C4B3",
    borderRadius: 7,
    height: 14,
    position: "absolute",
    right: 2,
    width: 14,
  },
  sliderLabels: {
    flexDirection: "row",
    justifyContent: "space-between",
  },
  metricsStrip: {
    gap: spacing.sm,
    paddingRight: spacing.lg,
  },
  miniMetric: {
    backgroundColor: "#F6F7F9",
    borderColor: "#E0E0E0",
    borderRadius: 8,
    borderWidth: 1,
    gap: spacing.xs,
    minHeight: mobile.touchTarget,
    padding: spacing.sm,
    width: 104,
  },
  miniMetricValue: {
    color: "#1A1A1A",
    fontSize: 16,
    fontWeight: "900",
    lineHeight: 20,
  },
  contextSection: {
    backgroundColor: "#F6F7F9",
    borderRadius: 12,
    gap: spacing.md,
    padding: spacing.lg,
  },
  contextHeader: {
    alignItems: "center",
    flexDirection: "row",
    justifyContent: "space-between",
    gap: spacing.md,
  },
  contextTitle: {
    color: "#1A1A1A",
    fontSize: 18,
    fontWeight: "900",
    lineHeight: 24,
  },
  contextItem: {
    gap: spacing.xs,
  },
  contextItemTitle: {
    color: "#1A1A1A",
    fontSize: 15,
    fontWeight: "900",
    lineHeight: 20,
  },
  contextMeta: {
    color: "#6C6C6C",
  },
  supportSection: {
    gap: spacing.md,
  },
});
