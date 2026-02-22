import os
import yaml

def load_prompt(filename):
    """Load a prompt from a YAML file."""
    script_dir = os.getcwd()
    # print(f"LIST DIR: {os.listdir()}")
    # prompt_path = os.path.join(f"/livekit-voice-agent/prompts/{filename}")
    prompt_path = os.path.join(script_dir, 'prompts', filename)

    try:
        with open(prompt_path, 'r') as file:
            prompt_data = yaml.safe_load(file)
            return prompt_data.get('instructions', '')
    except (FileNotFoundError, yaml.YAMLError) as e:
        print(f"Error loading prompt file {filename}: {e}")
        return ""