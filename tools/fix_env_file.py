import os

def fix_env():
    env_path = '.env'
    if not os.path.exists(env_path):
        print(".env file not found")
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.splitlines()
    new_lines = []
    
    # We'll do a simple pass to clean up specific known configuration lines
    # and try to fix the messy API key lines by ensuring ANTHROPIC_API_KEY is on its own line
    
    for line in lines:
        line = line.strip()
        if not line:
            new_lines.append("")
            continue
            
        # Fix known backend configs
        if line.startswith("DATA_PRODUCT_BACKEND="):
            new_lines.append("DATA_PRODUCT_BACKEND=supabase")
        elif line.startswith("BUSINESS_PROCESS_BACKEND="):
            new_lines.append("BUSINESS_PROCESS_BACKEND=supabase")
        elif line.startswith("KPI_REGISTRY_BACKEND="):
            new_lines.append("KPI_REGISTRY_BACKEND=supabase")
        elif line.startswith("PRINCIPAL_PROFILE_BACKEND="):
            new_lines.append("PRINCIPAL_PROFILE_BACKEND=supabase")
        elif line.startswith("BUSINESS_GLOSSARY_BACKEND="):
            new_lines.append("BUSINESS_GLOSSARY_BACKEND=supabase")
        
        # Attempt to fix the messy API key line if detected
        elif "ANTHROPIC_API_KEY=" in line and not line.startswith("ANTHROPIC_API_KEY="):
            # Split this line
            parts = line.split("ANTHROPIC_API_KEY=")
            if len(parts) == 2:
                # The part before might be garbage or continuation, let's keep it just in case
                if parts[0].strip():
                    new_lines.append(parts[0].strip())
                new_lines.append(f"ANTHROPIC_API_KEY={parts[1].strip()}")
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Write back
    with open(env_path, 'w', encoding='utf-8') as f:
        f.write("\n".join(new_lines))
    
    print("Fixed .env file")

if __name__ == "__main__":
    fix_env()
