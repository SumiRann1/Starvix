import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "src"))
sys.path.append(str(ROOT))

from agent_cli import get_model, set_current_model, settings

# TESTING THE MODEL SWITCH AND response
print(settings.current_model)
res = get_model(settings.current_model).invoke("Hii there, How are you?")
print(res.content)
set_current_model("nemotron_3_ultra")
print(settings.current_model)
res2 = get_model(settings.current_model).invoke("Hii there, How are you?")
print(res2.content)


# print("====== Printing all the Models ======\n")
# all_models = list_models()
# print(all_models)

# print("\n====== Default Model ======\n")
# m = get_model()
# print(m)

# print("\n====== Nemotron Model ======\n")
# nemotron = get_model("nemotron_3_ultra")
# print(nemotron)

# print("\n== Checking Response from 1 Model == \n")
# c = get_model("gpt_oss_120b")
# print(c.invoke("What are your thoughts on Acid Rain?"))

# print("\n=== Checking all models ===\n")
# for name in all_models:
#     print(f"Testing {name}...")
#     try:
#         model = get_model(name)
#         resp = model.invoke("hello")
#         print(f"Response: {resp.content}\n")
#     except Exception as e:
#         print(f"Error testing {name}: {e}\n")
