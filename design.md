# Flow Design

## Analyst Team
* Fundamentals Analyst：
    - evaluates company financial reports (latest 2 years)
* Sentiment Analyst:
    - Analyzes social media, news using sentiment scoring algorithm (latest 7 days)
* Technical Analyst:
    - Uses technical indicators to predict price movements, including MACD, RSI, Bollinger Bands, etc.

## Researcher Team
* Bullish researcher：assess the insights provided by the Analyst Team, evaluate the buy in reasons
* Bearish researcher：assess the insights provided by the Analyst Team, evaluate the sell or hold reasons
* Debate: debate on both sides

## Trading Team
* Trading team: Assess the insights provided by the Analyst Team and Researcher Team, and make a final decision on whether to buy, sell, or hold the stock.
    - Give the signal BUY/SELL/HOLD to provided equity
    - Give the timing when the signal is BUY/SELL

## Risk Management Team
* Evaluation of risk: Evaluate the risk of the investment, including the potential loss and the probability of loss.
* Final decision: Based on the risk evaluation, make a final decision on whether approve or reject the trading decision.
* If rejected, reprocess from Researcher Team once more.
* Stop process flow if rejected for more than 2 times.


# Inputs/Outputs

## Analyst Team
* Inputs
    - stock ticker
    - analyst period (default: 3 months)
* Outputs
    - insights provided by the Analyst Team

## Researcher Team
* Inputs
    - analyst period (default: 3 months)
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


# Architecture Design

