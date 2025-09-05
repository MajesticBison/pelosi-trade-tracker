# Adding More Politicians to the Trade Tracker

This guide explains how to add new politicians to the multi-politician trade tracking system.

## Quick Start

### 1. Set Up Example Politicians
```bash
# Add example politicians (McCarthy, Jeffries, Scott)
python manage_politicians.py setup-examples

# List all politicians
python manage_politicians.py list

# Activate a politician
python manage_politicians.py activate mccarthy
```

### 2. Add a Custom Politician
```bash
# Add a new politician
python manage_politicians.py add \
  --name "warren" \
  --full_name "Elizabeth Warren" \
  --search_name "Warren, Elizabeth" \
  --party "Democratic" \
  --state "MA" \
  --chamber "Senate" \
  --webhook "https://discord.com/api/webhooks/YOUR_WEBHOOK_URL" \
  --channel "#warren-trades" \
  --status "active"
```

### 3. Configure Discord Webhooks
Each politician needs their own Discord webhook URL. Create separate webhooks for each politician's channel.

## Detailed Setup

### Step 1: Create Discord Channels and Webhooks

1. **Create Discord Channels**:
   - `#pelosi-trades`
   - `#mccarthy-trades` 
   - `#jeffries-trades`
   - `#warren-trades`
   - etc.

2. **Create Webhooks**:
   - Go to each channel → Settings → Integrations → Webhooks
   - Create a new webhook for each channel
   - Copy the webhook URL

### Step 2: Add Politicians

#### Using the CLI Tool (Recommended)
```bash
# Add Kevin McCarthy
python manage_politicians.py add \
  --name "mccarthy" \
  --full_name "Kevin McCarthy" \
  --search_name "McCarthy, Kevin" \
  --party "Republican" \
  --state "CA" \
  --chamber "House" \
  --webhook "https://discord.com/api/webhooks/YOUR_MCCARTHY_WEBHOOK" \
  --channel "#mccarthy-trades" \
  --status "active"

# Add Hakeem Jeffries
python manage_politicians.py add \
  --name "jeffries" \
  --full_name "Hakeem Jeffries" \
  --search_name "Jeffries, Hakeem" \
  --party "Democratic" \
  --state "NY" \
  --chamber "House" \
  --webhook "https://discord.com/api/webhooks/YOUR_JEFFRIES_WEBHOOK" \
  --channel "#jeffries-trades" \
  --status "active"
```

#### Manual Configuration
Edit `politicians.json` directly:
```json
{
  "pelosi": {
    "name": "pelosi",
    "full_name": "Nancy Pelosi",
    "search_name": "Pelosi, Nancy",
    "discord_webhook": "https://discord.com/api/webhooks/YOUR_PELOSI_WEBHOOK",
    "channel_name": "#pelosi-trades",
    "status": "active",
    "description": "Speaker Emerita, California",
    "party": "Democratic",
    "state": "CA",
    "chamber": "House"
  },
  "mccarthy": {
    "name": "mccarthy",
    "full_name": "Kevin McCarthy", 
    "search_name": "McCarthy, Kevin",
    "discord_webhook": "https://discord.com/api/webhooks/YOUR_MCCARTHY_WEBHOOK",
    "channel_name": "#mccarthy-trades",
    "status": "active",
    "description": "Former Speaker, California",
    "party": "Republican",
    "state": "CA",
    "chamber": "House"
  }
}
```

### Step 3: Test the Setup

```bash
# Test Discord connections
python multi_politician_tracker.py --test-discord

# Test specific politician
python multi_politician_tracker.py --test-discord mccarthy

# Dry run to see what would be processed
python multi_politician_tracker.py --dry-run

# Show statistics
python multi_politician_tracker.py --stats
```

### Step 4: Set Up Automation

#### macOS (Cron)
```bash
# Edit crontab
crontab -e

# Add daily run at 9 AM
0 9 * * * cd "/path/to/politician-bot" && python multi_politician_tracker.py >> multi_politician_tracker.log 2>&1
```

#### Windows (Task Scheduler)
```powershell
# Run as Administrator
PowerShell -ExecutionPolicy Bypass -File setup_windows_task.ps1
```

## Popular Politicians to Track

### House Leadership
- **Nancy Pelosi** (D-CA) - Speaker Emerita
- **Kevin McCarthy** (R-CA) - Former Speaker  
- **Hakeem Jeffries** (D-NY) - Minority Leader
- **Steve Scalise** (R-LA) - Majority Leader
- **Katherine Clark** (D-MA) - Minority Whip

### Senate Leadership
- **Chuck Schumer** (D-NY) - Majority Leader
- **Mitch McConnell** (R-KY) - Minority Leader
- **Dick Durbin** (D-IL) - Majority Whip
- **John Thune** (R-SD) - Minority Whip

### Committee Chairs
- **Maxine Waters** (D-CA) - Financial Services
- **Patrick McHenry** (R-NC) - Financial Services
- **Ron Wyden** (D-OR) - Finance Committee
- **Mike Crapo** (R-ID) - Banking Committee

### High-Profile Members
- **Elizabeth Warren** (D-MA) - Consumer Protection
- **Ted Cruz** (R-TX) - Judiciary Committee
- **Marco Rubio** (R-FL) - Intelligence Committee
- **Kirsten Gillibrand** (D-NY) - Armed Services

## Management Commands

### List Politicians
```bash
# List all politicians
python manage_politicians.py list

# List only active politicians
python manage_politicians.py list --active-only
```

### Show Details
```bash
# Show politician details
python manage_politicians.py show mccarthy
```

### Update Configuration
```bash
# Update Discord webhook
python manage_politicians.py update mccarthy --webhook "NEW_WEBHOOK_URL"

# Change status
python manage_politicians.py update mccarthy --status "inactive"

# Update channel name
python manage_politicians.py update mccarthy --channel "#new-channel"
```

### Activate/Deactivate
```bash
# Activate politician
python manage_politicians.py activate mccarthy

# Deactivate politician
python manage_politician.py deactivate mccarthy
```

### Remove Politician
```bash
# Remove politician and all their data
python manage_politicians.py remove mccarthy
```

## Database Management

### View Statistics
```bash
python multi_politician_tracker.py --stats
```

### Clear Politician Data
```python
from multi_politician_database import MultiPoliticianTradesDB

db = MultiPoliticianTradesDB()
db.clear_politician_data("mccarthy")  # Remove all McCarthy data
```

## Troubleshooting

### Common Issues

1. **"Politician not found"**
   - Check spelling of politician name
   - Use `python manage_politicians.py list` to see available names

2. **"No Discord webhook configured"**
   - Add webhook URL: `python manage_politicians.py update <name> --webhook <url>`

3. **"No filings found"**
   - Check search name format (should be "Last, First")
   - Verify politician files financial disclosures
   - Check if politician is in House vs Senate

4. **"Discord notification failed"**
   - Test webhook: `python multi_politician_tracker.py --test-discord <name>`
   - Check webhook URL is correct
   - Verify Discord channel exists

### Search Name Format
The search name must match exactly how it appears in the House Clerk database:
- **Correct**: "Pelosi, Nancy", "McCarthy, Kevin", "Warren, Elizabeth"
- **Incorrect**: "Nancy Pelosi", "Kevin McCarthy", "Elizabeth Warren"

### Testing
```bash
# Test everything
python multi_politician_tracker.py --dry-run --verbose

# Test specific politician
python multi_politician_tracker.py --test-discord pelosi

# Check database
python multi_politician_tracker.py --stats
```

## Best Practices

1. **Start Small**: Add 2-3 politicians first, test thoroughly
2. **Separate Channels**: Use different Discord channels for each politician
3. **Monitor Logs**: Check logs regularly for errors
4. **Backup Database**: Keep backups of `politician_trades.db`
5. **Rate Limiting**: The system respects Discord rate limits automatically
6. **Regular Updates**: Update politician configurations as needed

## Migration from Single Politician

If you're migrating from the single-politician system:

1. **Backup Data**: Copy `pelosi_trades.db` to `politician_trades.db`
2. **Update Cron/Task Scheduler**: Change to use `multi_politician_tracker.py`
3. **Test**: Run `python multi_politician_tracker.py --dry-run`
4. **Verify**: Check that Pelosi data is still accessible

The new system is backward compatible with the old Pelosi-only system.
