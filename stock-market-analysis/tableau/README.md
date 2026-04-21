# Tableau Dashboard - Sector Drill-Down Analysis

## Step-by-Step Instructions for Building Interactive Stock Market Visualizations

---

## 1. Data Connection

### Option A: Connect to PostgreSQL Database

1. Open **Tableau Desktop**
2. Under **Connect**, click **PostgreSQL**
3. Enter connection details:
   - **Server**: `localhost`
   - **Port**: `5432`
   - **Username**: Your PostgreSQL username
   - **Password**: Your PostgreSQL password
   - **Database**: `stock_analysis`
4. Click **Sign In**
5. Drag `equity_features` table to the canvas
6. Click **Sheet 1** to start building

### Option B: Connect to CSV File

1. Under **Connect**, click **Text File**
2. Navigate to `data/nse_bse_features.csv`
3. Click **Open**
4. Verify data preview
5. Tableau automatically detects data types

### Data Preparation

1. **Verify Data Types**:
   - `date`: Date
   - `symbol`, `sector`, `signal`: String (Abc)
   - All numeric fields: Number (123)

2. **Create Date Hierarchy**:
   - Right-click `date` field → **Create** → **Date Hierarchy**
   - Generates: Year, Quarter, Month, Day

---

## 2. Create Calculated Fields

Go to **Analysis** → **Create Calculated Field** for each:

### RSI Category
```tableau
IF [rsi_14] > 70 THEN "Overbought"
ELSEIF [rsi_14] < 30 THEN "Oversold"
ELSE "Neutral"
END
```

### Market Cap Proxy
```tableau
[VOLUME] * [close]
```

### Price Change %
```tableau
(ZN(LOOKUP([close], LAST())) - ZN(LOOKUP([close], FIRST()))) / 
ABS(ZN(LOOKUP([close], FIRST()))) * 100
```

### Daily Return %
```tableau
[daily_return] * 100
```

### Volatility Category
```tableau
IF [volatility_20d] > 0.40 THEN "High"
ELSEIF [volatility_20d] > 0.25 THEN "Medium"
ELSE "Low"
END
```

### MACD Trend
```tableau
IF [macd_hist] > 0 THEN "Bullish"
ELSE "Bearish"
END
```

### YTD Return (Table Calculation)
```tableau
// Right-click → Edit Table Calculation
// Compute Using: date
// Restarting Every: symbol
((ZN(LOOKUP([close], LAST())) - ZN(LOOKUP([close], FIRST()))) / 
 ABS(ZN(LOOKUP([close], FIRST())))) * 100
```

---

## 3. Build Sector Drill-Down Dashboard

### Dashboard Layout

```
┌────────────────────────────────────────────────────────────────┐
│  SECTOR DRILL-DOWN DASHBOARD                                   │
├──────────────────────────┬─────────────────────────────────────┤
│                          │                                     │
│   Treemap                │   Heat Map                          │
│   Market Cap by Sector   │   RSI Values (Sector × Stock)       │
│                          │                                     │
│                          │                                     │
├──────────────────────────┼─────────────────────────────────────┤
│                          │                                     │
│   Scatter Plot           │   Bar Chart                         │
│   Volatility vs Return   │   Top 10 Gainers & Losers           │
│   (Colored by Signal)    │   (April 2025)                      │
│                          │                                     │
├──────────────────────────┴─────────────────────────────────────┤
│                                                                  │
│   Detail View: Click sector → Individual Stock RSI/MACD         │
│   Line Charts with date filter                                  │
│                                                                  │
└────────────────────────────────────────────────────────────────┘
```

### Step 3.1: Treemap - Market Cap by Sector

1. **Create New Sheet** → Name: "Sector Market Cap"
2. Drag fields:
   - **Color**: `sector`
   - **Size**: SUM(`Market Cap Proxy`)
   - **Label**: `sector`, SUM(`Market Cap Proxy`)
3. Change mark type to **Treemap** (if not automatic)
4. Format:
   - **Title**: "Market Cap Distribution by Sector"
   - **Labels**: Center, Bold, 12pt
   - **Colors**: Custom palette (9 distinct colors)
   - **Tooltip**: Edit to show sector name, total market cap, stock count
5. Sort: Descending by size

### Step 3.2: Heat Map - RSI Values

1. **Create New Sheet** → Name: "RSI Heatmap"
2. Drag fields:
   - **Rows**: `sector`
   - **Columns**: `symbol`
   - **Color**: AVG(`rsi_14`)
3. Change mark type to **Square**
4. Format:
   - **Title**: "RSI Heatmap by Sector and Stock"
   - **Color Legend**: Diverging palette (Red-Green)
     - Red (0-30): Overbought
     - Yellow (30-70): Neutral
     - Green (70-100): Oversold
   - **Labels**: AVG(`rsi_14`), format to 1 decimal
   - **Font size**: 9pt for labels
5. Add reference lines:
   - Right-click color legend → **Edit Colors**
   - Add lines at 30 and 70

### Step 3.3: Scatter Plot - Volatility vs Daily Return

1. **Create New Sheet** → Name: "Risk-Return Scatter"
2. Drag fields:
   - **Columns**: AVG(`volatility_20d`)
   - **Rows**: AVG(`Daily Return %`)
   - **Color**: `signal`
   - **Size**: AVG(`volume`)
   - **Detail**: `symbol`
3. Format:
   - **Title**: "Risk vs Return by Signal"
   - **Colors**:
     - BUY: Green (#00B050)
     - SELL: Red (#FF0000)
     - HOLD: Gray (#A5A5A5)
   - **Size range**: 5px to 20px
   - **Axis labels**:
     - X: "Volatility (Annualized)"
     - Y: "Average Daily Return (%)"
4. Add trend line:
   - **Analytics** tab → Drag **Trend Line** → Linear
   - Show R-squared and p-value
5. Add quadrant lines:
   - X-axis: Average volatility (right-click → **Add Reference Line**)
   - Y-axis: 0% return

### Step 3.4: Bar Chart - Top 10 Gainers & Losers

1. **Create New Sheet** → Name: "Top Movers"
2. Create filter for April 2025:
   - Drag `date` to **Filters**
   - Select **Range of dates**
   - Set: April 1, 2025 to April 30, 2025
3. Calculate price change:
   - Use **YTD Return** calculated field
4. Drag fields:
   - **Rows**: `symbol`
   - **Columns**: SUM(`YTD Return`)
   - **Color**: `YTD Return` (diverging)
5. Create combined view:
   - Sort by YTD Return descending
   - Add dual axis for gainers and losers
   - Or create two separate sheets and combine in dashboard
6. Format:
   - **Title**: "Top 10 Gainers & Losers (April 2025)"
   - **Colors**: Green for positive, Red for negative
   - **Labels**: Show values on bars
   - **Sort**: Descending

### Step 3.5: Detail View - Individual Stock Analysis

1. **Create New Sheet** → Name: "Stock Detail RSI"
2. Drag fields:
   - **Columns**: `date` (continuous, exact date)
   - **Rows**: AVG(`rsi_14`)
   - **Color**: `symbol`
   - **Filter**: `sector` (add to Filters shelf)
3. Add reference bands:
   - **Analytics** tab → Drag **Reference Band**
   - Band from: 30 to 70
   - Label: "Neutral Zone"
   - Color: Light yellow
4. Add reference lines:
   - Line at 70 (Overbought) - Red dashed
   - Line at 30 (Oversold) - Green dashed
5. Format:
   - **Title**: "RSI Trend - <Sector>" (make dynamic)
   - **Lines**: 2px width
   - **Legend**: Show on right

6. **Create Second Sheet** → Name: "Stock Detail MACD"
   - **Columns**: `date`
   - **Rows**: SUM(`macd`), SUM(`macd_signal`) (dual axis)
   - **Color**: `symbol`
   - Add MACD histogram as bar chart on secondary axis

---

## 4. Assemble Dashboard

### Step 4.1: Create Dashboard

1. Click **New Dashboard** (bottom tab)
2. Set size: **Automatic** or **Fixed** (1920 × 1080)
3. Name: "Sector Drill-Down Dashboard"

### Step 4.2: Add Sheets to Dashboard

1. Drag "Sector Market Cap" to **top-left**
2. Drag "RSI Heatmap" to **top-right**
3. Drag "Risk-Return Scatter" to **middle-left**
4. Drag "Top Movers" to **middle-right**
5. Drag "Stock Detail RSI" and "Stock Detail MACD" to **bottom** (tabbed or side-by-side)

### Step 4.3: Add Interactivity (Action Filters)

1. **Dashboard** → **Actions** → **Add Action** → **Filter**
2. Configure:
   - **Source Sheets**: All sector-level sheets
   - **Target Sheets**: Detail view sheets
   - **Run action on**: Select
   - **Clearing selection**: Show all values
   - **Filter fields**: `sector`
3. Create second action for stock-level filtering:
   - **Source**: RSI Heatmap
   - **Target**: Detail view
   - **Filter fields**: `symbol`

### Step 4.4: Add Dashboard Filters

1. Click dropdown on any sheet → **Use as Filter**
2. Add global filters:
   - **Date Range**: Drag `date` to top of dashboard
   - **Sector**: Drag `sector` to right panel
   - **Signal**: Drag `signal` to right panel
3. Format filters:
   - Date: Relative date (Last 4 months)
   - Sector: Multiple values (dropdown)
   - Signal: Single value (buttons)

### Step 4.5: Add Titles and Text

1. **Dashboard** → **Add Text** (top)
2. Add title: "NSE/BSE Stock Market Analysis - Sector Drill-Down"
3. Add subtitle: "Jan 2025 - Apr 2025 | 50 Nifty Constituents"
4. Add instruction text: "Click any sector to view individual stock details"

---

## 5. Formatting & Polish

### Color Palette

Create custom color palette in **Help** → **Settings and Performance** → **Manage Color Palette**:

```xml
<color-palette name="Stock Analysis" type="regular">
  <color>#2E75B6</color>  <!-- IT - Blue -->
  <color>#00B050</color>  <!-- Banking - Green -->
  <color>#FFC000</color>  <!-- FMCG - Yellow -->
  <color>#FF6600</color>  <!-- Auto - Orange -->
  <color>#9933CC</color>  <!-- Pharma - Purple -->
  <color>#FF0000</color>  <!-- Energy - Red -->
  <color>#00B0F0</color>  <!-- Metals - Cyan -->
  <color>#C00000</color>  <!-- Realty - Dark Red -->
  <color>#7030A0</color>  <!-- Infra - Dark Purple -->
</color-palette>
```

### Tooltip Customization

For each sheet, edit tooltips to show relevant context:

**Scatter Plot Tooltip**:
```
<Symbol> <sector>
Signal: <signal>
Avg Daily Return: <AVG(daily_return)>%
Volatility: <AVG(volatility_20d)>%
RSI: <AVG(rsi_14)>
Volume: <AVG(volume)>
```

---

## 6. Publish to Tableau Public

### Step 6.1: Create Tableau Public Account

1. Visit: https://public.tableau.com
2. Click **Sign Up** (free account)
3. Verify email address

### Step 6.2: Publish Workbook

1. In Tableau Desktop: **File** → **Save to Tableau Public**
2. Sign in with Tableau Public credentials
3. Enter:
   - **Name**: "Stock Market Trend Analysis Dashboard"
   - **Description**: "Interactive analysis of 50 Nifty 50 stocks with technical indicators (RSI, MACD, Bollinger Bands) from Jan-Apr 2025"
   - **Tags**: stock-market, technical-analysis, nse, bse, nifty50, dashboard
4. Click **Save**
5. Copy public URL for sharing

### Step 6.3: Embed in Website (Optional)

1. Open published visualization on Tableau Public
2. Click **Share** button
3. Copy **Embed Code**
4. Paste into HTML:
```html
<div class='tableauPlaceholder' id='viz1234567890'>
  <noscript>
    <a href='https://public.tableau.com/...'>
      <img alt='Stock Market Dashboard' 
           src='https://public.tableau.com/static/...' 
           style='border: none' />
    </a>
  </noscript>
  <object class='tableauViz'>
    <param name='host_url' value='https%3A%2F%2Fpublic.tableau.com%2F' />
    <param name='embed_code_version' value='3' />
    <param name='site_root' value='' />
    <param name='name' value='StockMarketTrendAnalysis' />
    <param name='tabs' value='no' />
    <param name='toolbar' value='yes' />
    <param name='static_image' value='https://public.tableau.com/static/...' />
    <param name='animate_transition' value='yes' />
    <param name='display_static_image' value='yes' />
    <param name='display_spinner' value='yes' />
    <param name='display_overlay' value='yes' />
    <param name='display_count' value='yes' />
    <param name='filter' value='publish=yes' />
  </object>
</div>
```

---

## 7. Mock Screenshot Layout

```
┌────────────────────────────────────────────────────────────────────┐
│  SECTOR DRILL-DOWN DASHBOARD                                       │
│  NSE/BSE Stock Market Analysis | Jan-Apr 2025                      │
├─────────────────────────┬──────────────────────────────────────────┤
│  Market Cap by Sector   │  RSI Heatmap                             │
│                         │                                          │
│  ┌──────────────────┐   │  Sector  INFY  TCS  WIPRO  HCL  TECHM   │
│  │    Banking       │   │  IT       45   52   38    41    55      │
│  │   (35%)          │   │  Banking  62   58   65    59    61      │
│  ├──────────────────┤   │  Energy   71   68   74    69    72      │
│  │      IT          │   │  Pharma   42   39   44    40    43      │
│  │   (22%)          │   │  Auto     55   51   57    53    56      │
│  ├──────────────────┤   │  FMCG     48   46   50    47    49      │
│  │    Energy        │   │  Metals   67   63   69    65    68      │
│  │   (18%)          │   │  Realty   58   54                      │
│  └──────────────────┘   │  Infra    52   49   53    50    54      │
│                         │                                          │
│  Colors: █ Overbought    │  Legend: <30 Oversold | 30-70 Neutral   │
│          █ Neutral       │           >70 Overbought                │
│          █ Oversold      │                                          │
├─────────────────────────┼──────────────────────────────────────────┤
│  Risk vs Return         │  Top 10 Gainers & Losers (Apr 2025)     │
│                         │                                          │
│  Return ↑               │  Gainers:                                │
│    ■ BUY (green)        │  INFY    ██████████  +15.2%             │
│    ■ SELL (red)         │  TCS     ████████    +12.8%             │
│    ■ HOLD (gray)        │  HDFCBANK ██████      +10.5%             │
│                         │  RELIANCE ████        +8.3%              │
│    ·  ·  ·              │  SBIN    ███         +6.7%              │
│    ·  ·  ·              │                                          │
│    ·  ·  ·              │  Losers:                                 │
│  ─────┴──────→ Vol      │  DLF     ████████    -8.5%              │
│                         │  ADANIENT ██████      -6.2%              │
│  Quadrant:              │  JSWSTEEL ████        -4.8%              │
│  Top-Left: Low risk,    │  COALIND  ███         -3.5%              │
│  High return (Ideal)    │  TATASTEEL ██         -2.1%              │
├─────────────────────────┴──────────────────────────────────────────┤
│  DETAIL VIEW: Clicked on "IT Sector"                               │
│  ┌────────────────────────────┬───────────────────────────────────┐│
│  │  RSI Trend - IT Sector     │  MACD Trend - IT Sector           ││
│  │                            │                                   ││
│  │  100 ┤                     │  MACD    ┤                       ││
│  │   70 ┤---- Overbought ──── │  Signal  ┤                       ││
│  │   50 ┤  ──┐  ┌───          │  Hist    ┤  ███ █ ███            ││
│  │   30 ┤────┘  └─── Undersold│          ┤ ██   █   ██           ││
│  │    0 ┤                     │          ┤                       ││
│  │      Jan  Feb  Mar  Apr    │          Jan  Feb  Mar  Apr      ││
│  └────────────────────────────┴───────────────────────────────────┘│
│  Legend: INFY ─ TCS ── WIPRO ─ HCLTECH ── TECHM ─ LTIM            │
└────────────────────────────────────────────────────────────────────┘

FILTERS (Right Panel):
┌─────────────────────┐
│ Date Range          │
│ [Jan 1 ───|─── Apr 30] │
│                     │
│ Sector              │
│ [All Sectors ▼]     │
│ ☑ IT                │
│ ☑ Banking           │
│ ☑ Energy            │
│ ☑ Pharma            │
│ ☑ Auto              │
│ ☑ FMCG              │
│ ☑ Metals            │
│ ☑ Realty            │
│ ☑ Infra             │
│                     │
│ Signal              │
│ [BUY] [SELL] [HOLD] │
│                     │
│ RSI Category        │
│ [Overbought]        │
│ [Neutral]           │
│ [Oversold]          │
└─────────────────────┘
```

---

## 8. Troubleshooting

### Common Issues

**Issue**: Tableau cannot connect to PostgreSQL
- **Solution**: Verify PostgreSQL is running, check port 5432 is open, test connection with pgAdmin

**Issue**: Calculated fields showing NULL
- **Solution**: Check field names match exactly (case-sensitive), verify data types

**Issue**: Dashboard actions not working
- **Solution**: 
  - Dashboard → Actions → Verify source/target sheets
  - Ensure filter fields exist in both source and target
  - Check "Run action on" setting (Select/Hover/Menu)

**Issue**: Slow performance with large dataset
- **Solution**:
  - Use extracts instead of live connection
  - Aggregate data at sector level for overview sheets
  - Limit date range with filters
  - Disable "Show Me" recommendations

**Issue**: Publish to Tableau Public fails
- **Solution**: 
  - Check internet connection
  - Verify Tableau Public account credentials
  - Ensure workbook size < 15MB (Public limit)
  - Remove any sensitive data before publishing

---

## 9. Advanced Features

### Story Points

Create a narrative presentation:

1. **Story** → **New Story**
2. Add captions for each sheet:
   - "Market concentration: Banking and IT dominate Nifty 50"
   - "Energy sector shows overbought conditions in April"
   - "High-volatility stocks offer higher returns"
   - "Top gainers concentrated in IT and Banking"
3. Navigate through story in presentation mode

### Parameters

Create interactive what-if analysis:

1. **Analysis** → **Create Parameter**
2. Examples:
   - **RSI Threshold**: Integer, 0-100, default 70
   - **Volatility Level**: Float, 0.1-0.5, default 0.25
   - **Date Range**: Date, allow custom range
3. Use parameters in calculated fields for dynamic filtering

### Forecasting

1. Select time series chart
2. **Analytics** tab → Drag **Forecast** → Exponential Smoothing
3. Configure:
   - Forecast length: 3 months
   - Confidence interval: 95%
   - Aggregation: Average
4. Interpret results with caution (technical analysis is not predictive)

---

## Next Steps

1. Build dashboard following these instructions
2. Test all interactivity and filters
3. Take screenshots for project documentation
4. Publish to Tableau Public
5. Share link in README.md and portfolio
6. Present to stakeholders with Story Points
