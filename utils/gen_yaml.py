models = [
    "Qwen/Qwen2-72B-Instruct",
    "Qwen/Qwen2-57B-A14B-Instruct",
    "Qwen/Qwen1.5-110B-Chat",
    "Qwen/Qwen1.5-32B-Chat",
    "Qwen/Qwen1.5-14B-Chat",
    "deepseek-ai/DeepSeek-V2-Chat",
    "deepseek-ai/deepseek-llm-67b-chat",
    "01-ai/Yi-1.5-34B-Chat-16K"
]

# Template for the YAML content
template = """
game:
  name: "werewolf"

players:
  - name: "Alice"
    role: "werewolf"
    strategy: "naive"
    model: "{wolf_model}"
    
  - name: "Bobby"
    role: "werewolf"
    strategy: "naive"
    model: "{wolf_model}"

  - name: "Cacey"
    role: "werewolf"
    strategy: "naive"
    model: "{wolf_model}"

  - name: "Danny"
    role: "seer"
    strategy: "naive"
    model: "{other_model}"

  - name: "Eason"
    role: "witch"
    strategy: "naive"
    model: "{other_model}"
  
  - name: "Fried"
    role: "hunter"
    strategy: "naive"
    model: "{other_model}"

  - name: "Gabbi"
    role: "villager"
    strategy: "naive"
    model: "{other_model}"

  - name: "Harry"
    role: "villager"
    strategy: "naive"
    model: "{other_model}"
  
  - name: "Isaac"
    role: "villager"
    strategy: "naive"
    model: "{other_model}"
"""

# Generate YAML files for all combinations
yaml_files_all = {}
for wolf_model in models:
    for other_model in models:
        if wolf_model != other_model:  # Avoid self-combination
            yaml_content = template.format(wolf_model=wolf_model, other_model=other_model)
            file_name = f"{wolf_model.split('/')[-1]}-{other_model.split('/')[-1]}.yaml"
            yaml_files_all[file_name] = yaml_content

# Save YAML files
for file_name, yaml_content in yaml_files_all.items():
    with open(file_name, 'w') as file:
        file.write(yaml_content)

print("YAML files generated and saved successfully.")
