"""
Core Prompt Optimizer using DSPy.

This module provides an efficient automatic prompt optimizer that:
1. Takes a prompt template with variables
2. Evaluates it against a dataset
3. Identifies flaws using quality metrics
4. Iteratively improves the prompt

Optimized for minimal API calls using DSPy's built-in optimizers.
"""

import logging
import dspy
import pandas as pd
from typing import Optional
from dataclasses import dataclass, field
from usage_tracker import UsageTracker, UsageStats, get_rate_limiter

# Configure logging for debug output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger('optimizer')


@dataclass
class OptimizationResult:
    """Result of prompt optimization."""
    original_prompt: str
    optimized_prompt: str
    original_score: float
    optimized_score: float
    improvement: float
    iterations: int
    feedback: list[str]
    usage_stats: Optional[UsageStats] = None
    
    def print_usage(self):
        """Print the usage statistics."""
        if self.usage_stats:
            print(self.usage_stats)
        else:
            print("No usage statistics available. Enable tracking with track_usage=True.")
    
    def __str__(self) -> str:
        lines = [
            "=" * 60,
            "OPTIMIZATION RESULTS",
            "=" * 60,
            f"Original Score:  {self.original_score:.2%}",
            f"Optimized Score: {self.optimized_score:.2%}",
            f"Improvement:     {self.improvement:+.2%}",
            f"Iterations:      {self.iterations}",
        ]
        if self.usage_stats:
            lines.extend([
                "",
                f"API Calls:       {self.usage_stats.api_calls:,}",
                f"Total Tokens:    {self.usage_stats.total_tokens:,}",
                f"Est. Cost:       ${self.usage_stats.estimated_cost:.4f}",
            ])
        lines.append("=" * 60)
        return "\n".join(lines)


class PromptTemplate(dspy.Signature):
    """A flexible prompt template that takes variables and produces output."""
    pass


def create_dynamic_signature(input_fields: list[str], output_field: str = "output") -> type:
    """
    Dynamically create a DSPy Signature based on input fields.
    
    Args:
        input_fields: List of variable names that will be inputs
        output_field: Name of the output field
        
    Returns:
        A DSPy Signature class
    """
    # Build the signature string
    inputs = ", ".join(input_fields)
    sig_string = f"{inputs} -> {output_field}"
    
    return dspy.Signature(sig_string)


class PromptOptimizer:
    """
    An efficient automatic prompt optimizer using DSPy and Gemini.
    
    This optimizer:
    1. Wraps a prompt template in a DSPy module
    2. Uses batch evaluation to minimize API calls
    3. Applies DSPy's MIPROv2 or BootstrapFewShot for optimization
    4. Provides feedback on what was improved
    """
    
    def __init__(
        self,
        prompt_template: str,
        input_variables: list[str],
        output_variable: str = "output",
        metric = None
    ):
        """
        Initialize the optimizer.
        
        Args:
            prompt_template: The prompt template with {variable} placeholders
            input_variables: List of variable names used in the template
            output_variable: Name of the output field
            metric: Evaluation metric (defaults to QualityMetric)
        """
        logger.info("\ud83d\udee0\ufe0f  Initializing PromptOptimizer...")
        self.prompt_template = prompt_template
        self.input_variables = input_variables
        self.output_variable = output_variable
        
        # Import here to avoid circular imports
        from metrics import QualityMetric
        self.metric = metric or QualityMetric()
        logger.debug(f"Using metric: {type(self.metric).__name__}")
        
        # Create the DSPy module
        self._create_module()
        logger.info(f"\u2705 Optimizer initialized with {len(input_variables)} input variables")
    
    def _create_module(self):
        """Create the DSPy module for this prompt."""
        sig = create_dynamic_signature(self.input_variables, self.output_variable)
        logger.debug(f"Created signature: {self.input_variables} -> {self.output_variable}")
        
        # Create a module that uses the prompt template
        class PromptModule(dspy.Module):
            def __init__(inner_self, template: str, signature):
                super().__init__()
                inner_self.template = template
                inner_self.predictor = dspy.ChainOfThought(signature)
            
            def forward(inner_self, **kwargs):
                # Apply rate limiting before API call
                rate_limiter = get_rate_limiter()
                rate_limiter.wait()
                # The template is stored as a hint/instruction in the module
                return inner_self.predictor(**kwargs)
        
        self.module = PromptModule(self.prompt_template, sig)
    
    def load_dataset(self, data: pd.DataFrame) -> list[dspy.Example]:
        """
        Convert a pandas DataFrame to DSPy Examples.
        
        Args:
            data: DataFrame with columns matching input_variables (and optionally output)
            
        Returns:
            List of DSPy Examples
        """
        examples = []
        
        for _, row in data.iterrows():
            example_dict = {var: row[var] for var in self.input_variables if var in row}
            
            # Add expected output if present
            if self.output_variable in row:
                example_dict[self.output_variable] = row[self.output_variable]
            
            # Create example with input fields marked
            example = dspy.Example(**example_dict).with_inputs(*self.input_variables)
            examples.append(example)
        
        return examples
    
    def evaluate(self, examples: list[dspy.Example], sample_size: int = None) -> tuple[float, list[str]]:
        """
        Evaluate the current prompt on examples.
        
        Args:
            examples: List of examples to evaluate on
            sample_size: Optional limit on number of examples (for efficiency)
            
        Returns:
            Tuple of (average_score, list_of_feedback)
        """
        if sample_size and len(examples) > sample_size:
            import random
            examples = random.sample(examples, sample_size)
        
        logger.info(f"\ud83d\udcdd Evaluating on {len(examples)} examples...")
        scores = []
        feedback = []
        
        for i, example in enumerate(examples, 1):
            try:
                # Run prediction
                kwargs = {var: getattr(example, var) for var in self.input_variables}
                logger.debug(f"  [{i}/{len(examples)}] Processing example...")
                prediction = self.module(**kwargs)
                
                # Evaluate
                score = self.metric(example, prediction)
                scores.append(score)
                logger.debug(f"  [{i}/{len(examples)}] Score: {score:.2f}")
                
                if score < 0.7:  # Collect feedback for low-scoring examples
                    feedback.append(
                        f"Low score ({score:.2f}) for input: {kwargs}"
                    )
            except Exception as e:
                logger.warning(f"  [{i}/{len(examples)}] Error: {e}")
                feedback.append(f"Error during evaluation: {e}")
                scores.append(0.0)
        
        avg_score = sum(scores) / len(scores) if scores else 0.0
        logger.info(f"\u2705 Evaluation complete. Average score: {avg_score:.2%}")
        return avg_score, feedback
    
    # Parameter limits
    MAX_ITERATIONS_LIMIT = 10
    SAMPLES_PER_ITERATION_MIN = 0
    SAMPLES_PER_ITERATION_MAX = 5
    
    # Available optimizer types:
    # - "bootstrap": BootstrapFewShot - efficient, uses few examples (recommended for cost savings)
    # - "mipro": MIPROv2 - more thorough optimization, uses more API calls
    VALID_OPTIMIZER_TYPES = ["bootstrap", "mipro"]
    
    # Default performance threshold (0.0-1.0)
    # If initial prompt scores above this, optimization is skipped
    DEFAULT_PERFORMANCE_THRESHOLD = 0.8
    
    def optimize(
        self,
        train_data: pd.DataFrame,
        max_iterations: int = 3,
        samples_per_iteration: int = 5,
        optimizer_type: str = "bootstrap",
        performance_threshold: float = None,
        skip_if_above_threshold: bool = True
    ) -> OptimizationResult:
        """
        Optimize the prompt using the provided training data.
        
        Args:
            train_data: DataFrame with training examples
            max_iterations: Maximum optimization iterations (1-10, default: 3)
            samples_per_iteration: Number of samples to use per iteration (0-5, default: 5)
            optimizer_type: Type of optimizer. Options:
                - "bootstrap": BootstrapFewShot - efficient, few API calls (default)
                - "mipro": MIPROv2 - more thorough, more API calls
            performance_threshold: Score threshold (0.0-1.0) above which optimization is skipped.
                If None, uses DEFAULT_PERFORMANCE_THRESHOLD (0.8).
            skip_if_above_threshold: If True, skip optimization when initial score >= threshold.
                If False, always run optimization regardless of initial score. (default: True)
            
        Returns:
            OptimizationResult with optimized prompt and metrics
            
        Raises:
            ValueError: If parameters are out of valid range
        """
        # Set default threshold if not provided
        if performance_threshold is None:
            performance_threshold = self.DEFAULT_PERFORMANCE_THRESHOLD
        
        # Validate threshold
        if not 0.0 <= performance_threshold <= 1.0:
            raise ValueError(f"performance_threshold must be between 0.0 and 1.0, got {performance_threshold}")
        
        logger.info("=" * 60)
        logger.info("\ud83d\ude80 STARTING PROMPT OPTIMIZATION")
        logger.info("=" * 60)
        logger.info(f"   Optimizer type: {optimizer_type}")
        logger.info(f"   Max iterations: {max_iterations}")
        logger.info(f"   Samples/iteration: {samples_per_iteration}")
        logger.info(f"   Performance threshold: {performance_threshold:.0%}")
        logger.info(f"   Skip if above threshold: {skip_if_above_threshold}")
        
        # Validate and clamp parameters
        if max_iterations < 1 or max_iterations > self.MAX_ITERATIONS_LIMIT:
            raise ValueError(f"max_iterations must be between 1 and {self.MAX_ITERATIONS_LIMIT}, got {max_iterations}")
        
        if samples_per_iteration < self.SAMPLES_PER_ITERATION_MIN or samples_per_iteration > self.SAMPLES_PER_ITERATION_MAX:
            raise ValueError(f"samples_per_iteration must be between {self.SAMPLES_PER_ITERATION_MIN} and {self.SAMPLES_PER_ITERATION_MAX}, got {samples_per_iteration}")
        
        if optimizer_type not in self.VALID_OPTIMIZER_TYPES:
            raise ValueError(f"optimizer_type must be one of {self.VALID_OPTIMIZER_TYPES}, got '{optimizer_type}'")
        
        logger.info("\ud83d\udcca Loading dataset...")
        examples = self.load_dataset(train_data)
        logger.info(f"   Loaded {len(examples)} examples")
        
        # Split into train/dev for optimization
        split_idx = max(1, len(examples) * 2 // 3)
        trainset = examples[:split_idx]
        devset = examples[split_idx:] if split_idx < len(examples) else examples[:2]
        logger.info(f"   Train set: {len(trainset)} examples, Dev set: {len(devset)} examples")
        
        # Evaluate original
        logger.info("\n\ud83d\udcdd Phase 1: Evaluating ORIGINAL prompt...")
        original_score, initial_feedback = self.evaluate(
            devset, sample_size=samples_per_iteration
        )
        logger.info(f"\u2705 Original prompt score: {original_score:.2%}")
        
        all_feedback = initial_feedback.copy()
        
        # Check if optimization is needed based on threshold
        if skip_if_above_threshold and original_score >= performance_threshold:
            logger.info("\n" + "=" * 60)
            logger.info("\u2728 PROMPT ALREADY PERFORMING WELL - SKIPPING OPTIMIZATION")
            logger.info("=" * 60)
            logger.info(f"   Initial score ({original_score:.2%}) >= threshold ({performance_threshold:.0%})")
            logger.info("   No optimization needed!")
            logger.info("=" * 60)
            
            # Capture usage stats
            usage_stats = None
            if UsageTracker.is_tracking():
                usage_stats = UsageTracker.get_stats()
                usage_stats = UsageStats(
                    api_calls=usage_stats.api_calls,
                    input_tokens=usage_stats.input_tokens,
                    output_tokens=usage_stats.output_tokens,
                    total_tokens=usage_stats.total_tokens,
                    cost_per_1k_input_tokens=usage_stats.cost_per_1k_input_tokens,
                    cost_per_1k_output_tokens=usage_stats.cost_per_1k_output_tokens
                )
            
            return OptimizationResult(
                original_prompt=self.prompt_template,
                optimized_prompt=self.prompt_template,  # No change
                original_score=original_score,
                optimized_score=original_score,  # Same as original
                improvement=0.0,
                iterations=0,  # No iterations performed
                feedback=all_feedback + ["Optimization skipped: initial score above threshold"],
                usage_stats=usage_stats
            )
        
        # Log that optimization will proceed
        if original_score < performance_threshold:
            logger.info(f"\n\u26a0\ufe0f  Prompt underperforming (score {original_score:.2%} < threshold {performance_threshold:.0%})")
            logger.info("   Proceeding with optimization...")
        
        # Choose optimizer based on preference
        logger.info(f"\n\u2699\ufe0f  Phase 2: Running {optimizer_type} optimizer...")
        if optimizer_type == "mipro":
            # MIPROv2 is more thorough but uses more API calls
            logger.debug("   Using MIPROv2 with num_candidates=3")
            optimizer = dspy.MIPROv2(
                metric=self.metric,
                num_candidates=3,  # Keep low for efficiency
                init_temperature=1.0
            )
        else:
            # BootstrapFewShot is efficient - uses few examples to improve
            logger.debug("   Using BootstrapFewShot with max_bootstrapped_demos=2")
            optimizer = dspy.BootstrapFewShot(
                metric=self.metric,
                max_bootstrapped_demos=2,  # Keep small for efficiency
                max_labeled_demos=2
            )
        
        # Run optimization
        try:
            logger.info("   Compiling optimized module...")
            # MIPROv2 supports num_trials, BootstrapFewShot does not
            if optimizer_type == "mipro":
                optimized_module = optimizer.compile(
                    self.module,
                    trainset=trainset,
                    num_trials=max_iterations
                )
            else:
                optimized_module = optimizer.compile(
                    self.module,
                    trainset=trainset
                )
            self.module = optimized_module
            logger.info("   \u2705 Optimization compiled successfully")
        except Exception as e:
            logger.warning(f"   \u26a0\ufe0f Optimization warning: {e}")
            all_feedback.append(f"Optimization warning: {e}")
        
        # Evaluate optimized version
        logger.info("\n\ud83d\udcdd Phase 3: Evaluating OPTIMIZED prompt...")
        optimized_score, opt_feedback = self.evaluate(
            devset, sample_size=samples_per_iteration
        )
        logger.info(f"\u2705 Optimized prompt score: {optimized_score:.2%}")
        all_feedback.extend(opt_feedback)
        
        # Extract optimized prompt representation
        optimized_prompt = self._extract_prompt()
        
        # Capture usage stats
        usage_stats = None
        if UsageTracker.is_tracking():
            usage_stats = UsageTracker.get_stats()
            # Create a copy of the stats to preserve them
            usage_stats = UsageStats(
                api_calls=usage_stats.api_calls,
                input_tokens=usage_stats.input_tokens,
                output_tokens=usage_stats.output_tokens,
                total_tokens=usage_stats.total_tokens,
                cost_per_1k_input_tokens=usage_stats.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=usage_stats.cost_per_1k_output_tokens
            )
        
        # Log summary
        improvement = optimized_score - original_score
        logger.info("\n" + "=" * 60)
        logger.info("\ud83c\udf89 OPTIMIZATION COMPLETE")
        logger.info("=" * 60)
        logger.info(f"   Original score:  {original_score:.2%}")
        logger.info(f"   Optimized score: {optimized_score:.2%}")
        logger.info(f"   Improvement:     {improvement:+.2%}")
        if usage_stats:
            logger.info(f"   API calls made:  {usage_stats.api_calls}")
            logger.info(f"   Total tokens:    {usage_stats.total_tokens:,}")
        logger.info("=" * 60)
        
        return OptimizationResult(
            original_prompt=self.prompt_template,
            optimized_prompt=optimized_prompt,
            original_score=original_score,
            optimized_score=optimized_score,
            improvement=optimized_score - original_score,
            iterations=max_iterations,
            feedback=all_feedback,
            usage_stats=usage_stats
        )
    
    def _extract_prompt(self) -> str:
        """Extract the current prompt/instructions from the module."""
        # Try to get the prompt from the predictor
        if hasattr(self.module, 'predictor'):
            predictor = self.module.predictor
            if hasattr(predictor, 'demos') and predictor.demos:
                # Format demos as examples
                demo_str = "\n".join([
                    f"Example: {d}" for d in predictor.demos[:3]
                ])
                return f"{self.prompt_template}\n\nLearned examples:\n{demo_str}"
        
        return self.prompt_template
    
    def run(self, **kwargs) -> str:
        """
        Run the optimized prompt with given inputs.
        
        Args:
            **kwargs: Input variables for the prompt
            
        Returns:
            The generated output
        """
        result = self.module(**kwargs)
        return getattr(result, self.output_variable, str(result))


class IterativePromptRefiner:
    """
    A more advanced optimizer that iteratively refines prompts using LLM feedback.
    
    This uses a meta-learning approach where an LLM analyzes failures and
    suggests prompt improvements directly.
    """
    
    # Parameter limits
    MAX_ITERATIONS_LIMIT = 10
    
    def __init__(self, max_iterations: int = 3):
        """
        Initialize the iterative prompt refiner.
        
        Args:
            max_iterations: Maximum refinement iterations (1-10, default: 3)
            
        Raises:
            ValueError: If max_iterations is out of valid range
        """
        logger.info(f"\ud83d\udee0\ufe0f  Initializing IterativePromptRefiner (max_iterations={max_iterations})")
        if max_iterations < 1 or max_iterations > self.MAX_ITERATIONS_LIMIT:
            raise ValueError(f"max_iterations must be between 1 and {self.MAX_ITERATIONS_LIMIT}, got {max_iterations}")
        
        self.max_iterations = max_iterations
        self.refiner = dspy.ChainOfThought(
            "current_prompt, failures, metric_scores -> improved_prompt: str, changes_made: str"
        )
        self.analyzer = dspy.ChainOfThought(
            "prompt, input_output_pairs, scores -> flaws: str, suggestions: str"
        )
        logger.info("\u2705 IterativePromptRefiner initialized")
    
    def analyze_failures(
        self,
        prompt: str,
        examples: list[dict],
        scores: list[float]
    ) -> tuple[str, str]:
        """
        Analyze why the prompt is failing on certain examples.
        
        Args:
            prompt: Current prompt template
            examples: List of input/output dictionaries
            scores: Corresponding scores for each example
            
        Returns:
            Tuple of (identified_flaws, improvement_suggestions)
        """
        logger.debug("Analyzing failures...")
        # Focus on low-scoring examples
        low_score_examples = [
            (ex, score) for ex, score in zip(examples, scores)
            if score < 0.7
        ][:3]  # Limit to 3 for efficiency
        
        if not low_score_examples:
            logger.debug("No significant flaws found")
            return "No significant flaws found.", "Prompt is performing well."
        
        logger.debug(f"Found {len(low_score_examples)} low-scoring examples to analyze")
        
        # Apply rate limiting
        rate_limiter = get_rate_limiter()
        rate_limiter.wait()
        
        pairs_str = "\n".join([
            f"Input: {ex}, Score: {score:.2f}" 
            for ex, score in low_score_examples
        ])
        
        result = self.analyzer(
            prompt=prompt,
            input_output_pairs=pairs_str,
            scores=f"Average: {sum(scores)/len(scores):.2f}, Min: {min(scores):.2f}"
        )
        
        return result.flaws, result.suggestions
    
    def refine(
        self,
        prompt: str,
        failures: str,
        scores: str
    ) -> tuple[str, str]:
        """
        Generate an improved version of the prompt.
        
        Args:
            prompt: Current prompt
            failures: Description of failures/flaws
            scores: Score information
            
        Returns:
            Tuple of (improved_prompt, changes_description)
        """
        logger.debug("Generating improved prompt...")
        
        # Apply rate limiting
        rate_limiter = get_rate_limiter()
        rate_limiter.wait()
        
        result = self.refiner(
            current_prompt=prompt,
            failures=failures,
            metric_scores=scores
        )
        
        return result.improved_prompt, result.changes_made
    
    # Default performance threshold (0.0-1.0)
    DEFAULT_PERFORMANCE_THRESHOLD = 0.8
    
    def optimize(
        self,
        initial_prompt: str,
        evaluator_fn,  # Function that takes prompt and returns (score, examples, scores_list)
        performance_threshold: float = None,
        skip_if_above_threshold: bool = True
    ) -> OptimizationResult:
        """
        Iteratively optimize a prompt using analysis and refinement.
        
        Args:
            initial_prompt: The starting prompt template
            evaluator_fn: Function to evaluate a prompt, returns (avg_score, examples, individual_scores)
            performance_threshold: Score threshold (0.0-1.0) above which optimization is skipped.
                If None, uses DEFAULT_PERFORMANCE_THRESHOLD (0.8).
            skip_if_above_threshold: If True, skip optimization when initial score >= threshold.
                If False, always run optimization regardless of initial score. (default: True)
            
        Returns:
            OptimizationResult
        """
        # Set default threshold if not provided
        if performance_threshold is None:
            performance_threshold = self.DEFAULT_PERFORMANCE_THRESHOLD
        
        # Validate threshold
        if not 0.0 <= performance_threshold <= 1.0:
            raise ValueError(f"performance_threshold must be between 0.0 and 1.0, got {performance_threshold}")
        
        logger.info("=" * 60)
        logger.info("\ud83d\ude80 STARTING ITERATIVE PROMPT REFINEMENT")
        logger.info("=" * 60)
        logger.info(f"   Max iterations: {self.max_iterations}")
        logger.info(f"   Performance threshold: {performance_threshold:.0%}")
        logger.info(f"   Skip if above threshold: {skip_if_above_threshold}")
        
        current_prompt = initial_prompt
        all_feedback = []
        
        # Initial evaluation
        logger.info("\n\ud83d\udcdd Initial evaluation...")
        original_score, examples, scores = evaluator_fn(current_prompt)
        best_score = original_score
        best_prompt = current_prompt
        logger.info(f"\u2705 Initial score: {original_score:.2%}")
        
        # Check if optimization is needed based on threshold
        if skip_if_above_threshold and original_score >= performance_threshold:
            logger.info("\n" + "=" * 60)
            logger.info("\u2728 PROMPT ALREADY PERFORMING WELL - SKIPPING OPTIMIZATION")
            logger.info("=" * 60)
            logger.info(f"   Initial score ({original_score:.2%}) >= threshold ({performance_threshold:.0%})")
            logger.info("   No optimization needed!")
            logger.info("=" * 60)
            
            # Capture usage stats
            usage_stats = None
            if UsageTracker.is_tracking():
                usage_stats = UsageTracker.get_stats()
                usage_stats = UsageStats(
                    api_calls=usage_stats.api_calls,
                    input_tokens=usage_stats.input_tokens,
                    output_tokens=usage_stats.output_tokens,
                    total_tokens=usage_stats.total_tokens,
                    cost_per_1k_input_tokens=usage_stats.cost_per_1k_input_tokens,
                    cost_per_1k_output_tokens=usage_stats.cost_per_1k_output_tokens
                )
            
            return OptimizationResult(
                original_prompt=initial_prompt,
                optimized_prompt=initial_prompt,  # No change
                original_score=original_score,
                optimized_score=original_score,  # Same as original
                improvement=0.0,
                iterations=0,  # No iterations performed
                feedback=all_feedback + ["Optimization skipped: initial score above threshold"],
                usage_stats=usage_stats
            )
        
        # Log that optimization will proceed
        if original_score < performance_threshold:
            logger.info(f"\n\u26a0\ufe0f  Prompt underperforming (score {original_score:.2%} < threshold {performance_threshold:.0%})")
            logger.info("   Proceeding with iterative refinement...")
        
        for i in range(self.max_iterations):
            logger.info(f"\n\ud83d\udd04 Iteration {i+1}/{self.max_iterations}")
            # Analyze failures
            # Analyze failures
            logger.info("   \ud83d\udd0d Analyzing failures...")
            flaws, suggestions = self.analyze_failures(current_prompt, examples, scores)
            all_feedback.append(f"Iteration {i+1} - Flaws: {flaws}")
            all_feedback.append(f"Iteration {i+1} - Suggestions: {suggestions}")
            logger.debug(f"   Flaws: {flaws[:100]}...")
            
            # Refine prompt
            logger.info("   \u2699\ufe0f  Refining prompt...")
            improved_prompt, changes = self.refine(
                current_prompt,
                flaws,
                f"Current score: {best_score:.2f}"
            )
            all_feedback.append(f"Iteration {i+1} - Changes: {changes}")
            logger.debug(f"   Changes: {changes[:100]}...")
            
            # Evaluate improved prompt
            logger.info("   \ud83d\udcdd Evaluating improved prompt...")
            new_score, examples, scores = evaluator_fn(improved_prompt)
            logger.info(f"   \ud83d\udcca New score: {new_score:.2%}")
            
            if new_score > best_score:
                improvement = new_score - best_score
                logger.info(f"   \u2705 Improvement! +{improvement:.2%}")
                best_score = new_score
                best_prompt = improved_prompt
                current_prompt = improved_prompt
            else:
                logger.info(f"   \u26a0\ufe0f  No improvement, stopping early")
                all_feedback.append(f"Iteration {i+1} - No improvement, keeping previous version")
                break
        
        # Capture usage stats
        usage_stats = None
        if UsageTracker.is_tracking():
            usage_stats = UsageTracker.get_stats()
            usage_stats = UsageStats(
                api_calls=usage_stats.api_calls,
                input_tokens=usage_stats.input_tokens,
                output_tokens=usage_stats.output_tokens,
                total_tokens=usage_stats.total_tokens,
                cost_per_1k_input_tokens=usage_stats.cost_per_1k_input_tokens,
                cost_per_1k_output_tokens=usage_stats.cost_per_1k_output_tokens
            )
        
        # Log summary
        improvement = best_score - original_score
        logger.info("\n" + "=" * 60)
        logger.info("\ud83c\udf89 ITERATIVE REFINEMENT COMPLETE")
        logger.info("=" * 60)
        logger.info(f"   Original score:  {original_score:.2%}")
        logger.info(f"   Final score:     {best_score:.2%}")
        logger.info(f"   Improvement:     {improvement:+.2%}")
        if usage_stats:
            logger.info(f"   API calls made:  {usage_stats.api_calls}")
            logger.info(f"   Total tokens:    {usage_stats.total_tokens:,}")
        logger.info("=" * 60)
        
        return OptimizationResult(
            original_prompt=initial_prompt,
            optimized_prompt=best_prompt,
            original_score=original_score,
            optimized_score=best_score,
            improvement=best_score - original_score,
            iterations=self.max_iterations,
            feedback=all_feedback,
            usage_stats=usage_stats
        )
