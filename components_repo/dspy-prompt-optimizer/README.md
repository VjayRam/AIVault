# DSPy Prompt Optimizer

![Component ID](https://img.shields.io/badge/Component%20ID-comp__dspy1-blue)
![Version](https://img.shields.io/badge/Version-v1.0.0-green)

A simple automatic prompt optimizer for better reasoning using DSPy and Google Gemini API.

## 🚀 Features

- **Automatic Prompt Optimization**: Given a prompt template with variables, automatically finds and fixes flaws.
- **Quality Metrics**: Built-in evaluation metrics for quality, semantic similarity, and exact match.
- **Efficient API Usage**: Optimized to minimize API calls using DSPy's bootstrap optimization.
- **Iterative Refinement**: Meta-learning approach that analyzes failures and improves prompts.

## 🛠️ Installation

1. Clone or download this project.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your Google API key:
   - Get your API key from [Google AI Studio](https://aistudio.google.com/app/apikey).
   - Create a `.env` file (copy from `.env.example`):
   ```
   GOOGLE_API_KEY=your_api_key_here
   ```

## 📖 Usage

### Basic Optimization

```python
import pandas as pd
from config import configure_gemini
from optimizer import PromptOptimizer
from metrics import QualityMetric

# Configure Gemini API
configure_gemini()

# Define your prompt template with variables
prompt_template = """
You are a helpful assistant.
Question: {question}
Context: {context}
Provide a clear answer.
"""

# Create your dataset (columns should match variables)
data = pd.DataFrame({
    "question": ["What is AI?", "How does ML work?"],
    "context": ["AI is artificial intelligence", "ML is machine learning"],
    "output": ["Expected answer 1", "Expected answer 2"]  # Optional
})

# Create and run optimizer
optimizer = PromptOptimizer(
    prompt_template=prompt_template,
    input_variables=["question", "context"],
    metric=QualityMetric()
)

result = optimizer.optimize(data, max_iterations=2)

print(f"Improvement: {result.improvement:+.2%}")
print(f"Optimized prompt: {result.optimized_prompt}")

# Use the optimized prompt
answer = optimizer.run(question="What is deep learning?", context="DL uses neural networks")
```

### Available Metrics

- **QualityMetric**: LLM-based evaluation of relevance, clarity, completeness, and accuracy.
- **ExactMatchMetric**: Checks if output matches expected exactly.
- **SemanticSimilarityMetric**: LLM-based semantic similarity check.
- **Composite Metrics**: Combine multiple metrics with custom weights.

### Optimization Strategies

**Bootstrap (Default - Efficient):** Uses few examples to learn patterns. Minimal API calls.

```python
result = optimizer.optimize(data, optimizer_type="bootstrap")
```

**MIPROv2 (Thorough):** More comprehensive optimization. Uses more API calls but can find better prompts.

```python
result = optimizer.optimize(data, optimizer_type="mipro")
```

**Iterative Refinement:** Uses meta-learning to analyze failures and suggest improvements.

```python
from optimizer import IterativePromptRefiner

refiner = IterativePromptRefiner(max_iterations=3)
result = refiner.optimize(initial_prompt, evaluator_function)
```

### Efficiency Tips

1. Use `gemini-2.0-flash` (default) for faster, cheaper API calls.
2. Keep `samples_per_iteration` low (3-5) during optimization.
3. Use `optimizer_type="bootstrap"` unless you need thorough optimization.
4. Start with `max_iterations=2` and increase if needed.

## 📋 Metadata

- **Author**: Vijay Ram Enaganti
- **Tags**: `DSPy`, `prompt-engineering`, `LLM`, `optimization`, `Gemini`
- **Component ID**: `comp_f1861`
