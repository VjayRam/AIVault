import pandas as pd
import numpy as np
from metrics.eval_metrics import EvalMetric
from llms.llm_client import LLMClient

class Evaluator:
    def __init__(self, llm_client: LLMClient, eval_metrics: list[EvalMetric]):
        self.llm_client = llm_client
        self.eval_metrics = eval_metrics
        print("Evaluator intialized with metrics:", [m.metric_name for m in eval_metrics])

    def evaluate(self, dataset: pd.DataFrame):
        summaries = {}
        summaries['num_samples'] = len(dataset)
        print("Number of API calls estimated: ", len(dataset) * len(self.eval_metrics))
        
        for metric in self.eval_metrics:
            ratings = []
            explanations = []
            for _, row in dataset.iterrows():
                # Extract variables dynamically from metric template
                template_vars = {}
                for key in metric.metric_prompt_template.split('{'):
                    if '}' in key:
                        var_name = key.split('}')[0]
                        # print(var_name)
                        template_vars[var_name] = row.get(var_name)
                        # print(template_vars)
                prompt = metric.metric_prompt_template.format(**template_vars)
                response = self.llm_client.generate(prompt=prompt)
                if response is not None:
                    # Handle both parsed objects and JSON strings
                    if isinstance(response, self.llm_client.LLMResponse):
                        response_parsed = response
                    else:
                        response_parsed = self.llm_client.LLMResponse.model_validate_json(response)
                    ratings.append(response_parsed.rating)
                    explanations.append(response_parsed.explanation)
                else:
                    ratings.append(-1)
                    explanations.append("N/A")
            dataset[f"{metric.metric_name}_rating"] = ratings
            dataset[f"{metric.metric_name}_explanation"] = explanations
            summaries[metric.metric_name] = {
                "mean": np.mean(ratings),  
                "std": np.std(ratings) 
            }
        return dataset, summaries
        
        