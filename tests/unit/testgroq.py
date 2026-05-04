import os
from groq import Groq
from dotenv import load_dotenv

# Load environment variables FIRST
load_dotenv()
key = os.getenv("GROQ_API_KEY")

print(f"Using GROQ API Key: ...{key[-8:] if key else 'None'}")

# Initialize client WITH the key explicitly
client = Groq(api_key=key)

completion = client.chat.completions.create(
    model="llama-3.1-8b-instant",  # Standard Groq model
    messages=[
      {
        "role": "user",
        "content": "Fiduciary Check: Respond with 'Handshake Successful'"
      }
    ],
    temperature=1,
    max_completion_tokens=1024,
    top_p=1,
    stream=True,
    stop=None
)

for chunk in completion:
    print(chunk.choices[0].delta.content or "", end="")
