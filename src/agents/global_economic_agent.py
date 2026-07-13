import requests
from datetime import datetime, timedelta


class GlobalEconomicAnalyst:
    """Fetches global economic data from World Bank API."""

    # World Bank indicators
    INDICATORS = {
        'cpi': 'FP.CPI.TOTL',           # Consumer Price Index
        'inflation': 'FP.CPI.TOTL.ZG',   # Inflation (annual %)
        'gdp_growth': 'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
        'gdp_per_capita': 'NY.GDP.PCAP.CD',  # GDP per capita (current US$)
        'unemployment': 'SL.UEM.TOTL.ZS',    # Unemployment (% of total labor force)
        'interest_rate': 'FR.INR.RINR',      # Real interest rate (%)
        'trade_balance': 'BN.CAB.XOKA.CD',   # Current account balance (current US$)
        'debt_to_gdp': 'GC.DOD.TOTL.GD.ZS', # Central government debt (% of GDP)
    }

    # Major economies to track
    MAJOR_ECONOMIES = {
        'US': 'United States',
        'CN': 'China',
        'JP': 'Japan',
        'DE': 'Germany',
        'GB': 'United Kingdom',
    }

    def __init__(self):
        self.base_url = 'https://api.worldbank.org/v2'

    def _fetch_indicator(self, indicator_code: str, country_code: str, periods: int = 4) -> list:
        """Fetch indicator data for a specific country."""
        url = f'{self.base_url}/country/{country_code}/indicator/{indicator_code}'
        params = {
            'format': 'json',
            'per_page': periods,
            'mrv': periods  # Most recent values
        }

        try:
            response = requests.get(url, params=params, timeout=15)
            if response.status_code == 200:
                data = response.json()
                if len(data) > 1 and data[1]:
                    return [
                        {
                            'date': item.get('date'),
                            'value': item.get('value'),
                            'country': item.get('country', {}).get('value')
                        }
                        for item in data[1] if item.get('value') is not None
                    ]
            return []
        except Exception as e:
            print(f'WARNING: Could not fetch {indicator_code} for {country_code}: {str(e)[:50]}')
            return []

    def _get_period_label(self, investment_period: str) -> str:
        """Get display label for the investment period."""
        period_map = {
            'short+': '1-7 days',
            'short': '1-4 weeks',
            'medium': '1-6 months',
            'long': '6+ months'
        }
        return period_map.get(investment_period, investment_period)

    def _get_data_points(self, investment_period: str) -> int:
        """Determine how many data points to fetch based on period."""
        period_map = {
            'short+': 2,
            'short': 3,
            'medium': 4,
            'long': 6
        }
        return period_map.get(investment_period, 4)

    def analyze(self, investment_period: str = 'medium') -> str:
        """Analyze global economic conditions."""
        print(f'DEBUG: GlobalEconomicAnalyst analyzing with period {investment_period}')

        period_label = self._get_period_label(investment_period)
        data_points = self._get_data_points(investment_period)

        report_sections = []

        # Header
        report_sections.append(f"""## Global Economic Analysis

**Analysis Period:** {period_label}
**Data Source:** World Bank API

---""")

        # Fetch all indicators for all countries in parallel
        from concurrent.futures import ThreadPoolExecutor, as_completed

        fetch_tasks = {}
        for country_code, country_name in self.MAJOR_ECONOMIES.items():
            for indicator_name, indicator_code in self.INDICATORS.items():
                key = (country_code, country_name, indicator_name, indicator_code)
                fetch_tasks[key] = None

        results = {}
        with ThreadPoolExecutor(max_workers=8) as executor:
            futures = {
                executor.submit(self._fetch_indicator, ic, cc, dp): (cc, cn, iname, ic)
                for (cc, cn, iname, ic), dp in [
                    (k, data_points) for k in fetch_tasks
                ]
            }
            for future in as_completed(futures):
                cc, cn, iname, ic = futures[future]
                try:
                    data = future.result()
                    results[(cc, iname)] = data
                except Exception:
                    results[(cc, iname)] = []

        # Build report sections from fetched data
        for country_code, country_name in self.MAJOR_ECONOMIES.items():
            section = f"\n### {country_name} ({country_code})\n"

            indicators_data = []
            for indicator_name, indicator_code in self.INDICATORS.items():
                data = results.get((country_code, indicator_name), [])
                if data:
                    latest = data[0]
                    prev = data[1] if len(data) > 1 else None

                    # Calculate change if previous value exists
                    change_str = ""
                    if prev and prev['value'] and latest['value']:
                        change = latest['value'] - prev['value']
                        change_str = f" (Δ {change:+.2f})"

                    indicators_data.append({
                        'name': indicator_name.replace('_', ' ').title(),
                        'value': latest['value'],
                        'date': latest['date'],
                        'change': change_str
                    })

            if indicators_data:
                # Create table
                section += "\n| Indicator | Value | Period | Change |\n"
                section += "|-----------|-------|--------|--------|\n"
                for item in indicators_data:
                    value_str = f"{item['value']:.2f}" if item['value'] else "N/A"
                    section += f"| {item['name']} | {value_str} | {item['date']} | {item['change']} |\n"
            else:
                section += "\n*No data available for this period*\n"

            report_sections.append(section)

        # Add summary section
        report_sections.append("""
---

### Key Takeaways

*Analysis based on latest available World Bank data for major economies.*
*Data may include reporting lags (typically 1-3 months for most indicators).*
""")

        return '\n'.join(report_sections)


def get_global_economic_analysis(investment_period: str = 'medium') -> str:
    """Convenience function to get global economic analysis."""
    analyst = GlobalEconomicAnalyst()
    return analyst.analyze(investment_period)
