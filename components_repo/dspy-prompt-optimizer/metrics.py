"""
Evaluation metrics for prompt quality assessment.

This module provides a modular metric system that allows you to:
1. Use built-in metrics (QualityMetric, ExactMatchMetric, SemanticSimilarityMetric)
2. Create custom metrics by extending BaseMetric or using create_custom_metric()
3. Combine multiple metrics with create_composite_metric()

Example of creating a custom metric:
    
    # Option 1: Using the factory function
    def my_scorer(example, prediction):
        # Your scoring logic here
        return 0.8  # Return score between 0 and 1
    
    my_metric = create_custom_metric(my_scorer, name="MyMetric")
    
    # Option 2: Extending BaseMetric
    class MyMetric(BaseMetric):
        def score(self, example, prediction, trace=None) -> float:
            # Your scoring logic here
            return 0.8
"""

import logging
import dspy
from typing import Callable, Optional, Protocol
from abc import ABC, abstractmethod

# Configure logging for debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('metrics')


# Type alias for metric functions
MetricFunction = Callable[[dspy.Example, any, Optional[any]], float]


class MetricProtocol(Protocol):
    """Protocol defining the metric interface."""
    def __call__(self, example: dspy.Example, prediction, trace=None) -> float: ...


class BaseMetric(ABC):
    """
    Abstract base class for all metrics.
    
    Extend this class to create custom metrics with full control.
    
    Example:
        class LengthMetric(BaseMetric):
            def __init__(self, min_length: int = 10, max_length: int = 500):
                super().__init__(name="LengthMetric")
                self.min_length = min_length
                self.max_length = max_length
            
            def score(self, example, prediction, trace=None) -> float:
                output = self.get_prediction_text(prediction)
                length = len(output)
                if self.min_length <= length <= self.max_length:
                    return 1.0
                return 0.0
    """
    
    def __init__(self, name: str = None):
        self.name = name or self.__class__.__name__
    
    @abstractmethod
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        """
        Compute the score for a prediction.
        
        Args:
            example: The input example with expected fields
            prediction: The model's prediction/output
            trace: Optional trace for debugging
            
        Returns:
            A score between 0 and 1
        """
        pass
    
    def __call__(self, example: dspy.Example, prediction, trace=None) -> float:
        """Make the metric callable."""
        return self.score(example, prediction, trace)
    
    def get_prediction_text(self, prediction) -> str:
        """Helper to extract text from prediction object."""
        if hasattr(prediction, 'output'):
            return str(prediction.output)
        elif hasattr(prediction, 'answer'):
            return str(prediction.answer)
        return str(prediction)
    
    def get_expected_text(self, example: dspy.Example) -> Optional[str]:
        """Helper to extract expected output from example."""
        for field in ['output', 'answer', 'label', 'expected']:
            if hasattr(example, field):
                return str(getattr(example, field))
        return None
    
    def get_input_text(self, example: dspy.Example) -> str:
        """Helper to extract input text from example."""
        for field in ['input', 'question', 'query', 'text', 'prompt']:
            if hasattr(example, field):
                return str(getattr(example, field))
        # Return all non-output fields as string
        fields = {k: v for k, v in example.items() if k not in ['output', 'answer', 'label']}
        return str(fields)
    
    def __repr__(self):
        return f"{self.name}()"


class QualityMetric(BaseMetric):
    """
    A quality metric that uses an LLM to evaluate response quality.
    
    Evaluates multiple aspects in a single API call:
    - Relevance: Does the output address the input properly?
    - Clarity: Is the output clear and well-structured?
    - Completeness: Does the output cover all necessary aspects?
    
    Args:
        criteria: List of evaluation criteria (customizable)
        
    Example:
        # Default criteria
        metric = QualityMetric()
        
        # Custom criteria for code review
        metric = QualityMetric(criteria=[
            "code correctness",
            "follows best practices",
            "proper error handling",
            "readable and maintainable"
        ])
    """
    
    def __init__(self, criteria: list[str] = None):
        super().__init__(name="QualityMetric")
        self.criteria = criteria or [
            "relevance to the input",
            "clarity and coherence",
            "completeness of the response",
            "accuracy and correctness"
        ]
        self.evaluator = dspy.ChainOfThought(
            "input, output, criteria -> score: float, feedback: str"
        )
        logger.debug(f"QualityMetric initialized with {len(self.criteria)} criteria")
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        output = self.get_prediction_text(prediction)
        input_text = self.get_input_text(example)
        criteria_text = ", ".join(self.criteria)
        
        # Apply rate limiting
        from usage_tracker import get_rate_limiter
        rate_limiter = get_rate_limiter()
        rate_limiter.wait()
        
        try:
            logger.debug(f"QualityMetric: Evaluating output (length={len(output)} chars)")
            result = self.evaluator(
                input=input_text,
                output=output,
                criteria=f"Rate the output on a scale of 0-10 based on: {criteria_text}. "
                        f"Provide a single score and brief feedback."
            )
            score = self._parse_score(result.score)
            normalized_score = score / 10.0  # Normalize to 0-1
            logger.debug(f"QualityMetric: Score = {normalized_score:.2f}")
            return normalized_score
        except Exception as e:
            logger.warning(f"QualityMetric: Evaluation error - {e}")
            return 0.5
    
    def _parse_score(self, score_text) -> float:
        if isinstance(score_text, (int, float)):
            return float(score_text)
        import re
        numbers = re.findall(r'[\d.]+', str(score_text))
        if numbers:
            return float(numbers[0])
        return 5.0


class ExactMatchMetric(BaseMetric):
    """
    Exact match metric for cases where expected output is known.
    
    Args:
        case_sensitive: Whether comparison should be case-sensitive (default: False)
        strip_whitespace: Whether to strip whitespace before comparison (default: True)
    """
    
    def __init__(self, case_sensitive: bool = False, strip_whitespace: bool = True):
        super().__init__(name="ExactMatchMetric")
        self.case_sensitive = case_sensitive
        self.strip_whitespace = strip_whitespace
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        expected = self.get_expected_text(example)
        if expected is None:
            return 0.5
        
        predicted = self.get_prediction_text(prediction)
        
        if self.strip_whitespace:
            expected = expected.strip()
            predicted = predicted.strip()
        
        if not self.case_sensitive:
            expected = expected.lower()
            predicted = predicted.lower()
        
        return 1.0 if predicted == expected else 0.0


class ContainsMetric(BaseMetric):
    """
    Check if prediction contains expected keywords or phrases.
    
    Args:
        keywords: List of keywords/phrases that should appear in the output
        require_all: If True, all keywords must be present; if False, any keyword counts
        case_sensitive: Whether matching should be case-sensitive
    """
    
    def __init__(self, keywords: list[str] = None, require_all: bool = True, case_sensitive: bool = False):
        super().__init__(name="ContainsMetric")
        self.keywords = keywords or []
        self.require_all = require_all
        self.case_sensitive = case_sensitive
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        output = self.get_prediction_text(prediction)
        
        # Use keywords from example if not provided in init
        keywords = self.keywords
        if not keywords and hasattr(example, 'keywords'):
            keywords = example.keywords if isinstance(example.keywords, list) else [example.keywords]
        
        if not keywords:
            return 0.5  # No keywords to check
        
        if not self.case_sensitive:
            output = output.lower()
            keywords = [k.lower() for k in keywords]
        
        matches = sum(1 for k in keywords if k in output)
        
        if self.require_all:
            return 1.0 if matches == len(keywords) else matches / len(keywords)
        else:
            return 1.0 if matches > 0 else 0.0


class SemanticSimilarityMetric(BaseMetric):
    """
    Semantic similarity between expected and predicted outputs using LLM.
    More lenient than exact match, but still checks correctness.
    """
    
    def __init__(self):
        super().__init__(name="SemanticSimilarityMetric")
        self.evaluator = dspy.ChainOfThought(
            "expected, predicted -> similarity_score: float, reasoning: str"
        )
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        expected = self.get_expected_text(example)
        if expected is None:
            return 0.5
        
        predicted = self.get_prediction_text(prediction)
        
        try:
            result = self.evaluator(
                expected=expected,
                predicted=predicted
            )
            score = float(result.similarity_score) if result.similarity_score else 0.5
            return min(max(score, 0.0), 1.0)
        except:
            return 0.5


class LengthMetric(BaseMetric):
    """
    Evaluate output based on length constraints.
    
    Args:
        min_length: Minimum acceptable length (default: 1)
        max_length: Maximum acceptable length (default: 1000)
        target_length: Ideal length (optional, for gradient scoring)
    """
    
    def __init__(self, min_length: int = 1, max_length: int = 1000, target_length: int = None):
        super().__init__(name="LengthMetric")
        self.min_length = min_length
        self.max_length = max_length
        self.target_length = target_length
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        output = self.get_prediction_text(prediction)
        length = len(output)
        
        if length < self.min_length or length > self.max_length:
            return 0.0
        
        if self.target_length:
            # Score based on distance from target
            distance = abs(length - self.target_length)
            max_distance = max(self.target_length - self.min_length, self.max_length - self.target_length)
            return 1.0 - (distance / max_distance) if max_distance > 0 else 1.0
        
        return 1.0


class CompositeMetric(BaseMetric):
    """
    Combine multiple metrics with optional weights.
    
    Args:
        metrics: List of metric instances or callables
        weights: Optional weights for each metric (defaults to equal weights)
        aggregation: How to combine scores - "weighted_avg", "min", "max", "product"
        
    Example:
        composite = CompositeMetric(
            metrics=[QualityMetric(), ExactMatchMetric()],
            weights=[0.7, 0.3],
            aggregation="weighted_avg"
        )
    """
    
    VALID_AGGREGATIONS = ["weighted_avg", "min", "max", "product"]
    
    def __init__(
        self, 
        metrics: list, 
        weights: list[float] = None,
        aggregation: str = "weighted_avg"
    ):
        super().__init__(name="CompositeMetric")
        self.metrics = metrics
        self.weights = weights or [1.0 / len(metrics)] * len(metrics)
        
        if aggregation not in self.VALID_AGGREGATIONS:
            raise ValueError(f"aggregation must be one of {self.VALID_AGGREGATIONS}")
        self.aggregation = aggregation
        
        if len(self.weights) != len(self.metrics):
            raise ValueError("Number of weights must match number of metrics")
    
    def score(self, example: dspy.Example, prediction, trace=None) -> float:
        scores = [m(example, prediction, trace) for m in self.metrics]
        
        if self.aggregation == "weighted_avg":
            return sum(s * w for s, w in zip(scores, self.weights))
        elif self.aggregation == "min":
            return min(scores)
        elif self.aggregation == "max":
            return max(scores)
        elif self.aggregation == "product":
            result = 1.0
            for s in scores:
                result *= s
            return result
        
        return sum(scores) / len(scores)
    
    def __repr__(self):
        metric_names = [getattr(m, 'name', m.__class__.__name__) for m in self.metrics]
        return f"CompositeMetric({metric_names}, aggregation={self.aggregation})"


# ============================================================================
# Factory functions for creating custom metrics
# ============================================================================

def create_custom_metric(
    scorer_fn: Callable[[dspy.Example, any], float],
    name: str = "CustomMetric"
) -> BaseMetric:
    """
    Create a custom metric from a simple scoring function.
    
    This is the easiest way to create a custom metric without extending BaseMetric.
    
    Args:
        scorer_fn: A function that takes (example, prediction) and returns a score (0-1)
        name: Name for the metric
        
    Returns:
        A metric instance
        
    Example:
        def word_count_scorer(example, prediction):
            output = str(prediction.output) if hasattr(prediction, 'output') else str(prediction)
            word_count = len(output.split())
            return min(word_count / 100, 1.0)  # Score based on word count
        
        word_metric = create_custom_metric(word_count_scorer, name="WordCountMetric")
    """
    class CustomMetric(BaseMetric):
        def __init__(self):
            super().__init__(name=name)
            self._scorer_fn = scorer_fn
        
        def score(self, example, prediction, trace=None):
            return self._scorer_fn(example, prediction)
    
    return CustomMetric()


def create_llm_metric(
    evaluation_prompt: str,
    criteria: str = None,
    name: str = "LLMMetric"
) -> BaseMetric:
    """
    Create a custom LLM-based metric with a custom evaluation prompt.
    
    Args:
        evaluation_prompt: The prompt template for evaluation
        criteria: Additional criteria description
        name: Name for the metric
        
    Returns:
        A metric instance
        
    Example:
        metric = create_llm_metric(
            evaluation_prompt="Is this response helpful and accurate?",
            criteria="helpfulness, accuracy, conciseness",
            name="HelpfulnessMetric"
        )
    """
    class LLMMetric(BaseMetric):
        def __init__(self):
            super().__init__(name=name)
            self.evaluator = dspy.ChainOfThought(
                "input, output, instruction -> score: float, reasoning: str"
            )
            self.prompt = evaluation_prompt
            self.criteria = criteria
        
        def score(self, example, prediction, trace=None):
            output = self.get_prediction_text(prediction)
            input_text = self.get_input_text(example)
            
            instruction = self.prompt
            if self.criteria:
                instruction += f"\n\nEvaluate based on: {self.criteria}"
            instruction += "\n\nProvide a score from 0.0 to 1.0"
            
            try:
                result = self.evaluator(
                    input=input_text,
                    output=output,
                    instruction=instruction
                )
                score = float(result.score) if result.score else 0.5
                return min(max(score, 0.0), 1.0)
            except:
                return 0.5
    
    return LLMMetric()


def create_composite_metric(
    metrics: list, 
    weights: list[float] = None,
    aggregation: str = "weighted_avg"
) -> CompositeMetric:
    """
    Create a composite metric from multiple metrics with optional weights.
    
    Args:
        metrics: List of metric functions/classes
        weights: Optional weights for each metric (defaults to equal weights)
        aggregation: How to combine - "weighted_avg", "min", "max", "product"
        
    Returns:
        A CompositeMetric instance
        
    Example:
        # 70% quality, 30% exact match
        combined = create_composite_metric(
            [QualityMetric(), ExactMatchMetric()],
            weights=[0.7, 0.3]
        )
        
        # All metrics must pass (use min)
        strict = create_composite_metric(
            [LengthMetric(min_length=10), QualityMetric()],
            aggregation="min"
        )
    """
    return CompositeMetric(metrics=metrics, weights=weights, aggregation=aggregation)


# ============================================================================
# Metric Registry for easy access
# ============================================================================

class MetricRegistry:
    """
    Registry of available metrics for easy discovery and instantiation.
    
    Example:
        # List available metrics
        print(MetricRegistry.list_metrics())
        
        # Get a metric by name
        metric = MetricRegistry.get("quality")
        
        # Register a custom metric
        MetricRegistry.register("my_metric", MyCustomMetric)
    """
    
    _metrics = {
        "quality": QualityMetric,
        "exact_match": ExactMatchMetric,
        "semantic": SemanticSimilarityMetric,
        "contains": ContainsMetric,
        "length": LengthMetric,
    }
    
    @classmethod
    def register(cls, name: str, metric_class: type):
        """Register a new metric class."""
        cls._metrics[name.lower()] = metric_class
    
    @classmethod
    def get(cls, name: str, **kwargs) -> BaseMetric:
        """Get a metric instance by name."""
        name = name.lower()
        if name not in cls._metrics:
            raise ValueError(f"Unknown metric: {name}. Available: {list(cls._metrics.keys())}")
        return cls._metrics[name](**kwargs)
    
    @classmethod
    def list_metrics(cls) -> list[str]:
        """List all registered metric names."""
        return list(cls._metrics.keys())
    
    @classmethod
    def get_info(cls) -> dict:
        """Get information about all registered metrics."""
        return {
            name: {
                "class": metric_class.__name__,
                "doc": metric_class.__doc__.split('\n')[1].strip() if metric_class.__doc__ else ""
            }
            for name, metric_class in cls._metrics.items()
        }
