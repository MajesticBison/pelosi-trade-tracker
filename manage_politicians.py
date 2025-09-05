#!/usr/bin/env python3
"""
Command-line tool for managing politician configurations.
"""

import argparse
import sys
from politicians_config import PoliticiansManager, PoliticianConfig, PoliticianStatus, EXAMPLE_POLITICIANS

def list_politicians(manager: PoliticiansManager, active_only: bool = False):
    """List all politicians."""
    politicians = manager.get_active_politicians() if active_only else manager.politicians.values()
    
    if not politicians:
        print("No politicians configured.")
        return
    
    print(f"{'Name':<15} {'Full Name':<25} {'Status':<10} {'Party':<12} {'State':<5} {'Chamber':<8}")
    print("-" * 80)
    
    for config in sorted(politicians, key=lambda x: x.name):
        print(f"{config.name:<15} {config.full_name:<25} {config.status.value:<10} "
              f"{config.party:<12} {config.state:<5} {config.chamber:<8}")

def add_politician(manager: PoliticiansManager, args):
    """Add a new politician."""
    try:
        config = PoliticianConfig(
            name=args.name,
            full_name=args.full_name,
            search_name=args.search_name,
            discord_webhook=args.webhook or "",
            channel_name=args.channel,
            status=PoliticianStatus(args.status),
            description=args.description or "",
            party=args.party or "",
            state=args.state or "",
            chamber=args.chamber or "House"
        )
        
        manager.add_politician(config)
        print(f"✅ Added politician: {config.full_name}")
        
    except Exception as e:
        print(f"❌ Error adding politician: {e}")

def remove_politician(manager: PoliticiansManager, name: str):
    """Remove a politician."""
    if manager.remove_politician(name):
        print(f"✅ Removed politician: {name}")
    else:
        print(f"❌ Politician not found: {name}")

def update_politician(manager: PoliticiansManager, name: str, args):
    """Update a politician configuration."""
    updates = {}
    
    if args.status:
        updates['status'] = args.status
    if args.webhook:
        updates['discord_webhook'] = args.webhook
    if args.channel:
        updates['channel_name'] = args.channel
    if args.description:
        updates['description'] = args.description
    
    if manager.update_politician(name, **updates):
        print(f"✅ Updated politician: {name}")
    else:
        print(f"❌ Politician not found: {name}")

def show_politician(manager: PoliticiansManager, name: str):
    """Show detailed information about a politician."""
    config = manager.get_politician(name)
    if not config:
        print(f"❌ Politician not found: {name}")
        return
    
    print(f"📋 Politician Details: {config.full_name}")
    print("=" * 50)
    print(f"Name: {config.name}")
    print(f"Full Name: {config.full_name}")
    print(f"Search Name: {config.search_name}")
    print(f"Status: {config.status.value}")
    print(f"Party: {config.party}")
    print(f"State: {config.state}")
    print(f"Chamber: {config.chamber}")
    print(f"Channel: {config.channel_name}")
    print(f"Webhook: {'✅ Configured' if config.discord_webhook else '❌ Not configured'}")
    print(f"Description: {config.description}")

def setup_examples(manager: PoliticiansManager):
    """Set up example politicians."""
    print("Setting up example politicians...")
    
    for name, config in EXAMPLE_POLITICIANS.items():
        if name not in manager.politicians:
            manager.add_politician(config)
            print(f"✅ Added example: {config.full_name}")
        else:
            print(f"ℹ️  Already exists: {config.full_name}")
    
    print(f"\n📋 Use 'python manage_politicians.py list' to see all politicians")
    print(f"📋 Use 'python manage_politicians.py activate <name>' to activate a politician")

def activate_politician(manager: PoliticiansManager, name: str):
    """Activate a politician."""
    if manager.update_politician(name, status=PoliticianStatus.ACTIVE):
        print(f"✅ Activated politician: {name}")
    else:
        print(f"❌ Politician not found: {name}")

def deactivate_politician(manager: PoliticiansManager, name: str):
    """Deactivate a politician."""
    if manager.update_politician(name, status=PoliticianStatus.INACTIVE):
        print(f"✅ Deactivated politician: {name}")
    else:
        print(f"❌ Politician not found: {name}")

def main():
    parser = argparse.ArgumentParser(description="Manage politician configurations")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List politicians')
    list_parser.add_argument('--active-only', action='store_true', 
                           help='Show only active politicians')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new politician')
    add_parser.add_argument('name', help='Politician name (e.g., "pelosi")')
    add_parser.add_argument('full_name', help='Full name (e.g., "Nancy Pelosi")')
    add_parser.add_argument('search_name', help='Search name (e.g., "Pelosi, Nancy")')
    add_parser.add_argument('--webhook', help='Discord webhook URL')
    add_parser.add_argument('--channel', default='#trades', help='Discord channel name')
    add_parser.add_argument('--status', default='inactive', choices=['active', 'inactive', 'testing'],
                          help='Initial status')
    add_parser.add_argument('--description', help='Description')
    add_parser.add_argument('--party', help='Political party')
    add_parser.add_argument('--state', help='State abbreviation')
    add_parser.add_argument('--chamber', default='House', choices=['House', 'Senate'],
                          help='Chamber')
    
    # Remove command
    remove_parser = subparsers.add_parser('remove', help='Remove a politician')
    remove_parser.add_argument('name', help='Politician name to remove')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update a politician')
    update_parser.add_argument('name', help='Politician name to update')
    update_parser.add_argument('--status', choices=['active', 'inactive', 'testing'],
                             help='Update status')
    update_parser.add_argument('--webhook', help='Update Discord webhook')
    update_parser.add_argument('--channel', help='Update Discord channel')
    update_parser.add_argument('--description', help='Update description')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show politician details')
    show_parser.add_argument('name', help='Politician name to show')
    
    # Setup examples command
    subparsers.add_parser('setup-examples', help='Set up example politicians')
    
    # Activate/Deactivate commands
    activate_parser = subparsers.add_parser('activate', help='Activate a politician')
    activate_parser.add_argument('name', help='Politician name to activate')
    
    deactivate_parser = subparsers.add_parser('deactivate', help='Deactivate a politician')
    deactivate_parser.add_argument('name', help='Politician name to deactivate')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    manager = PoliticiansManager()
    
    if args.command == 'list':
        list_politicians(manager, args.active_only)
    elif args.command == 'add':
        add_politician(manager, args)
    elif args.command == 'remove':
        remove_politician(manager, args.name)
    elif args.command == 'update':
        update_politician(manager, args.name, args)
    elif args.command == 'show':
        show_politician(manager, args.name)
    elif args.command == 'setup-examples':
        setup_examples(manager)
    elif args.command == 'activate':
        activate_politician(manager, args.name)
    elif args.command == 'deactivate':
        deactivate_politician(manager, args.name)

if __name__ == "__main__":
    main()
