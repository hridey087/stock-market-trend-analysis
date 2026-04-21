/**
 * Google Apps Script - ETL Automation for Stock Market Analysis
 * 
 * This script runs daily at 8:00 AM IST to:
 * 1. Fetch latest stock data from Flask API
 * 2. Update Google Sheets with raw data, signals, and summaries
 * 3. Apply conditional formatting
 * 4. Send email summary to stakeholders
 * 5. Log ETL run status
 * 
 * Author: Stock Analysis Team
 * Version: 1.0.0
 */

// ============================================================
// CONFIGURATION
// ============================================================

const CONFIG = {
  // Flask API endpoint (update with your deployed URL)
  FLASK_API_URL: 'https://your-flask-api.herokuapp.com',
  
  // Google Sheet ID (extract from sheet URL)
  SHEET_ID: 'your-google-sheet-id-here',
  
  // Stakeholder email for summary reports
  STAKEHOLDER_EMAIL: 'team@company.com',
  
  // Retry settings
  RETRY_ATTEMPTS: 3,
  RETRY_DELAY_MS: 5000,
  
  // Sheet names
  SHEET_NAMES: {
    RAW_DATA: 'Raw_Data',
    SIGNALS: 'Signals',
    SECTOR_SUMMARY: 'Sector_Summary',
    INDEX_VIEW: 'Index_View',
    LOGS: 'Logs'
  }
};


// ============================================================
// MAIN ETL FUNCTION
// ============================================================

/**
 * Main ETL function - runs daily via time-based trigger
 * Fetches data, updates sheets, sends email summary
 */
function runDailyETL() {
  const startTime = new Date();
  Logger.log('========================================');
  Logger.log('ETL RUN STARTED: ' + startTime.toString());
  Logger.log('========================================');
  
  try {
    // Initialize spreadsheet
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    ensureSheetsExist(ss);
    
    // Step 1: Fetch latest data from API
    Logger.log('[1/5] Fetching latest data from API...');
    const latestData = fetchDataFromAPI('/api/latest');
    
    if (!latestData || !latestData.data || latestData.data.length === 0) {
      throw new Error('No data received from API');
    }
    
    Logger.log('Received ' + latestData.data.length + ' records');
    
    // Step 2: Fetch trading signals
    Logger.log('[2/5] Fetching trading signals...');
    const signalsData = fetchDataFromAPI('/api/signals?signal=BUY,SELL');
    
    // Step 3: Fetch sector summary
    Logger.log('[3/5] Fetching sector summary...');
    const sectorData = fetchDataFromAPI('/api/sector-summary');
    
    // Step 4: Write data to sheets
    Logger.log('[4/5] Writing data to Google Sheets...');
    writeToRawDataSheet(ss, latestData.data);
    writeToSignalsSheet(ss, signalsData ? signalsData.data : []);
    writeToSectorSummarySheet(ss, sectorData ? sectorData.data : []);
    writeToIndexViewSheet(ss, latestData.data);
    
    // Step 5: Apply formatting and send email
    Logger.log('[5/5] Applying formatting and sending summary...');
    applyConditionalFormatting(ss);
    
    // Calculate statistics
    const stats = calculateStatistics(latestData.data, signalsData ? signalsData.data : []);
    
    // Send summary email
    sendSummaryEmail(stats);
    
    // Log successful run
    const endTime = new Date();
    const duration = (endTime - startTime) / 1000; // seconds
    logETLRun(ss, 'SUCCESS', latestData.data.length, duration);
    
    Logger.log('========================================');
    Logger.log('ETL RUN COMPLETED SUCCESSFULLY');
    Logger.log('Duration: ' + duration.toFixed(2) + ' seconds');
    Logger.log('Records processed: ' + latestData.data.length);
    Logger.log('========================================');
    
  } catch (error) {
    Logger.log('ETL RUN FAILED: ' + error.toString());
    handleError(error, 'runDailyETL');
    
    // Log failed run
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    logETLRun(ss, 'FAILED: ' + error.toString(), 0, 0);
  }
}


// ============================================================
// API DATA FETCHING
// ============================================================

/**
 * Fetch data from Flask API with retry logic
 * 
 * @param {string} endpoint - API endpoint path
 * @return {Object} Parsed JSON response
 */
function fetchDataFromAPI(endpoint) {
  const url = CONFIG.FLASK_API_URL + endpoint;
  
  for (let attempt = 1; attempt <= CONFIG.RETRY_ATTEMPTS; attempt++) {
    try {
      Logger.log('API Request (attempt ' + attempt + '): ' + url);
      
      const options = {
        'method': 'get',
        'muteHttpExceptions': true,
        'followRedirects': true
      };
      
      const response = UrlFetchApp.fetch(url, options);
      const responseCode = response.getResponseCode();
      
      if (responseCode === 200) {
        const data = JSON.parse(response.getContentText());
        Logger.log('API request successful');
        return data;
      } else {
        Logger.log('API returned status code: ' + responseCode);
        if (attempt < CONFIG.RETRY_ATTEMPTS) {
          Utilities.sleep(CONFIG.RETRY_DELAY_MS * attempt);
        }
      }
    } catch (error) {
      Logger.log('API request failed (attempt ' + attempt + '): ' + error.toString());
      if (attempt < CONFIG.RETRY_ATTEMPTS) {
        Utilities.sleep(CONFIG.RETRY_DELAY_MS * attempt);
      } else {
        throw new Error('API request failed after ' + CONFIG.RETRY_ATTEMPTS + ' attempts: ' + error.toString());
      }
    }
  }
  
  return null;
}


// ============================================================
// SHEET WRITE OPERATIONS
// ============================================================

/**
 * Write raw OHLCV data to Raw_Data sheet
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 * @param {Array} data - Array of stock data records
 */
function writeToRawDataSheet(ss, data) {
  Logger.log('Writing to Raw_Data sheet...');
  
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAMES.RAW_DATA);
  
  // Clear existing data
  sheet.clear();
  
  if (data.length === 0) {
    sheet.getRange(1, 1).setValue('No data available');
    return;
  }
  
  // Prepare headers
  const headers = Object.keys(data[0]);
  const headerRow = headers.map(h => h.charAt(0).toUpperCase() + h.slice(1));
  
  // Prepare data rows
  const rows = data.map(record => {
    return headers.map(header => {
      const value = record[header];
      // Convert null/undefined to empty string
      return (value === null || value === undefined) ? '' : value;
    });
  });
  
  // Write to sheet
  sheet.getRange(1, 1, 1, headers.length).setValues([headerRow])
       .setFontWeight('bold')
       .setBackground('#4472C4')
       .setFontColor('#FFFFFF');
  
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  
  // Auto-fit columns
  sheet.autoResizeColumns(1, headers.length);
  
  Logger.log('Raw_Data sheet updated: ' + data.length + ' rows');
}


/**
 * Write BUY/SELL signals to Signals sheet
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 * @param {Array} data - Array of signal records
 */
function writeToSignalsSheet(ss, data) {
  Logger.log('Writing to Signals sheet...');
  
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAMES.SIGNALS);
  sheet.clear();
  
  if (data.length === 0) {
    sheet.getRange(1, 1).setValue('No signals available');
    return;
  }
  
  // Select relevant columns
  const columns = ['date', 'symbol', 'sector', 'close', 'rsi_14', 'macd', 'macd_signal', 'macd_hist', 'signal'];
  const headers = columns.map(h => h.charAt(0).toUpperCase() + h.slice(1));
  
  const rows = data.map(record => {
    return columns.map(col => {
      const value = record[col];
      return (value === null || value === undefined) ? '' : value;
    });
  });
  
  // Write headers
  sheet.getRange(1, 1, 1, columns.length).setValues([headers])
       .setFontWeight('bold')
       .setBackground('#4472C4')
       .setFontColor('#FFFFFF');
  
  // Write data
  sheet.getRange(2, 1, rows.length, columns.length).setValues(rows);
  
  sheet.autoResizeColumns(1, columns.length);
  
  Logger.log('Signals sheet updated: ' + data.length + ' rows');
}


/**
 * Write sector summary to Sector_Summary sheet
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 * @param {Array} data - Array of sector summary records
 */
function writeToSectorSummarySheet(ss, data) {
  Logger.log('Writing to Sector_Summary sheet...');
  
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAMES.SECTOR_SUMMARY);
  sheet.clear();
  
  if (data.length === 0) {
    sheet.getRange(1, 1).setValue('No sector data available');
    return;
  }
  
  const headers = Object.keys(data[0]).map(h => h.charAt(0).toUpperCase() + h.slice(1));
  const rows = data.map(record => Object.values(record));
  
  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
       .setFontWeight('bold')
       .setBackground('#4472C4')
       .setFontColor('#FFFFFF');
  
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  sheet.autoResizeColumns(1, headers.length);
  
  Logger.log('Sector_Summary sheet updated: ' + data.length + ' rows');
}


/**
 * Write Nifty 50 index view (aggregated daily data)
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 * @param {Array} data - Array of all stock records
 */
function writeToIndexViewSheet(ss, data) {
  Logger.log('Writing to Index_View sheet...');
  
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAMES.INDEX_VIEW);
  sheet.clear();
  
  if (data.length === 0) {
    sheet.getRange(1, 1).setValue('No index data available');
    return;
  }
  
  // Aggregate by date
  const dateMap = {};
  data.forEach(record => {
    const date = record.date;
    if (!dateMap[date]) {
      dateMap[date] = {
        date: date,
        stocks_traded: 0,
        total_volume: 0,
        sum_close: 0,
        buy_count: 0,
        sell_count: 0,
        hold_count: 0
      };
    }
    dateMap[date].stocks_traded += 1;
    dateMap[date].total_volume += (record.volume || 0);
    dateMap[date].sum_close += (record.close || 0);
    if (record.signal === 'BUY') dateMap[date].buy_count += 1;
    if (record.signal === 'SELL') dateMap[date].sell_count += 1;
    if (record.signal === 'HOLD') dateMap[date].hold_count += 1;
  });
  
  // Convert to array
  const aggregatedData = Object.values(dateMap).map(d => ({
    ...d,
    avg_close: (d.sum_close / d.stocks_traded).toFixed(2)
  }));
  
  const headers = ['Date', 'Stocks Traded', 'Total Volume', 'Avg Close', 'Buy Signals', 'Sell Signals', 'Hold Signals'];
  const rows = aggregatedData.map(d => [
    d.date, d.stocks_traded, d.total_volume, d.avg_close,
    d.buy_count, d.sell_count, d.hold_count
  ]);
  
  sheet.getRange(1, 1, 1, headers.length).setValues([headers])
       .setFontWeight('bold')
       .setBackground('#4472C4')
       .setFontColor('#FFFFFF');
  
  sheet.getRange(2, 1, rows.length, headers.length).setValues(rows);
  sheet.autoResizeColumns(1, headers.length);
  
  Logger.log('Index_View sheet updated: ' + aggregatedData.length + ' rows');
}


// ============================================================
// FORMATTING & VISUALIZATION
// ============================================================

/**
 * Apply conditional formatting to sheets
 * Green for BUY, Red for SELL, Gray for HOLD
 */
function applyConditionalFormatting(ss) {
  Logger.log('Applying conditional formatting...');
  
  // Format Signals sheet
  const signalsSheet = ss.getSheetByName(CONFIG.SHEET_NAMES.SIGNALS);
  const signalsRange = signalsSheet.getDataRange();
  const signalColumnIndex = 9; // Column I (signal column)
  
  // Find signal column dynamically
  const headers = signalsSheet.getRange(1, 1, 1, signalsSheet.getLastColumn()).getValues()[0];
  const signalCol = headers.indexOf('Signal') + 1; // 1-based index
  
  if (signalCol > 0) {
    // Clear existing conditional format rules
    const rules = signalsSheet.getConditionalFormatRules();
    signalsSheet.setConditionalFormatRules([]);
    
    // Create new rules
    const newRules = [
      // BUY - Green
      SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$' + columnLetter(signalCol) + '2="BUY"')
        .setBackground('#d9ead3')
        .setRanges([signalsRange])
        .build(),
      
      // SELL - Red
      SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$' + columnLetter(signalCol) + '2="SELL"')
        .setBackground('#f4cccc')
        .setRanges([signalsRange])
        .build(),
      
      // HOLD - Gray
      SpreadsheetApp.newConditionalFormatRule()
        .whenFormulaSatisfied('=$' + columnLetter(signalCol) + '2="HOLD"')
        .setBackground('#efefef')
        .setRanges([signalsRange])
        .build()
    ];
    
    signalsSheet.setConditionalFormatRules(newRules);
    Logger.log('Conditional formatting applied to Signals sheet');
  }
}


/**
 * Convert column number to letter (1=A, 2=B, 26=Z, 27=AA)
 * 
 * @param {number} num - Column number (1-based)
 * @return {string} Column letter
 */
function columnLetter(num) {
  let letter = '';
  while (num > 0) {
    num--;
    letter = String.fromCharCode(65 + (num % 26)) + letter;
    num = Math.floor(num / 26);
  }
  return letter;
}


// ============================================================
// STATISTICS & EMAIL
// ============================================================

/**
 * Calculate summary statistics from data
 * 
 * @param {Array} allData - All stock records
 * @param {Array} signals - Signal records
 * @return {Object} Statistics object
 */
function calculateStatistics(allData, signals) {
  const buyCount = signals.filter(s => s.signal === 'BUY').length;
  const sellCount = signals.filter(s => s.signal === 'SELL').length;
  
  // Find top 3 gainers and losers
  const sortedByReturn = allData.sort((a, b) => (b.daily_return || 0) - (a.daily_return || 0));
  const topGainers = sortedByReturn.slice(0, 3);
  const topLosers = sortedByReturn.slice(-3).reverse();
  
  return {
    totalRecords: allData.length,
    buyCount: buyCount,
    sellCount: sellCount,
    topGainers: topGainers,
    topLosers: topLosers,
    latestDate: allData.length > 0 ? allData[0].date : 'N/A'
  };
}


/**
 * Send summary email to stakeholders
 * 
 * @param {Object} stats - Statistics object
 */
function sendSummaryEmail(stats) {
  Logger.log('Sending summary email...');
  
  const subject = 'Stock Market ETL Summary - ' + stats.latestDate;
  
  const body = `
    <h2>Stock Market Trend Analysis - Daily ETL Summary</h2>
    <p><strong>Date:</strong> ${stats.latestDate}</p>
    <p><strong>Total Records Processed:</strong> ${stats.totalRecords}</p>
    
    <h3>Trading Signals Today</h3>
    <ul>
      <li><span style="color: green; font-weight: bold;">BUY Signals: ${stats.buyCount}</span></li>
      <li><span style="color: red; font-weight: bold;">SELL Signals: ${stats.sellCount}</span></li>
    </ul>
    
    <h3>Top 3 Gainers</h3>
    <ol>
      ${stats.topGainers.map(s => `<li>${s.symbol} (${s.sector}): ${(s.daily_return * 100).toFixed(2)}%</li>`).join('')}
    </ol>
    
    <h3>Top 3 Losers</h3>
    <ol>
      ${stats.topLosers.map(s => `<li>${s.symbol} (${s.sector}): ${(s.daily_return * 100).toFixed(2)}%</li>`).join('')}
    </ol>
    
    <hr>
    <p><em>View full data in Google Sheet: ${SpreadsheetApp.getActiveSpreadsheet().getUrl()}</em></p>
    <p><em>This is an automated email from the Stock Market ETL system.</em></p>
  `;
  
  try {
    MailApp.sendEmail({
      to: CONFIG.STAKEHOLDER_EMAIL,
      subject: subject,
      htmlBody: body
    });
    Logger.log('Summary email sent to ' + CONFIG.STAKEHOLDER_EMAIL);
  } catch (error) {
    Logger.log('Failed to send email: ' + error.toString());
  }
}


// ============================================================
// LOGGING
// ============================================================

/**
 * Log ETL run status to Logs sheet
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 * @param {string} status - Run status (SUCCESS/FAILED)
 * @param {number} recordsProcessed - Number of records processed
 * @param {number} duration - Duration in seconds
 */
function logETLRun(ss, status, recordsProcessed, duration) {
  const sheet = ss.getSheetByName(CONFIG.SHEET_NAMES.LOGS);
  
  const timestamp = new Date();
  const logEntry = [
    timestamp,
    status,
    recordsProcessed,
    duration.toFixed(2) + ' seconds'
  ];
  
  // Append to bottom
  sheet.appendRow(logEntry);
  
  Logger.log('ETL run logged: ' + status);
}


// ============================================================
// ERROR HANDLING
// ============================================================

/**
 * Handle errors with logging and email notification
 * 
 * @param {Error} error - Error object
 * @param {string} functionName - Name of function that failed
 */
function handleError(error, functionName) {
  Logger.log('ERROR in ' + functionName + ': ' + error.toString());
  Logger.log('Stack trace: ' + error.stack);
  
  // Send error notification email
  try {
    MailApp.sendEmail({
      to: CONFIG.STAKEHOLDER_EMAIL,
      subject: 'Stock Market ETL - ERROR Alert',
      body: `
        ETL Run Failed
        
        Function: ${functionName}
        Error: ${error.toString()}
        Time: ${new Date().toString()}
        
        Please check the Logs sheet in Google Sheet for details.
      `
    });
  } catch (emailError) {
    Logger.log('Failed to send error email: ' + emailError.toString());
  }
}


// ============================================================
// HELPER FUNCTIONS
// ============================================================

/**
 * Ensure all required sheets exist in spreadsheet
 * 
 * @param {Spreadsheet} ss - Google Spreadsheet object
 */
function ensureSheetsExist(ss) {
  const sheetNames = Object.values(CONFIG.SHEET_NAMES);
  
  sheetNames.forEach(name => {
    let sheet = ss.getSheetByName(name);
    if (!sheet) {
      sheet = ss.insertSheet(name);
      Logger.log('Created sheet: ' + name);
    }
  });
}
