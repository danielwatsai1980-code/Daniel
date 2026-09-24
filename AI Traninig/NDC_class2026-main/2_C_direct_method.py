import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

model_id = "gpt2"

# Load pre-trained tokenizer and model architecture
tokenizer = AutoTokenizer.from_pretrained(model_id)
model = AutoModelForCausalLM.from_pretrained(model_id)

# Tokenize input string into input tensors
prompt = "The future of embedded robotics relies on"
inputs = tokenizer(prompt, return_tensors="pt")

# Generate response token IDs
with torch.no_grad():
    output_tokens = model.generate(**inputs, max_new_tokens=20)

# Decode token IDs back to human-readable text
decoded_text = tokenizer.decode(output_tokens[0], skip_special_tokens=True)
print("Output Text:\n", decoded_text)