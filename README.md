# Nancy Pelosi Trade Tracker

A Python script that automatically scrapes the U.S. House Clerk's financial disclosure site for new Periodic Transaction Reports (PTRs) filed by Nancy Pelosi, downloads PDFs, extracts trade information, and sends notifications to Discord.

## Features

- **Automated Scraping**: Monitors the House Clerk's disclosure site for new Pelosi filings
- **PDF Processing**: Downloads and parses PTR PDFs using `pdfplumber`
- **Trade Extraction**: Identifies stocks, ETFs, and options (calls/puts) with transaction details
- **Discord Integration**: Sends formatted trade alerts to a dedicated Discord channel
- **Duplicate Prevention**: Uses SQLite database to track processed filings
- **Flexible Execution**: Supports test mode, dry runs, and cron job scheduling

## Trade Types Supported

- **Stocks/ETFs**: Regular equity purchases and sales
- **Options**: Call and put options with underlying ticker extraction
- **Transaction Details**: Date, action (Buy/Sell), amount range, asset name, ticker

## Requirements

- Python 3.7+
- Internet connection for web scraping
- Discord server with webhook configured

## Installation

1. **Clone or download the project files**
   ```bash
   # If you have the files locally, just navigate to the directory
   cd "Politician Bot"
   ```

2. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   # Copy the example environment file
   cp env.example .env
   
   # Edit .env with your Discord webhook URL
   nano .env
   ```

4. **Configure Discord webhook**
   - Go to your Discord server
   - Navigate to the channel where you want notifications
   - Add "Incoming Webhooks" integration
   - Create a webhook for your `#pelosi-trades` channel
   - Copy the webhook URL to your `.env` file

## Configuration

### Environment Variables (`.env`)

```bash
# Required: Your Discord webhook URL
DISCORD_WEBHOOK_URL=https://discord.com/api/webhooks/YOUR_WEBHOOK_ID/YOUR_WEBHOOK_TOKEN

# Optional: Customize the channel name for display purposes
DISCORD_CHANNEL_NAME=#pelosi-trades
```

### Discord Webhook Setup

1. **Create a Discord Webhook**:
   - Go to your Discord server
   - Right-click on the channel where you want notifications
   - Select "Edit Channel" → "Integrations" → "Webhooks"
   - Click "Create Webhook"
   - Give it a name like "Pelosi Trade Bot"

2. **Configure the Webhook**:
   - Copy the webhook URL from the webhook settings
   - Paste it into your `.env` file as `DISCORD_WEBHOOK_URL`

3. **Test the webhook**:
   ```bash
   python pelosi_tracker.py --test-discord
   ```

## Usage

### Basic Usage

```bash
# Run the tracker (normal mode)
python pelosi_tracker.py

# Run in test mode (no Discord notifications)
python pelosi_tracker.py --test

# Dry run (no file downloads)
python pelosi_tracker.py --dry-run

# Verbose logging
python pelosi_tracker.py --verbose
```

### Command Line Options

- `--test`: Test mode - scrapes and parses but doesn't send Discord messages
- `--dry-run`: Dry run mode - doesn't download files or save to database
- `--verbose`: Enable detailed logging
- `--test-discord`: Test Discord connection only

### Cron Job Setup

For automated daily execution:

```bash
# Edit crontab
crontab -e

# Add this line to run daily at 9 AM
0 9 * * * cd /path/to/politician-bot && python pelosi_tracker.py >> pelosi_tracker.log 2>&1

# Or run every 12 hours
0 */12 * * * cd /path/to/politician-bot && python pelosi_tracker.py >> pelosi_tracker.log 2>&1
```

## How It Works

1. **Scraping**: The script visits the House Clerk's disclosure site and searches for Nancy Pelosi's filings
2. **Detection**: Identifies new PTR filings that haven't been processed before
3. **Download**: Downloads new PDF filings to a temporary location
4. **Parsing**: Extracts trade information using pattern matching and text analysis
5. **Storage**: Saves filing and trade data to a local SQLite database
6. **Notification**: Sends formatted Discord messages for each trade found
7. **Cleanup**: Removes temporary PDF files

## Database Schema

The script creates a local SQLite database (`pelosi_trades.db`) with two tables:

### `filings` table
- `filing_id`: Unique identifier for each filing
- `filing_date`: Date the filing was submitted
- `pdf_url`: URL to the original PDF
- `processed_at`: Timestamp when the filing was processed
- `trade_count`: Number of trades extracted

### `trades` table
- `filing_id`: Reference to the parent filing
- `asset_name`: Name of the stock/asset
- `ticker`: Stock ticker symbol (if available)
- `trade_type`: Type of trade (stock, option_call, option_put)
- `action`: Buy or Sell
- `amount_range`: Dollar amount range
- `transaction_date`: Date of the trade
- `filing_date`: Date the filing was submitted

## Discord Message Examples

### Stock Trade
```
📢 Nancy Pelosi Stock Trade!
Stock: Apple Inc (AAPL)
Type: Stock
Action: Buy
Amount: $15,001-$50,000
Date: 06/15/2023
PDF: View Filing
```

### Options Trade
```
📢 Nancy Pelosi Option Trade!
Stock: Amazon.com Inc (AMZN)
Type: CALL
Action: Buy
Amount: $500k–$1M
Date: 06/15/2023
PDF: View Filing
```

### Multiple Trades
```
📢 Nancy Pelosi Multiple Trades Alert!
3 new trades found in latest filing

1. Buy Stock - Apple Inc (AAPL) - $15,001-$50,000
2. Sell Option - NVIDIA Corp (NVDA) PUT - $100,001-$250,000
3. Buy Stock - Microsoft Corp (MSFT) - $1,001-$15,000

PDF: View Full Filing
```

## Troubleshooting

### Common Issues

1. **Discord webhook errors**:
   - Verify your webhook URL is correct
   - Test with `python pelosi_tracker.py --test-discord`
   - Check that the webhook is active and has proper permissions

2. **PDF parsing issues**:
   - Some PTRs may have different formats
   - Check the logs for parsing errors
   - The parser is designed to be robust but may need adjustments for edge cases

3. **Scraping failures**:
   - The House Clerk site structure may change
   - Check if the site is accessible
   - Review logs for specific error messages

### Logs

The script creates detailed logs in:
- Console output (with `--verbose` for more detail)
- `pelosi_tracker.log` file
- Database records for all processed filings

### Testing

Always test with `--test` flag first:
```bash
# Test the entire pipeline without sending Discord messages
python pelosi_tracker.py --test --verbose

# Test just the Discord connection
python pelosi_tracker.py --test-discord
```

## Customization

### Adding More Politicians

To track other politicians, modify the `scraper.py` file:
1. Update the `_is_pelosi_filing()` method
2. Add new name variations
3. Consider creating a configuration file for multiple politicians

### Adjusting Trade Parsing

The PDF parser in `pdf_parser.py` can be customized:
1. Modify regex patterns for different date formats
2. Add new asset type detection
3. Adjust amount range parsing for different formats

### Discord Message Formatting

Customize Discord messages in `discord_notifier.py`:
1. Change emojis and formatting
2. Add more trade details
3. Modify message structure

## Security Notes

- **Webhook URLs**: Keep your Discord webhook URL private
- **Local Database**: The SQLite database contains no sensitive information
- **Temporary Files**: PDFs are downloaded temporarily and deleted after processing
- **Rate Limiting**: The scraper includes reasonable delays to avoid overwhelming the House Clerk site

## Contributing

This is a focused tool for tracking specific financial disclosures. If you find issues or want to improve the parsing logic:

1. Test thoroughly with real PTR documents
2. Update the regex patterns as needed
3. Consider edge cases in the House Clerk's document format
4. Maintain backward compatibility for existing databases

## License

This project is provided as-is for educational and research purposes. Please respect the House Clerk's website terms of service and use responsibly.

## Support

For issues or questions:
1. Check the logs for error messages
2. Verify your Discord webhook configuration
3. Test with the `--test` flag to isolate issues
4. Review the database to see what data was processed

---

**Note**: This tool is designed to track publicly available financial disclosure information. Always comply with applicable laws and website terms of service when scraping public data.
