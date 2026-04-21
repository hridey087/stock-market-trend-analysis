# Power BI Dashboard - Executive KPI Page

## Step-by-Step Instructions for Building the Stock Market Analysis Dashboard

---

## 1. Data Connection

### Option A: Connect to PostgreSQL Database (Recommended)

1. Open **Power BI Desktop**
2. Click **Home** → **Get Data** → **PostgreSQL database**
3. Enter connection details:
   - **Server**: `localhost`
   - **Database**: `stock_analysis`
4. Click **OK**
5. Select authentication method:
   - **Database**: Enter username and password
6. Select the `equity_features` table
7. Click **Transform Data** to open Power Query Editor

### Option B: Import CSV File

1. Click **Home** → **Get Data** → **Text/CSV**
2. Navigate to `data/nse_bse_features.csv`
3. Click **Open**
4. Verify data preview
5. Click **Transform Data**

### Power Query Transformations

In Power Query Editor:

1. **Set Data Types**:
   - `date`: Date
   - `open`, `high`, `low`, `close`: Decimal Number
   - `volume`: Whole Number
   - `rsi_14`, `macd`, `macd_signal`, `macd_hist`: Decimal Number
   - `sma_20`, `sma_50`, `sma_200`: Decimal Number
   - `bb_upper`, `bb_lower`, `bb_mid`: Decimal Number
   - `vol_zscore`, `daily_return`, `volatility_20d`: Decimal Number
   - `symbol`, `sector`, `signal`: Text

2. **Remove Duplicates**:
   - Select `date` and `symbol` columns
   - Right-click → **Remove Duplicates**

3. Click **Close & Apply** to load data

---

## 2. Create DAX Measures

Go to **Modeling** → **New Measure** and create the following measures:

### Total Records
```dax
Total Records = COUNTROWS(equity_features)
```

### Average RSI
```dax
Avg RSI = AVERAGE(equity_features[rsi_14])
```

### Buy Signal Percentage
```dax
Buy Signal % = 
DIVIDE(
    COUNTROWS(FILTER(equity_features, equity_features[signal] = "BUY")),
    COUNTROWS(equity_features)
)
```

### Sector Average Return
```dax
Sector Avg Return = 
AVERAGEX(equity_features, equity_features[daily_return]) * 100
```

### Nifty 50 Average Close
```dax
Nifty 50 Avg Close = AVERAGE(equity_features[close])
```

### Most Active Sector
```dax
Most Active Sector = 
TOPN(1, VALUES(equity_features[sector]), [Total Records])
```

### Total Volume
```dax
Total Volume = SUM(equity_features[volume])
```

### YTD Return
```dax
YTD Return = 
VAR FirstDate = CALCULATE(MIN(equity_features[date]), ALL(equity_features))
VAR LastDate = MAX(equity_features[date])
VAR FirstClose = CALCULATE(AVERAGE(equity_features[close]), equity_features[date] = FirstDate)
VAR LastClose = AVERAGE(equity_features[close])
RETURN
    DIVIDE(LastClose - FirstClose, FirstClose) * 100
```

---

## 3. Build Executive KPI Page

### Layout Structure

```
┌─────────────────────────────────────────────────────────────┐
│  [KPI Card]    [KPI Card]    [KPI Card]    [KPI Card]       │
│  Total Records  Nifty Avg    Buy Signal %  Most Active      │
│                            Close            Sector          │
├──────────────────────────────┬──────────────────────────────┤
│                              │                              │
│   Line Chart                 │   Bar Chart                  │
│   Nifty 50 Close vs          │   Sector-wise                │
│   SMA_20 vs SMA_50           │   YTD Returns                │
│                              │                              │
│                              │                              │
├──────────────────────────────┼──────────────────────────────┤
│                              │                              │
│   Stacked Bar Chart          │   Slicers Panel              │
│   Signal Distribution        │   - Date Range (Slider)      │
│   per Sector                 │   - Sector (Dropdown)        │
│                              │   - Signal (Buttons)         │
│                              │                              │
└──────────────────────────────┴──────────────────────────────┘
```

### Step 3.1: Create KPI Cards (Top Row)

1. Click **Insert** → **Card** visual
2. Create 4 cards:
   - **Card 1**: Drag `Total Records` measure
   - **Card 2**: Drag `Nifty 50 Avg Close` measure
   - **Card 3**: Drag `Buy Signal %` measure (Format as percentage)
   - **Card 4**: Drag `Most Active Sector` measure
3. Format each card:
   - **Background**: Light gray (#F2F2F2)
   - **Font size**: 24pt for value, 12pt for label
   - **Border**: Rounded corners, 2px border

### Step 3.2: Line Chart - Price vs Moving Averages

1. Click **Insert** → **Line chart**
2. Configure:
   - **X-axis**: `date`
   - **Y-axis**: `close`, `sma_20`, `sma_50` (add all three)
3. Format:
   - Title: "Nifty 50 Price vs Moving Averages"
   - Close line: Blue, 3px width
   - SMA_20 line: Orange, 2px width, dashed
   - SMA_50 line: Red, 2px width, dashed
   - Show markers: Off
   - Add legend at bottom

### Step 3.3: Bar Chart - Sector YTD Returns

1. Click **Insert** → **Clustered bar chart**
2. Configure:
   - **X-axis**: `Sector Avg Return` measure
   - **Y-axis**: `sector`
3. Format:
   - Title: "Sector-wise YTD Returns (%)"
   - Data colors: Conditional formatting
     - Positive returns: Green gradient
     - Negative returns: Red gradient
   - Show data labels: On
   - Sort descending

### Step 3.4: Stacked Bar Chart - Signal Distribution

1. Click **Insert** → **Stacked bar chart**
2. Configure:
   - **X-axis**: Count of records (Drag any field to Values)
   - **Y-axis**: `sector`
   - **Legend**: `signal`
3. Format:
   - Title: "Trading Signals by Sector"
   - Legend colors:
     - BUY: Green (#00B050)
     - SELL: Red (#FF0000)
     - HOLD: Gray (#A5A5A5)
   - Show percentage in data labels

### Step 3.5: Add Slicers (Right Panel)

1. Click **Insert** → **Slicer**
2. Create 3 slicers:

   **Date Range Slicer**:
   - Field: `date`
   - Format: Slider
   - Set default: Last 3 months

   **Sector Slicer**:
   - Field: `sector`
   - Format: Dropdown
   - Enable "Select All" option

   **Signal Slicer**:
   - Field: `signal`
   - Format: Buttons (horizontal)
   - Colors: BUY=Green, SELL=Red, HOLD=Gray

3. Arrange slicers vertically on the right side

---

## 4. Formatting & Polish

### Page-Level Settings

1. **Page Size**:
   - View → Page View → 16:9
   - Custom: 1920 × 1080 pixels

2. **Page Background**:
   - White (#FFFFFF)
   - Add subtle grid pattern (optional)

3. **Theme**:
   - View → Themes → Custom theme
   - Primary color: #2E75B6 (blue)
   - Secondary color: #00B050 (green)
   - Warning color: #FF0000 (red)

### Visual Interactions

1. Enable cross-filtering:
   - Click any sector in bar chart → filters all other visuals
   - Click date range → updates all time-based visuals

2. Disable unwanted interactions:
   - Format → Edit interactions
   - Set slicers to "Filter" mode (not highlight)

---

## 5. Export & Publish

### Export to PowerPoint

1. **File** → **Export** → **PowerPoint**
2. Choose "Export current page" or "All pages"
3. Review and adjust layout in PowerPoint

### Publish to Power BI Service

1. **File** → **Publish** → **Publish to Power BI**
2. Sign in to Power BI account (requires Pro license for sharing)
3. Select workspace
4. Access online at: https://app.powerbi.com

### Create Dashboard

1. In Power BI Service, open published report
2. Click **Pin visual** on key charts
3. Create new dashboard: "Stock Market Analysis"
4. Arrange pinned visuals
5. Set up data refresh schedule (if connected to PostgreSQL)

---

## 6. Mock Screenshot Layout

```
┌──────────────────────────────────────────────────────────────────┐
│  STOCK MARKET TREND ANALYSIS DASHBOARD                  [Date]   │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐        │
│  │  48,500  │  │  1,847   │  │   32.5%  │  │  Banking │        │
│  │  Total   │  │  Avg     │  │  Buy     │  │  Most    │        │
│  │ Records  │  │  Close   │  │ Signals │  │  Active  │        │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘        │
│                                                                  │
├──────────────────────────────────┬───────────────────────────────┤
│  Nifty 50 Price vs Moving Avg   │  Sector YTD Returns (%)       │
│                                  │                               │
│  |    /\\      Close             │  Banking  ████████ 12.5%     │
│  |   /  \\     SMA20             │  IT       ██████   10.2%     │
│  |  /    \\    SMA50             │  Energy   ████     8.1%      │
│  | /      \\                     │  Pharma   ███      6.3%      │
│  |/        \\                    │  Auto     ██       4.7%      │
│  |         \\                    │  FMCG     █        2.1%      │
│  +-------------------           │  Metals   █        1.8%      │
│  Jan   Feb   Mar   Apr          │  Realty              -1.2%    │
│                                  │  Infra               -3.5%    │
├──────────────────────────────────┼───────────────────────────────┤
│  Signal Distribution by Sector  │  FILTERS                      │
│                                  │                               │
│  Banking  [■■■□□] BUY SELL HOLD │  Date Range: [====|====]      │
│  IT       [■■■■□] BUY SELL HOLD │          Jan 1 - Apr 30       │
│  Energy   [■■■□□] BUY SELL HOLD │                               │
│  Pharma   [■■□□□] BUY SELL HOLD │  Sector: [All ▼]              │
│  Auto     [■■■□□] BUY SELL HOLD │         ☑ IT                  │
│  FMCG     [■■□□□] BUY SELL HOLD │         ☑ Banking             │
│  Metals   [■■■□□] BUY SELL HOLD │         ☑ Energy              │
│  Realty   [■□□□□] BUY SELL HOLD │         ☑ Pharma              │
│  Infra    [■■■□□] BUY SELL HOLD │         ☑ Auto                │
│                                  │         ☑ FMCG                │
│                                  │         ☑ Metals              │
│                                  │         ☑ Realty              │
│                                  │         ☑ Infra               │
│                                  │                               │
│                                  │  Signal: [BUY] [SELL] [HOLD] │
└──────────────────────────────────┴───────────────────────────────┘
```

---

## 7. Troubleshooting

### Common Issues

**Issue**: Cannot connect to PostgreSQL
- **Solution**: Verify PostgreSQL is running, check connection string, ensure firewall allows port 5432

**Issue**: DAX measures showing blank values
- **Solution**: Check column names match exactly, verify data types are correct

**Issue**: Slow report performance
- **Solution**: 
  - Use Import mode instead of DirectQuery for better performance
  - Remove unused columns in Power Query
  - Create date table for better time intelligence

**Issue**: Slicers not filtering visuals
- **Solution**: Check visual interactions (Format → Edit interactions), ensure slicer field exists in visual's data model

---

## 8. Additional Enhancements

### Advanced Features to Add

1. **Drill-through page**: Click sector → see individual stock details
2. **Tooltips**: Hover over chart → show RSI, MACD, Volume
3. **Bookmarks**: Save different views (e.g., "IT Sector Focus", "Banking Analysis")
4. **Annotations**: Add text boxes explaining key insights
5. **KPI indicators**: Add up/down arrows for trends
6. **Dynamic titles**: Update based on slicer selections

### DAX Time Intelligence

```dax
MTD Return = 
TOTALMTD(SUM(equity_features[daily_return]), equity_features[date])

QTD Return = 
TOTALQTD(SUM(equity_features[daily_return]), equity_features[date])

YoY Return = 
VAR CurrentYear = YEAR(MAX(equity_features[date]))
VAR PreviousYear = CurrentYear - 1
RETURN
    CALCULATE([YTD Return], YEAR(equity_features[date]) = PreviousYear)
```

---

## Next Steps

1. Build the dashboard following these instructions
2. Take screenshots of your completed dashboard
3. Replace placeholder images in main README.md
4. Share dashboard link with stakeholders
5. Set up automated data refresh (if using Power BI Service)
