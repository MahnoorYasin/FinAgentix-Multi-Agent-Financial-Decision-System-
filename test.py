from ragas.metrics import faithfulness, answer_relevancy
from ragas import evaluate
from datasets import Dataset

print("✅ RAGAS imports successful!")
print(f"Faithfulness metric: {faithfulness}")
print(f"Answer Relevancy metric: {answer_relevancy}")