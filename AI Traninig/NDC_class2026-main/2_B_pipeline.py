from transformers import pipeline

# 1. Sentiment Analysis
classifier = pipeline("sentiment-analysis")
result = classifier("The Hugging Face Transformers library is easy to use!")
print("Sentiment Result:", result)

# 2. Text Generation
generator = pipeline("text-generation", model="gpt2")
output = generator("Autonomous systems in robotics are", max_length=30)
print("\nGenerated Text:\n", output[0]["generated_text"])