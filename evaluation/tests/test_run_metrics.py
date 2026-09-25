"""Offline tests: execute pipeline functions without importing model/infra SDKs."""
import ast
from contextlib import contextmanager
import importlib.util
import logging
import math
from pathlib import Path
import re
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]


def definitions(path, names, namespace):
    tree = ast.parse(path.read_text())
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef, ast.Assign))
             and (getattr(node, 'name', None) in names or
                  any(isinstance(t, ast.Name) and t.id in names for t in getattr(node, 'targets', [])))]
    exec(compile(ast.Module(body=nodes, type_ignores=[]), str(path), 'exec'), namespace)
    return namespace


class MetricsTests(unittest.TestCase):
    def setUp(self):
        carbon = ModuleType('codecarbon')
        carbon.OfflineEmissionsTracker = SimpleNamespace
        config = SimpleNamespace(MEASURE_VRAM=False)
        spec = importlib.util.spec_from_file_location('sample_metrics', ROOT / 'run_metrics.py')
        self.metrics = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {'codecarbon': carbon, 'true_mas': SimpleNamespace(config=config)}):
            spec.loader.exec_module(self.metrics)
        @contextmanager
        def resources():
            yield
            self.metrics.stats.update(energy_wh=0.2, estimated_co2e_g=0.03)
        self.metrics.monitor_emissions = resources
        self.aggregate = definitions(ROOT / 'misc/ablation/ablation-iac-eval-pipeline.py',
                                     {'RESOURCE_METRICS', 'aggregate_resource_metrics'},
                                     {'pd': pd, 're': re, 'math': math})['aggregate_resource_metrics']

    def frame(self):
        df = pd.DataFrame({'Prompt': ['a', 'b', None]})
        for sample in range(2):
            df[f'LLM Correct? #{sample}'] = ['Success', 'Failure', None]
            for metric in self.metrics.METRICS:
                df[f'{metric} #{sample}'] = [sample + 1, sample + 2, None]
        return df

    def test_aggregation_multiple_samples_and_datasets(self):
        first = self.frame()
        second = self.frame().iloc[:1].copy()
        self.assertEqual(self.aggregate(first)['attempts'], 8)
        self.assertEqual(self.aggregate(first)['peak_vram_mib'], 3)
        self.assertEqual(self.aggregate(second)['attempts'], 3)

    def test_missing_independently_and_zero(self):
        for missing in [None, float('nan'), float('inf'), 'bad', -1]:
            df = self.frame()
            df['attempts #0'] = 0
            df['attempts #1'] = 0
            df['peak_vram_mib #1'] = df['peak_vram_mib #1'].astype(object)
            df.at[0, 'peak_vram_mib #1'] = missing
            result = self.aggregate(df)
            self.assertIsNone(result['peak_vram_mib'])
            self.assertEqual(result['attempts'], 0)
        df = self.frame().drop(columns=['energy_wh #1'])
        self.assertIsNone(self.aggregate(df)['energy_wh'])
        old = df[[c for c in df if c.startswith(('Prompt', 'LLM'))]]
        self.assertTrue(all(v is None for v in self.aggregate(old).values()))

    def test_timeout_usage_unknown_but_counters_known(self):
        self.metrics.attempt()
        self.metrics.failure(TimeoutError())
        self.metrics.attempt(retry=True)
        self.metrics.response(5, 2, 'stop')
        self.assertIsNone(self.metrics.stats['prompt_tokens'])
        self.assertEqual(self.metrics.stats['timeouts'], 1)
        self.assertEqual(self.metrics.stats['attempts'], 2)
        self.assertEqual(self.metrics.stats['retries'], 1)

    def test_independent_usage_and_output_limit(self):
        self.metrics.attempt()
        self.metrics.response(None, 3, 'length')
        self.metrics.response(4, 2, 'stop')
        self.assertIsNone(self.metrics.stats['prompt_tokens'])
        self.assertEqual(self.metrics.stats['completion_tokens'], 5)
        self.assertEqual(self.metrics.stats['output_limit_hits'], 1)

    def test_resource_tracker_conversion_and_failure(self):
        tracker = SimpleNamespace(start=lambda: None, stop=lambda: 0.001,
                                  final_emissions_data=SimpleNamespace(energy_consumed=0.002))
        self.metrics.config.CODECARBON_COUNTRY_ISO_CODE = 'FIN'
        self.metrics.config.GPU_METRICS_DEVICE = '0'
        # Reload the original context manager, retaining fake hardware dependencies.
        ns = definitions(ROOT / 'run_metrics.py', {'monitor_emissions'}, {
            'contextmanager': contextmanager, 'config': self.metrics.config,
            'logging': logging, 'stats': self.metrics.stats,
            'OfflineEmissionsTracker': lambda **kwargs: tracker,
        })
        with ns['monitor_emissions']():
            pass
        self.assertEqual(self.metrics.stats['energy_wh'], 2)
        self.assertEqual(self.metrics.stats['estimated_co2e_g'], 1)
        self.metrics.reset()
        tracker.stop = lambda: None
        with self.assertLogs(level='WARNING'), ns['monitor_emissions']():
            pass
        self.assertIsNone(self.metrics.stats['energy_wh'])

    def test_interrupted_sample_does_not_checkpoint(self):
        import tempfile
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / 'detailed.csv'
            df = pd.DataFrame({'Prompt': ['task']})
            df.to_csv(checkpoint, index=False)
            before = checkpoint.read_bytes()
            with self.assertRaises(KeyboardInterrupt):
                with self.metrics.measure_sample(df, 0, 0, checkpoint):
                    self.metrics.attempt()
                    raise KeyboardInterrupt()
            self.assertEqual(checkpoint.read_bytes(), before)

    def test_checkpoint_resume_shared_retrieval(self):
        import tempfile
        calls = []
        def enhance(prompt, method, retriever):
            calls.append('retrieval')
            self.metrics.attempt()
            self.metrics.response(10, 2, 'stop')
            return 'enhanced'
        def generate(*args):
            calls.append('generation')
            self.metrics.attempt()
            self.metrics.response(3, 1, 'stop')
            return 'code'
        result = dict(terraform_plan_success=True, opa_evaluation_result='Success',
                      terraform_plan_error='', opa_evaluation_error='', notes='')
        ns = definitions(ROOT / 'eval.py', {'model_evaluation', 'determine_eval_samples'}, {
            'pd': pd, 'math': math, 'logging': logging, 'logger': logging.getLogger('test'),
            'NUM_SAMPLES_PER_TASK': 1, 'run_metrics': self.metrics,
            'prompt_enhancements': enhance, 'models': SimpleNamespace(local_model=generate),
            'BASE_URL': '', 'API_KEY': '', 'DELIMITERS': [],
            'separate_answer_and_code': lambda *args: ('', 'code'),
            'eval_pipeline': lambda *args: result,
        })
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / 'detailed.csv'
            df = pd.DataFrame({'Prompt': ['task'], 'Rego intent': ['policy']})
            def run(frame, existing=0):
                ns['model_evaluation'](frame.iloc[0], 'system', frame, 0, 'local', 'RAG',
                                       existing, None, 'uuid', None, checkpoint=checkpoint)
            run(df)
            saved = pd.read_csv(checkpoint)
            self.assertEqual(saved.at[0, 'prompt_tokens #0'], 13)
            self.assertEqual(ns['determine_eval_samples'](checkpoint)[0], 1)
            ns['NUM_SAMPLES_PER_TASK'] = 3
            run(saved)
            resumed = pd.read_csv(checkpoint)
            self.assertEqual(resumed.at[0, 'prompt_tokens #0'], 13)
            self.assertEqual(resumed.at[0, 'prompt_tokens #1'], 13)
            self.assertEqual(resumed.at[0, 'prompt_tokens #2'], 3)
            self.assertNotIn('Enhanced prompt', resumed.columns)
            self.assertEqual(calls, ['retrieval', 'generation', 'retrieval', 'generation', 'generation'])
            run(resumed)
            self.assertEqual(len(calls), 5)
            self.assertEqual(ns['determine_eval_samples'](checkpoint)[0], 3)
            self.assertEqual(list(Path(directory).iterdir()), [checkpoint])


if __name__ == '__main__':
    unittest.main()
