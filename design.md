# Flow Design

## Analyst Team
* Fundamentals Analyst：
    - evaluates company financial reports
* Sentiment Analyst:
    - Analyzes social media, news using sentiment scoring algorithm
* Technical Analyst:
    - Uses technical indicators to predict price movements, including MACD, RSI, Bollinger Bands, etc.
* Special Analyst:
    - Assess the insights of some special topics.

## Researcher Team
* Bullish researcher：assess the insights provided by the Analyst Team, evaluate the buy in reasons
* Bearish researcher：assess the insights provided by the Analyst Team, evaluate the sell or hold reasons
* Debate: debate on both sides (bull/bear)

## Trading Team
* Trading team: Assess the insights provided by the Analyst Team and Researcher Team, and make a final decision on whether to buy, sell, or hold the stock.
    - Give the signal BUY/SELL/HOLD to provided equity
    - Give the timing when the signal is BUY/SELL

## Risk Management Team
* Evaluation of risk: Evaluate the risk of the investment, including the potential loss and the probability of loss.
* Final decision: Based on the risk evaluation, make a final decision on whether approve or reject the trading decision.


# Inputs/Outputs

## Analyst Team
* Inputs
    - stockSymbol (ticker)
    - investmentPeriod (short:within 1 month; medium: within 6 months; long: within 2 years)
* Outputs
    - insights provided by the Analyst Team

## Researcher Team
* Inputs
    - investmentPeriod (short:within 1 month; medium: within 6 months; long: within 2 years)
    - insights provided by the Analyst Team
* Outputs
    - debate result provided by the Researcher Team

## Trading Team
* Inputs
    - debate result provided by the Researcher Team
* Outputs
    - trading signal: BUY/SELL/HOLD
    - trading timing: when to BUY/SELL
    - reason for trading

## Risk Management Team
* Inputs
    - insights provided by the Analyst Team
    - debate result provided by the Researcher Team
    - trading signal by the Trading Team
    - trading timing by the Trading Team
* Outputs
    - risk evaluation: APPROVE/REJECT
    - reason for risk evaluation


# Logical Design

## Analyst Team
* Fundamentals Analyst
(1) Call alphavantage API to get stock fundamentals data
function=OVERVIEW
input: {stockSymbol}, {apiKey}
output: company information, financial ratios

function=ETF_PROFILE
input: {stockSymbol}, {apiKey}
output: net assets, expense ratio, and turnover

function=DIVIDENDS
input: {stockSymbol}, {apiKey}
output: dividend historical distributions

function=INCOME_STATEMENT
input: {stockSymbol}, {apiKey}
output: the annual and quarterly income statements

function=BALANCE_SHEET
input: {stockSymbol}, {apiKey}
output: the annual and quarterly balance sheets

function=CASH_FLOW
input: {stockSymbol}, {apiKey}
output: the annual and quarterly cash flow

function=EARNINGS_ESTIMATES
input: {stockSymbol}, {apiKey}
output: the annual and quarterly earnings (EPS) and revenue estimates

(2) return the financial summary report based on fundamentals data
User prompt: "Please summarize the financial data of {stockSymbol} based on: {outputOfOverview},
{outputOfETFProfile}, {outputOfDividends}, {outputOfIncomeStatement}, {outputOfBalanceSheet}, {outputOfCashFlow}, {outputOfEarningsEstimates}."
System prompt: "You are a helpful AI assistant."

* Sentiment Analyst
(1) Call alphavantage API to get news data
function=NEWS_SENTIMENT
input: {stockSymbol}, {apiKey}, {time_from}, {time_to}, {sort}, {limit}
time_from: today - 14 days
time_to: today
sort: LATEST
limit: 30
output: news data

(2) return the news sentiment analysis report based on news data
User prompt: "Please sentiment analysis on the news data."
System prompt: "You are a news sentiment researcher tasked with analyzing news and trends."

* Technical Analyst
(1) Call alphavantage API to get technical indicators
function=SMA
input: {stockSymbol}, {apiKey}, {interval}, {time_period}, {series_type}
interval: "30min" when investmentPeriod=short; "daily" when investmentPeriod=medium; "weekly" when investmentPeriod=long
time_period: e.g. 30, 60
series_type: close
output: simple moving average indicators
Prepare close_50_sm (time_period=50), close_200_sma (time_period=200)

function=EMA
input: {stockSymbol}, {apiKey}, {interval}, {time_period}, {series_type}
interval: "30min" when investmentPeriod=short; "daily" when investmentPeriod=medium; "weekly" when investmentPeriod=long
time_period: e.g. 30, 60
series_type: close
output: exponential moving average indicators
Prepare close_10_ema (time_period=10)

Calculate MACD
call Yahoo Finance API
data['MACD'] = data['EMA12'] - data['EMA26']

Calculate MACD Signal
data['Signal_Line'] = data['MACD'].ewm(span=9, adjust=False).mean()

function=RSI
input: {stockSymbol}, {apiKey}, {interval}, {time_period}, {series_type}
output: relative strength index indicators

function=BBANDS
input: {stockSymbol}, {apiKey}, {interval}, {time_period}, {series_type}
output: bollinger bands indicators

Calculate VWAP (Volume Weighted Average Price)
call Yahoo Finance API
data['cum_price_volume'] = (data['Close'] * data['Volume']).cumsum()
data['cum_volume'] = data['Volume'].cumsum()
data['VWAP'] = data['cum_price_volume'] / data['cum_volume']

(2) return the technical analysis report based on technical indicators
User prompt: "Please return the technical analysis report based on technical indicators."
System prompt: "You are a technical indicators researcher."

* Special Analyst
(1) Call alphavantage API to get insider transactions
function=INSIDER_TRANSACTIONS
input: {stockSymbol}, {apiKey}
output: insider transactions of the stock ticker

## Researcher Team
* Bullish researcher
User prompt: "provide a bullish analysis for {stockSymbol}"
Resources available:
Company fundamentals report: {fundamentals_report}
news sentiment report: {sentiment_report}
Market research report: {technical_research_report}
Report history of the debate: {memory}
Use this information to deliver a compelling bull argument, refute the bear's concerns, and engage in a dynamic debate that demonstrates the strengths of the bull position. You must also address reflections and learn from lessons and mistakes you made in the past."

System prompt: "You are a Bull Analyst advocating for investing in the stock. Your task is to build a strong, evidence-based case emphasizing growth potential, competitive advantages, and positive market indicators. Leverage the provided research and data to address concerns and counter bearish arguments effectively.

Key points to focus on:
- Growth Potential: Highlight the company's market opportunities, revenue projections, and scalability.
- Competitive Advantages: Emphasize factors like unique products, strong branding, or dominant market positioning.
- Positive Indicators: Use financial health, industry trends, and recent positive news as evidence.
- Bear Counterpoints: Critically analyze the bear argument with specific data and sound reasoning, addressing concerns thoroughly and showing why the bull perspective holds stronger merit.
- Engagement: Present your argument in a conversational style, engaging directly with the bear analyst's points and debating effectively rather than just listing data."

* Bearish researcher
User prompt: "provide a bearish analysis for {stockSymbol}"
Resources available:
Company fundamentals report: {fundamentals_report}
news sentiment report: {sentiment_report}
Market research report: {technical_research_report}
Report history of the debate: {memory}
Use this information to deliver a compelling bear argument, refute the bull's claims, and engage in a dynamic debate that demonstrates the risks and weaknesses of investing in the stock. You must also address reflections and learn from lessons and mistakes you made in the past."

System prompt: "You are a Bear Analyst making the case against investing in the stock. Your goal is to present a well-reasoned argument emphasizing risks, challenges, and negative indicators. Leverage the provided research and data to highlight potential downsides and counter bullish arguments effectively.

Key points to focus on:
- Risks and Challenges: Highlight factors like market saturation, financial instability, or macroeconomic threats that could hinder the stock's performance.
- Competitive Weaknesses: Emphasize vulnerabilities such as weaker market positioning, declining innovation, or threats from competitors.
- Negative Indicators: Use evidence from financial data, market trends, or recent adverse news to support your position.
- Bull Counterpoints: Critically analyze the bull argument with specific data and sound reasoning, exposing weaknesses or over-optimistic assumptions.
- Engagement: Present your argument in a conversational style, directly engaging with the bull analyst's points and debating effectively rather than simply listing facts.
"

* Debate
User prompt: "provide debate result based on both bullish analysis and bearish analysis"

## Trading Team
User prompt: "provide trader_plan including:
    - trading signal: BUY/SELL/HOLD
    - trading timing: when/what price to BUY/SELL
    - reason for trading"
System prompt: "You are a trading agent analyzing market data to make investment decisions. Based on your analysis, always include the following key information in your analysis:
1. **PROPOSAL**: **BUY/HOLD/SELL**' to confirm your recommendation.
2. **TARGET PRICE**: A 3-month mid-term forecast target price with currency based on analysis - Require: 1) provide a specific value; 2) the target price should be reasonable and its fluctuation does not exceed ±30% of the latest closing price - {close_price}.
3. **CONFIDENCE**: The degree of confidence in the decision (between 0 and 1)
4. **RISK SCORE**: Investment risk level (between 0 and 1, 0 is low risk and 1 is high risk)
5. **LAST CLOSE PRICE**: {close_price}
6. **RATIONALE**: A brief explanation of the reasoning behind the decision.

Target Price Calculation Guidelines:
- Based on valuation data from fundamental analysis
- Reference support and resistance levels from technical analysis
- Consider industry average valuations
- Incorporate market sentiment and news impact
- Even if market sentiment is overheated, target prices should be based on reasonable valuations.

Do not forget to utilize lessons from past decisions to learn from your mistakes. Here is some reflections from similar situations you traded in and the lessons learned: {past_memory_lession_learned}"

## Risk Management Team
User prompt: "provide risk_plan including:
    - risky risk analysis
    - neutral risk analysis
    - safe risk analysis
    - final risk evaluation: APPROVE/REJECT
    - reason for risk evaluation"
System prompt: "
As the Risk Management Judge and Debate Facilitator, your goal is to evaluate the debate between three risk analysts—Risky, Neutral, and Safe. Determine the best course of action for the trader. Choose Hold only if strongly justified by specific arguments, not as a fallback when all sides seem valid. Strive for clarity and decisiveness.

Guidelines for Decision-Making:
1. **Summarize Key Arguments**: Extract the strongest points from each analyst, focusing on relevance to the context.
2. **Provide Rationale**: Support your recommendation with direct quotes and counterarguments from the debate.
3. **Refine the Trader's Plan**: Start with the trader's original plan, **{trader_plan}**, and adjust it based on the analysts' insights.
4. **Learn from Past Mistakes**: Use lessons from **{past_memory_lession_learned}** to address prior misjudgments and improve the decision you are making now to make sure you don't make a wrong BUY/SELL/HOLD call that loses money.
"

## utils
Calculate close_price
call Yahoo Finance API to get close_price

lesson learner
(1) Store the final report in a vector database as memory with the analysis datetime
(2) compare the last report in memory with the actual closed market price based on the analysis datetime, to get the lesson learned
User prompt: "compare the last report in memory with the actual closed market price based on the analysis datetime, to get the lesson learned"
(3) Store the lesson learned in a vector database as past_memory_lession_learned with the analysis datetime

# UI
(1) Use CLI to interact with the system
(2) user input the stock symbol (e.g.GOOG), investment period (i.e.SHORT/MEDIUM/LONG)
(3) system output to the console and the result file
    - financial summary report
    - news sentiment analysis report
    - technical analysis report
    - insider transactions
    - bullish analysis
    - bearish analysis
    - debate result
    - trading plan
    - risk plan
    Note: for each report to the console, limit the output to within 500 words

# Appendix: Model
OpenRouter Model
API Key: OPENROUTER_API_KEY set in .env file
Model: set in .env file

# Appendix: API Information

alphavantage API
API Key: ALPHA_VANTAGE_API_KEY set in .env file
API documentation: https://www.alphavantage.co/documentation/#intelligence

Yahoo Finance API
API documentation: https://ranaroussi.github.io/yfinance/reference/index.html

# Appendix: storage
Vector database: Milvus
Result file path: set in .env file. Default name: result_<yyyymmdd_HH24MI>.log

# Appendix: agents
Multiples agents:
- Fundamentals Analyst Agent
- Sentiment Analyst Agent
- Technical Analyst Agent
- Special Analyst Agent
- Bullish researcher Agent
- Bearish researcher Agent
- Debate Agent
- Trading Agent
- Risk Management Agent

Agent framework: LangGraph