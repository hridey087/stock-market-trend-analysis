/**
 * Google Apps Script - Custom Menu for Stock Market ETL
 * 
 * Adds a custom menu to Google Sheets for manual ETL triggering
 * and utility functions.
 * 
 * This file should be combined with etl_automation.js in the 
 * Apps Script editor.
 */

// ============================================================
// ON OPEN - Create Custom Menu
// ============================================================

/**
 * Creates custom menu when spreadsheet opens
 */
function onOpen() {
  const ui = SpreadsheetApp.getUi();
  
  ui.createMenu('Stock Analysis ETL')
    .addItem('▶ Run Full ETL', 'runDailyETL')
    .addItem('⟳ Refresh Raw Data', 'refreshRawData')
    .addItem('⟳ Update Signals Only', 'refreshSignals')
    .addItem('⟳ Update Sector Summary', 'refreshSectorSummary')
    .addSeparator()
    .addItem('📊 View Logs', 'showLogs')
    .addItem('📧 Send Test Email', 'sendTestEmail')
    .addItem('🔧 Apply Formatting', 'applyFormattingOnly')
    .addSeparator()
    .addItem('ℹ About', 'showAbout')
    .addToUi();
  
  Logger.log('Custom menu added to spreadsheet');
}


// ============================================================
// MENU ACTION FUNCTIONS
// ============================================================

/**
 * Refresh only raw data from API
 */
function refreshRawData() {
  Logger.log('Manual trigger: Refresh Raw Data');
  
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    const latestData = fetchDataFromAPI('/api/latest');
    
    if (latestData && latestData.data) {
      writeToRawDataSheet(ss, latestData.data);
      SpreadsheetApp.getUi().alert('Raw data refreshed successfully: ' + latestData.data.length + ' records');
    } else {
      SpreadsheetApp.getUi().alert('No data received from API');
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
    handleError(error, 'refreshRawData');
  }
}


/**
 * Refresh only trading signals
 */
function refreshSignals() {
  Logger.log('Manual trigger: Refresh Signals');
  
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    const signalsData = fetchDataFromAPI('/api/signals?signal=BUY,SELL');
    
    if (signalsData && signalsData.data) {
      writeToSignalsSheet(ss, signalsData.data);
      applyConditionalFormatting(ss);
      SpreadsheetApp.getUi().alert('Signals refreshed: ' + signalsData.data.length + ' signals');
    } else {
      SpreadsheetApp.getUi().alert('No signals received from API');
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
    handleError(error, 'refreshSignals');
  }
}


/**
 * Refresh only sector summary
 */
function refreshSectorSummary() {
  Logger.log('Manual trigger: Refresh Sector Summary');
  
  try {
    const ss = SpreadsheetApp.openById(CONFIG.SHEET_ID);
    const sectorData = fetchDataFromAPI('/api/sector-summary');
    
    if (sectorData && sectorData.data) {
      writeToSectorSummarySheet(ss, sectorData.data);
      SpreadsheetApp.getUi().alert('Sector summary refreshed: ' + sectorData.data.length + ' sectors');
    } else {
      SpreadsheetApp.getUi().alert('No sector data received from API');
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
    handleError(error, 'refreshSectorSummary');
  }
}


/**
 * Show Logs sheet
 */
function showLogs() {
  Logger.log('Manual trigger: Show Logs');
  
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    const logsSheet = ss.getSheetByName(CONFIG.SHEET_NAMES.LOGS);
    
    if (logsSheet) {
      ss.setActiveSheet(logsSheet);
      SpreadsheetApp.getUi().alert('Navigate to Logs sheet to view ETL history');
    } else {
      SpreadsheetApp.getUi().alert('Logs sheet not found');
    }
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
  }
}


/**
 * Send test email to verify email configuration
 */
function sendTestEmail() {
  Logger.log('Manual trigger: Send Test Email');
  
  try {
    const subject = 'Stock Market ETL - Test Email';
    const body = `
      <h2>Test Email - Stock Market ETL System</h2>
      <p>This is a test email to verify email configuration.</p>
      <p><strong>Time:</strong> ${new Date().toString()}</p>
      <p><strong>Sheet:</strong> ${SpreadsheetApp.getActiveSpreadsheet().getName()}</p>
      <hr>
      <p><em>If you received this email, the email configuration is working correctly.</em></p>
    `;
    
    MailApp.sendEmail({
      to: CONFIG.STAKEHOLDER_EMAIL,
      subject: subject,
      htmlBody: body
    });
    
    SpreadsheetApp.getUi().alert('Test email sent successfully to ' + CONFIG.STAKEHOLDER_EMAIL);
  } catch (error) {
    SpreadsheetApp.getUi().alert('Failed to send test email: ' + error.toString());
  }
}


/**
 * Apply conditional formatting only (without refreshing data)
 */
function applyFormattingOnly() {
  Logger.log('Manual trigger: Apply Formatting');
  
  try {
    const ss = SpreadsheetApp.getActiveSpreadsheet();
    applyConditionalFormatting(ss);
    SpreadsheetApp.getUi().alert('Conditional formatting applied successfully');
  } catch (error) {
    SpreadsheetApp.getUi().alert('Error: ' + error.toString());
  }
}


/**
 * Show About dialog with system information
 */
function showAbout() {
  const aboutText = `
Stock Market Trend Analysis - ETL System
Version: 1.0.0

This system automatically:
• Fetches latest stock data from Flask API
• Updates Google Sheets with OHLCV data
• Tracks BUY/SELL trading signals
• Aggregates sector-level summaries
• Sends daily email summaries

Data Source: NSE/BSE (via yfinance)
Update Frequency: Daily at 8:00 AM IST
Stocks Tracked: 50 Nifty 50 constituents

For support: team@company.com
  `;
  
  SpreadsheetApp.getUi().alert(aboutText);
}


// ============================================================
// INSTALLABLE TRIGGER SETUP
// ============================================================

/**
 * Create time-based trigger for daily ETL
 * Run this function once to set up the trigger
 */
function createDailyTrigger() {
  // Delete existing triggers
  const triggers = ScriptApp.getProjectTriggers();
  triggers.forEach(trigger => {
    ScriptApp.deleteTrigger(trigger);
  });
  
  // Create new daily trigger at 8 AM IST
  ScriptApp.newTrigger('runDailyETL')
    .timeBased()
    .atHour(8)
    .everyDays(1)
    .inTimezone('Asia/Kolkata')
    .create();
  
  Logger.log('Daily trigger created: 8:00 AM IST');
  SpreadsheetApp.getUi().alert('Daily ETL trigger set up: Runs every day at 8:00 AM IST');
}


/**
 * Create trigger for menu creation (on spreadsheet open)
 * This is automatically created, but included for documentation
 */
function createOnOpenTrigger() {
  // onOpen() is a simple trigger, doesn't need installation
  // Just included here for reference
  Logger.log('onOpen trigger is automatic - no setup needed');
}
