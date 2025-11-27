"""
Example usage of the DSPy Prompt Optimizer.

This demonstrates how to:
1. Set up the Gemini API
2. Create a prompt with variables
3. Prepare a dataset
4. Optimize the prompt
5. Use the optimized prompt
6. Track and display API usage statistics
"""

import pandas as pd
from config import configure_gemini
from optimizer import PromptOptimizer, IterativePromptRefiner
from metrics import QualityMetric, SemanticSimilarityMetric, create_composite_metric
from usage_tracker import UsageTracker


def main():
    # 1. Configure Gemini API (track_usage=True is default)
    print("Configuring Gemini API...")
    configure_gemini(model_name="gemini-2.0-flash")  # Fast and efficient model
    
    # 2. Define your prompt template
    # Variables are the column names from your dataset
    prompt_template = """
    You are a helpful assistant that answers questions.
    
    Question: {question}
    Context: {context}
    
    Provide a clear and accurate answer.
    """
    
    # 3. Create sample dataset
    # In real usage, load this from CSV: pd.read_csv("your_data.csv")
    data = pd.DataFrame({
        "question": [
            "What is the capital of France?",
            "Who wrote Romeo and Juliet?",
            "What is photosynthesis?",
            "When did World War II end?",
            "What is the speed of light?",
            "Who painted the Mona Lisa?",
        ],
        "context": [
            "France is a country in Western Europe known for its culture and history.",
            "Romeo and Juliet is a famous tragedy written in the 16th century.",
            "Photosynthesis is a biological process that occurs in plants.",
            "World War II was a global conflict that involved most nations.",
            "Light travels at a constant speed in a vacuum.",
            "The Mona Lisa is displayed in the Louvre Museum in Paris.",
        ],
        "output": [  # Expected outputs for evaluation (optional but helpful)
            "Paris",
            "William Shakespeare",
            "The process by which plants convert sunlight into energy",
            "1945",
            "Approximately 299,792 kilometers per second",
            "Leonardo da Vinci",
        ]
    })
    
    print(f"Dataset loaded: {len(data)} examples")
    
    # 4. Create the optimizer
    print("\nCreating prompt optimizer...")
    optimizer = PromptOptimizer(
        prompt_template=prompt_template,
        input_variables=["question", "context"],
        output_variable="output",
        metric=QualityMetric()  # Uses LLM to evaluate quality
    )
    
    # 5. Run optimization (efficient - uses bootstrap method)
    # Parameter limits:
    #   - max_iterations: 1-10 (recommended: 2-3 for efficiency)
    #   - samples_per_iteration: 0-5 (recommended: 3-5 for balance)
    #   - performance_threshold: 0.0-1.0 (default: 0.8) - skip optimization if initial score >= threshold
    # Available optimizer_type options:
    #   - "bootstrap": BootstrapFewShot - efficient, uses few examples (default, recommended)
    #   - "mipro": MIPROv2 - more thorough optimization, uses more API calls
    print("\nOptimizing prompt (this may take a minute)...")
    result = optimizer.optimize(
        train_data=data,
        max_iterations=2,  # Range: 1-10 (keep low for efficiency)
        samples_per_iteration=3,  # Range: 0-5
        optimizer_type="bootstrap",  # Options: "bootstrap" (efficient) or "mipro" (thorough)
        performance_threshold=0.85,  # Skip if initial score >= 80% (default: 0.8)
        skip_if_above_threshold=True  # Set to False to always optimize
    )
    
    # 6. Print results (includes usage stats automatically)
    print(result)  # Uses OptimizationResult.__str__() which includes usage stats
    
    print(f"\nOriginal Prompt:\n{result.original_prompt}")
    print(f"\nOptimized Prompt:\n{result.optimized_prompt}")
    
    if result.feedback:
        print("\nFeedback:")
        for fb in result.feedback[:5]:  # Show first 5
            print(f"  - {fb}")
    
    # 7. Print detailed usage statistics
    print("\n")
    result.print_usage()  # Detailed API usage breakdown
    
    # 8. Use the optimized prompt
    print("\n" + "="*60)
    print("TESTING OPTIMIZED PROMPT")
    print("="*60)
    
    test_question = "What is machine learning?"
    test_context = "Machine learning is a subset of artificial intelligence."
    
    answer = optimizer.run(question=test_question, context=test_context)
    print(f"Question: {test_question}")
    print(f"Context: {test_context}")
    print(f"Answer: {answer}")


def example_iterative_refinement():
    """
    Example of using the IterativePromptRefiner for more control.
    
    This approach gives you more visibility into what's being improved.
    """
    import dspy
    from config import configure_gemini
    from metrics import QualityMetric
    
    configure_gemini()
    
    # Initial prompt that might have issues
    initial_prompt = """
    Answer the following question briefly.
    Question: {question}
    """
    
    # Sample data
    test_cases = [
        {"question": "Explain quantum computing", "expected": "detailed technical explanation"},
        {"question": "What causes rain?", "expected": "water cycle explanation"},
        {"question": "How do vaccines work?", "expected": "immune system response explanation"},
    ]
    
    metric = QualityMetric(criteria=[
        "accuracy",
        "depth of explanation",
        "clarity"
    ])
    
    def evaluator(prompt):
        """Custom evaluator function."""
        predictor = dspy.ChainOfThought("question -> answer")
        
        examples = []
        scores = []
        
        for tc in test_cases:
            result = predictor(question=tc["question"])
            example = dspy.Example(question=tc["question"], output=result.answer)
            score = metric(example, result)
            
            examples.append({"question": tc["question"], "answer": result.answer})
            scores.append(score)
        
        avg_score = sum(scores) / len(scores)
        return avg_score, examples, scores
    
    # Run iterative refinement
    refiner = IterativePromptRefiner(max_iterations=3)
    result = refiner.optimize(initial_prompt, evaluator)
    
    print("Iterative Refinement Results:")
    print(f"Original: {result.original_prompt}")
    print(f"Optimized: {result.optimized_prompt}")
    print(f"Score improvement: {result.original_score:.2%} -> {result.optimized_score:.2%}")
    
    for fb in result.feedback:
        print(f"  {fb}")


def example_custom_metric():
    """
    Example showing how to use custom metrics for specific use cases.
    
    The metric system is modular - you can:
    1. Use built-in metrics (QualityMetric, ExactMatchMetric, etc.)
    2. Create custom metrics with create_custom_metric()
    3. Create LLM-based metrics with create_llm_metric()
    4. Combine metrics with create_composite_metric()
    5. Use MetricRegistry to discover and instantiate metrics
    """
    from config import configure_gemini
    from metrics import (
        QualityMetric, 
        ExactMatchMetric, 
        ContainsMetric,
        LengthMetric,
        create_composite_metric,
        create_custom_metric,
        create_llm_metric,
        MetricRegistry,
        BaseMetric
    )
    
    configure_gemini()
    
    # =========================================================================
    # Option 1: Use built-in metrics
    # =========================================================================
    quality_metric = QualityMetric(criteria=["accuracy", "helpfulness"])
    exact_metric = ExactMatchMetric(case_sensitive=False)
    contains_metric = ContainsMetric(keywords=["the", "is"], require_all=False)
    length_metric = LengthMetric(min_length=10, max_length=500)
    
    # =========================================================================
    # Option 2: Create a custom metric from a simple function
    # =========================================================================
    def word_count_scorer(example, prediction):
        """Score based on word count - prefer 20-50 words."""
        output = str(prediction.output) if hasattr(prediction, 'output') else str(prediction)
        word_count = len(output.split())
        if 20 <= word_count <= 50:
            return 1.0
        elif word_count < 20:
            return word_count / 20
        else:
            return max(0, 1 - (word_count - 50) / 100)
    
    word_count_metric = create_custom_metric(word_count_scorer, name="WordCountMetric")
    
    # =========================================================================
    # Option 3: Create a custom LLM-based metric
    # =========================================================================
    helpfulness_metric = create_llm_metric(
        evaluation_prompt="Rate how helpful and actionable this response is.",
        criteria="helpfulness, actionability, user-friendliness",
        name="HelpfulnessMetric"
    )
    
    # =========================================================================
    # Option 4: Extend BaseMetric for full control
    # =========================================================================
    class SentimentMetric(BaseMetric):
        """Check if response has positive sentiment."""
        def __init__(self):
            super().__init__(name="SentimentMetric")
            self.positive_words = ["great", "good", "excellent", "helpful", "thank"]
            self.negative_words = ["bad", "wrong", "error", "fail", "sorry"]
        
        def score(self, example, prediction, trace=None) -> float:
            output = self.get_prediction_text(prediction).lower()
            pos_count = sum(1 for w in self.positive_words if w in output)
            neg_count = sum(1 for w in self.negative_words if w in output)
            total = pos_count + neg_count
            if total == 0:
                return 0.5
            return pos_count / total
    
    sentiment_metric = SentimentMetric()
    
    # =========================================================================
    # Option 5: Combine metrics with different aggregation strategies
    # =========================================================================
    
    # Weighted average (default)
    combined_weighted = create_composite_metric(
        [quality_metric, exact_metric],
        weights=[0.7, 0.3],
        aggregation="weighted_avg"
    )
    
    # All metrics must pass (use min)
    combined_strict = create_composite_metric(
        [length_metric, quality_metric],
        aggregation="min"
    )
    
    # Any metric passing is good (use max)
    combined_lenient = create_composite_metric(
        [exact_metric, contains_metric],
        aggregation="max"
    )
    
    # =========================================================================
    # Option 6: Use MetricRegistry to discover metrics
    # =========================================================================
    print("Available metrics:", MetricRegistry.list_metrics())
    
    # Get a metric by name
    quality = MetricRegistry.get("quality", criteria=["accuracy"])
    semantic = MetricRegistry.get("semantic")
    
    # Register your custom metric for reuse
    MetricRegistry.register("sentiment", SentimentMetric)
    
    # =========================================================================
    # Use with optimizer
    # =========================================================================
    data = pd.DataFrame({
        "question": ["What is 2+2?", "What is the capital of Japan?"],
        "output": ["4", "Tokyo"]
    })
    
    optimizer = PromptOptimizer(
        prompt_template="Answer precisely: {question}",
        input_variables=["question"],
        metric=combined_weighted  # Swap in any metric here!
    )
    
    result = optimizer.optimize(data, max_iterations=2)
    print(f"Optimization complete. Score: {result.optimized_score:.2%}")
    
    # Print usage stats
    result.print_usage()


def example_usage_tracking():
    """
    Example showing how to track API usage and token consumption.
    
    The usage tracker provides:
    - Number of API calls
    - Input/output token counts
    - Estimated costs (based on model pricing)
    """
    from config import configure_gemini
    from optimizer import PromptOptimizer
    from metrics import QualityMetric
    from usage_tracker import UsageTracker
    
    # Method 1: Automatic tracking (enabled by default in configure_gemini)
    configure_gemini(track_usage=True)  # This starts tracking automatically
    
    data = pd.DataFrame({
        "question": ["What is AI?", "What is ML?"],
        "output": ["Artificial Intelligence", "Machine Learning"]
    })
    
    optimizer = PromptOptimizer(
        prompt_template="Define: {question}",
        input_variables=["question"],
        metric=QualityMetric()
    )
    
    result = optimizer.optimize(data, max_iterations=1, samples_per_iteration=2)
    
    # Usage is automatically included in the result
    print(result)  # Includes usage stats in output
    result.print_usage()  # Detailed breakdown
    
    # Access raw stats programmatically
    if result.usage_stats:
        print(f"\nProgrammatic access:")
        print(f"  API Calls: {result.usage_stats.api_calls}")
        print(f"  Tokens: {result.usage_stats.total_tokens}")
        print(f"  Cost: ${result.usage_stats.estimated_cost:.6f}")
    
    # Method 2: Manual tracking with context manager
    UsageTracker.reset()  # Reset counters
    UsageTracker.start()
    
    # ... do some LLM operations ...
    answer = optimizer.run(question="What is deep learning?")
    
    stats = UsageTracker.get_stats()
    print(f"\nManual tracking stats:")
    print(stats)
    
    # Method 3: Context manager for scoped tracking
    with UsageTracker.track() as stats:
        answer = optimizer.run(question="What is a neural network?")
    
    print(f"\nScoped tracking stats:")
    print(stats)


if __name__ == "__main__":
    print("DSPy Prompt Optimizer Demo")
    print("="*60)
    print("\nMake sure to set GOOGLE_API_KEY in .env file first!")
    print("Get your API key from: https://aistudio.google.com/app/apikey\n")
    
    # Run main example
    main()
    
    # Uncomment to run other examples:
    # example_iterative_refinement()
    # example_custom_metric()
    # example_usage_tracking()
