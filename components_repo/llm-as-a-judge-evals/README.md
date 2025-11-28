# LLM-as-a-Judge Evaluations

![Component ID](https://img.shields.io/badge/Component%20ID-comp__c642a-blue)
![Version](https://img.shields.io/badge/Version-v1.0.0-green)

A flexible evaluation framework that uses Large Language Models as judges to assess AI-generated responses. Supports multiple LLM providers (OpenAI, Anthropic, Google Gemini) and includes a comprehensive library of evaluation metrics.

## 🚀 Features

- **Multi-Provider Support**: Works with OpenAI, Anthropic, and Google Gemini models.
- **Pre-built Metrics**: Includes pointwise and pairwise evaluation templates for coherence, fluency, safety, groundedness, and more.
- **Structured Outputs**: Uses Pydantic models to ensure consistent rating and explanation responses.
- **Batch Evaluation**: Evaluate entire datasets with automatic metric aggregation.
- **Extensible**: Easily create custom evaluation metrics with your own prompt templates.

## 🛠️ Installation

1. Clone or download this component.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Set up your API keys for the LLM provider(s) you want to use.

## 📖 Usage

### Basic Evaluation

```python
import pandas as pd
from metrics.eval_templates import EvalMetricTemplates
from metrics.eval_metrics import EvalMetric
from llms.llm_client import LLMClient
from evaluation.eval_engine import Evaluator

# Set your API key
GEMINI_API_KEY = "your_api_key_here"

# Create a dataset with prompts and responses to evaluate
dataset = pd.DataFrame({
    "prompt": ["What is AI?", "Explain quantum computing."],
    "response": ["AI is the simulation of human intelligence.", "Quantum computing uses quantum bits."]
})

# Define evaluation metrics using pre-built templates
fluency = EvalMetric(
    metric_name="fluency",
    metric_prompt_template=EvalMetricTemplates.PointwiseMetric.FLUENCY
)
coherence = EvalMetric(
    metric_name="coherence",
    metric_prompt_template=EvalMetricTemplates.PointwiseMetric.COHERENCE
)

# Initialize LLM client with judge model
llm_client = LLMClient(
    judge_model="google/gemini-2.0-flash-lite",
    api_key=GEMINI_API_KEY
)

# Create evaluator and run evaluation
evaluator = Evaluator(llm_client=llm_client, eval_metrics=[fluency, coherence])
eval_table, summary = evaluator.evaluate(dataset=dataset)

print(eval_table)
print(summary)
```

### Available Metrics

**Pointwise Metrics** (evaluate single responses):
- `COHERENCE` - Logical flow and organization of ideas
- `FLUENCY` - Grammar, word choice, and natural flow
- `SAFETY` - Absence of harmful or inappropriate content
- `GROUNDEDNESS` - Factual accuracy based on provided context
- `INSTRUCTION_FOLLOWING` - Adherence to user instructions
- `VERBOSITY` - Appropriate response length
- `MULTI_TURN_CHAT_QUALITY` - Quality in conversational context

**Pairwise Metrics** (compare two responses):
- `PAIRWISE_COHERENCE` - Compare coherence between responses
- `PAIRWISE_FLUENCY` - Compare fluency between responses
- `PAIRWISE_SAFETY` - Compare safety between responses

### Supported LLM Providers

| Provider | Model Format | Example |
|----------|--------------|---------|
| OpenAI | `openai/model-name` | `openai/gpt-4o` |
| Anthropic | `anthropic/model-name` | `anthropic/claude-3-sonnet` |
| Google | `google/model-name` | `google/gemini-2.0-flash-lite` |

### Custom Metrics

Create your own evaluation metrics with custom prompt templates:

```python
custom_template = """
# Instruction
Evaluate the response for technical accuracy.

## Rating Rubric
5: Completely accurate
3: Partially accurate
1: Inaccurate

## User Input
{prompt}

## Response
{response}
"""

custom_metric = EvalMetric(
    metric_name="technical_accuracy",
    metric_prompt_template=custom_template
)
```

## 📋 Metadata

- **Author**: Vijay Ram Enaganti
- **Tags**: `LLM`, `evaluation`, `AI-judge`, `metrics`, `benchmarking`
