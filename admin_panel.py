#!/usr/bin/env python3
"""
Admin Panel for iHub Bot Knowledge Base Management

This script provides a command-line interface for managing the knowledge base
of tools, locations, and resources for the school chatbot.
"""

import json
import os
import sys
from datetime import datetime

class KnowledgeBaseAdmin:
    def __init__(self, kb_file='knowledge_base.json'):
        self.kb_file = kb_file
        self.data = self.load_data()
    
    def load_data(self):
        """Load knowledge base data from file"""
        if os.path.exists(self.kb_file):
            with open(self.kb_file, 'r') as f:
                return json.load(f)
        else:
            return {"tools": []}
    
    def save_data(self):
        """Save knowledge base data to file"""
        with open(self.kb_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        # Remove embeddings to force regeneration
        if os.path.exists('embeddings.pkl'):
            os.remove('embeddings.pkl')
        if os.path.exists('faiss_index.idx'):
            os.remove('faiss_index.idx')
        
        print(f"✅ Knowledge base saved to {self.kb_file}")
        print("📝 Embeddings will be regenerated on next app startup")
    
    def list_tools(self):
        """List all tools in the knowledge base"""
        if not self.data['tools']:
            print("No tools found in the knowledge base.")
            return
        
        print(f"\n📋 Found {len(self.data['tools'])} tools:")
        print("-" * 60)
        for i, tool in enumerate(self.data['tools'], 1):
            print(f"{i:2d}. {tool['name']} ({tool['category']})")
            print(f"    📍 {tool['location']}")
            print(f"    ⏰ {tool['availability']}")
            if tool['training_required']:
                print(f"    ⚠️  Training required - {tool['contact']}")
            print()
    
    def add_tool(self):
        """Add a new tool to the knowledge base"""
        print("\n➕ Adding a new tool")
        print("=" * 40)
        
        # Get next ID
        max_id = max([tool['id'] for tool in self.data['tools']], default=0)
        new_id = max_id + 1
        
        # Collect tool information
        tool = {
            "id": new_id,
            "name": input("Tool/Resource name: ").strip(),
            "category": input("Category (e.g., Fabrication, Computing, Study Space): ").strip(),
            "location": input("Location (building/room): ").strip(),
            "description": input("Description: ").strip(),
            "availability": input("Availability (hours/schedule): ").strip(),
            "training_required": input("Training required? (y/n): ").lower().startswith('y'),
            "contact": input("Contact (person/extension): ").strip(),
            "keywords": []
        }
        
        # Get keywords
        print("\nEnter keywords (comma-separated, for better search):")
        keywords_input = input("Keywords: ").strip()
        if keywords_input:
            tool["keywords"] = [kw.strip().lower() for kw in keywords_input.split(',')]
        
        # Add to data
        self.data['tools'].append(tool)
        
        print(f"\n✅ Added tool: {tool['name']}")
        return tool
    
    def edit_tool(self):
        """Edit an existing tool"""
        if not self.data['tools']:
            print("No tools to edit.")
            return
        
        self.list_tools()
        
        try:
            index = int(input("\nEnter tool number to edit: ")) - 1
            if index < 0 or index >= len(self.data['tools']):
                print("Invalid tool number.")
                return
        except ValueError:
            print("Please enter a valid number.")
            return
        
        tool = self.data['tools'][index]
        print(f"\n✏️  Editing: {tool['name']}")
        print("=" * 40)
        print("Press Enter to keep current value")
        
        # Edit each field
        new_name = input(f"Name ({tool['name']}): ").strip()
        if new_name:
            tool['name'] = new_name
        
        new_category = input(f"Category ({tool['category']}): ").strip()
        if new_category:
            tool['category'] = new_category
        
        new_location = input(f"Location ({tool['location']}): ").strip()
        if new_location:
            tool['location'] = new_location
        
        new_description = input(f"Description ({tool['description']}): ").strip()
        if new_description:
            tool['description'] = new_description
        
        new_availability = input(f"Availability ({tool['availability']}): ").strip()
        if new_availability:
            tool['availability'] = new_availability
        
        training_input = input(f"Training required ({tool['training_required']}) (y/n): ").strip()
        if training_input:
            tool['training_required'] = training_input.lower().startswith('y')
        
        new_contact = input(f"Contact ({tool['contact']}): ").strip()
        if new_contact:
            tool['contact'] = new_contact
        
        keywords_input = input(f"Keywords ({', '.join(tool['keywords'])}): ").strip()
        if keywords_input:
            tool['keywords'] = [kw.strip().lower() for kw in keywords_input.split(',')]
        
        print(f"✅ Updated tool: {tool['name']}")
    
    def delete_tool(self):
        """Delete a tool from the knowledge base"""
        if not self.data['tools']:
            print("No tools to delete.")
            return
        
        self.list_tools()
        
        try:
            index = int(input("\nEnter tool number to delete: ")) - 1
            if index < 0 or index >= len(self.data['tools']):
                print("Invalid tool number.")
                return
        except ValueError:
            print("Please enter a valid number.")
            return
        
        tool = self.data['tools'][index]
        confirm = input(f"Are you sure you want to delete '{tool['name']}'? (y/n): ")
        if confirm.lower().startswith('y'):
            deleted_tool = self.data['tools'].pop(index)
            print(f"❌ Deleted tool: {deleted_tool['name']}")
        else:
            print("Deletion cancelled.")
    
    def search_tools(self):
        """Search for tools by keyword"""
        if not self.data['tools']:
            print("No tools to search.")
            return
        
        query = input("\nEnter search term: ").strip().lower()
        if not query:
            return
        
        matches = []
        for tool in self.data['tools']:
            # Search in name, description, category, keywords
            search_text = f"{tool['name']} {tool['description']} {tool['category']} {' '.join(tool['keywords'])}".lower()
            if query in search_text:
                matches.append(tool)
        
        if matches:
            print(f"\n🔍 Found {len(matches)} matches for '{query}':")
            print("-" * 60)
            for i, tool in enumerate(matches, 1):
                print(f"{i}. {tool['name']} ({tool['category']})")
                print(f"   📍 {tool['location']}")
                print()
        else:
            print(f"No matches found for '{query}'")
    
    def export_backup(self):
        """Export a backup of the knowledge base"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = f"knowledge_base_backup_{timestamp}.json"
        
        with open(backup_file, 'w') as f:
            json.dump(self.data, f, indent=2)
        
        print(f"💾 Backup saved to {backup_file}")
    
    def import_from_file(self):
        """Import knowledge base from a file"""
        filename = input("Enter filename to import from: ").strip()
        
        if not os.path.exists(filename):
            print(f"File '{filename}' not found.")
            return
        
        try:
            with open(filename, 'r') as f:
                imported_data = json.load(f)
            
            if 'tools' not in imported_data:
                print("Invalid file format. Expected 'tools' key.")
                return
            
            # Ask for merge or replace
            action = input("Merge with existing data (m) or replace all (r)? ").lower()
            
            if action == 'r':
                self.data = imported_data
                print(f"✅ Replaced knowledge base with data from {filename}")
            elif action == 'm':
                # Merge tools, avoiding duplicates by ID
                existing_ids = {tool['id'] for tool in self.data['tools']}
                new_tools = [tool for tool in imported_data['tools'] if tool['id'] not in existing_ids]
                self.data['tools'].extend(new_tools)
                print(f"✅ Merged {len(new_tools)} new tools from {filename}")
            else:
                print("Import cancelled.")
                return
                
        except json.JSONDecodeError:
            print("Error: Invalid JSON file.")
        except Exception as e:
            print(f"Error importing file: {e}")
    
    def show_statistics(self):
        """Show knowledge base statistics"""
        tools = self.data['tools']
        if not tools:
            print("No tools in the knowledge base.")
            return
        
        categories = {}
        training_required = 0
        
        for tool in tools:
            category = tool['category']
            categories[category] = categories.get(category, 0) + 1
            if tool['training_required']:
                training_required += 1
        
        print(f"\n📊 Knowledge Base Statistics")
        print("=" * 40)
        print(f"Total tools: {len(tools)}")
        print(f"Tools requiring training: {training_required}")
        print(f"Tools not requiring training: {len(tools) - training_required}")
        print("\nTools by category:")
        for category, count in sorted(categories.items()):
            print(f"  {category}: {count}")
    
    def run(self):
        """Main admin interface loop"""
        print("🤖 iHub Bot - Knowledge Base Admin Panel")
        print("=" * 50)
        
        while True:
            print("\nChoose an option:")
            print("1. List all tools")
            print("2. Add new tool")
            print("3. Edit tool")
            print("4. Delete tool")
            print("5. Search tools")
            print("6. Show statistics")
            print("7. Export backup")
            print("8. Import from file")
            print("9. Save and exit")
            print("0. Exit without saving")
            
            choice = input("\nEnter your choice (0-9): ").strip()
            
            if choice == '1':
                self.list_tools()
            elif choice == '2':
                self.add_tool()
            elif choice == '3':
                self.edit_tool()
            elif choice == '4':
                self.delete_tool()
            elif choice == '5':
                self.search_tools()
            elif choice == '6':
                self.show_statistics()
            elif choice == '7':
                self.export_backup()
            elif choice == '8':
                self.import_from_file()
            elif choice == '9':
                self.save_data()
                print("👋 Goodbye!")
                break
            elif choice == '0':
                print("👋 Exiting without saving!")
                break
            else:
                print("Invalid choice. Please try again.")

def main():
    """Main entry point"""
    admin = KnowledgeBaseAdmin()
    admin.run()

if __name__ == "__main__":
    main()