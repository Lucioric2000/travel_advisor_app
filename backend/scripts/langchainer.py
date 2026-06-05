import getpass
import os
import dotenv

dotenv.load_dotenv()
from langchain.chat_models import init_chat_model
if not os.environ.get("GOOGLE_API_KEY"):
  os.environ["GOOGLE_API_KEY"] = getpass.getpass("Enter API key for Gemini: ")


model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")
#model = init_chat_model("gpt-4o-mini", model_provider="openai")
msg = model.invoke("Hello, world!")
assert 0, msg