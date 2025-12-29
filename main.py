from brain import SecondBrain
from llm import extract_remember_content

HELP_TEXT = """
Second Brain Commands:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  /help          - Show this help message
  /index         - Re-index the document (run after external edits)
  /stats         - Show document completion statistics
  /gaps          - Analyze what's missing in the document
  /gaps D1       - Analyze gaps in specific domain (D1-D6)
  /markers       - List all valid section markers
  /quit          - Exit the program

For normal use, just type naturally:
  - Ask questions about your research
  - To add content, say things like:
      "remember [note]"
      "add this: [note]"
      "save [note]"
      "note that [note]"
      "don't forget [note]"
      "make a note of [note]"
  - To specify a section: "add [note] in [D2:DEFINITION]"

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""

def main():
    print("=" * 60)
    print("  SECOND BRAIN - ELSA Research Assistant")
    print("=" * 60)
    print("\nInitializing...")
    
    brain = SecondBrain()
    
    print("\nIndexing document...")
    stats = brain.index_document()
    print(f"Ready! {stats['complete_sections']}/{stats['total_sections']} sections have content.")
    print("\nType /help for commands, or just ask a question.\n")
    
    pending_remember = None  # Stores pending remember action awaiting confirmation
    
    while True:
        try:
            user_input = input("You: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nGoodbye!")
            break
        
        if not user_input:
            continue
        
        # Handle pending confirmation
        if pending_remember:
            lower_input = user_input.lower()
            
            if lower_input == "yes":
                result = brain.confirm_remember(
                    pending_remember["content"],
                    pending_remember["marker"]
                )
                print(f"\nBrain: {result['message']}\n")
                pending_remember = None
                continue
            
            elif lower_input == "no":
                print("\nBrain: Cancelled.\n")
                pending_remember = None
                continue
            
            elif user_input.startswith("[") and user_input.endswith("]"):
                # User specified a different marker
                result = brain.confirm_remember(
                    pending_remember["content"],
                    user_input
                )
                print(f"\nBrain: {result['message']}\n")
                pending_remember = None
                continue
            
            else:
                print("\nBrain: Please type 'yes', 'no', or a specific marker like [D2:DEFINITION]\n")
                continue
        
        # Commands
        if user_input.startswith("/"):
            cmd = user_input.lower().split()
            
            if cmd[0] == "/help":
                print(HELP_TEXT)
            
            elif cmd[0] == "/quit":
                print("Goodbye!")
                break
            
            elif cmd[0] == "/index":
                print("\nRe-indexing document...")
                stats = brain.index_document()
                print(f"Done! {stats['complete_sections']}/{stats['total_sections']} sections indexed.\n")
            
            elif cmd[0] == "/stats":
                stats = brain.get_stats()
                print(f"\nDocument Statistics:")
                print(f"  Total sections: {stats['total_sections']}")
                print(f"  Complete: {stats['complete_sections']}")
                print(f"  Empty: {stats['empty_sections']}")
                print(f"\nBy domain:")
                for d, s in stats['domains'].items():
                    print(f"  {d}: {s['complete']}/{s['total']} complete")
                print()
            
            elif cmd[0] == "/gaps":
                domain = cmd[1].upper() if len(cmd) > 1 else None
                if domain and domain not in ["D1", "D2", "D3", "D4", "D5", "D6"]:
                    print(f"\nInvalid domain: {domain}. Use D1-D6.\n")
                else:
                    print("\nAnalyzing gaps...")
                    analysis = brain.gaps(domain)
                    print(f"\n{analysis}\n")
            
            elif cmd[0] == "/markers":
                print(brain.list_markers())
            
            else:
                print(f"\nUnknown command: {cmd[0]}. Type /help for commands.\n")
            
            continue
        
        # Remember command (natural language)
        remember_content = extract_remember_content(user_input)
        if remember_content:
            content = remember_content
            
            # Check if user specified a marker
            if " in [" in content and content.endswith("]"):
                # Parse explicit marker: "X in [D1:DEFINITION]"
                parts = content.rsplit(" in ", 1)
                note_content = parts[0]
                marker = parts[1]
                
                print(f"\nBrain: Adding to {marker}...")
                result = brain.confirm_remember(note_content, marker)
                print(f"{result['message']}\n")
            else:
                # Auto-classify
                result = brain.remember(content, confirm=True)
                
                if result["status"] == "pending_confirmation":
                    print(f"\nBrain: {result['message']}")
                    pending_remember = {
                        "content": result["content"],
                        "marker": result["classification"]["marker"]
                    }
                else:
                    print(f"\nBrain: {result['message']}\n")
            
            continue
        
        # Regular query
        response = brain.query(user_input)
        print(f"\nBrain: {response}\n")


if __name__ == "__main__":
    main()
