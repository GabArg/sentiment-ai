import itertools
from pathlib import Path
from src.direct_review_config import load_direct_review_config
from src.hybrid_config import load_hybrid_config
from src.multilingual_config import load_multilingual_config

def test_all_flag_combinations_remain_independent_and_default_safe():
 for hybrid,multilingual,direct in itertools.product((False,True),repeat=3):
  environ={'ENABLE_HYBRID_SENTIMENT':str(hybrid),'ENABLE_MULTILINGUAL_SENTIMENT':str(multilingual),'ENABLE_DIRECT_MULTILINGUAL_REVIEW':str(direct)}
  assert load_hybrid_config({},environ).enabled is hybrid
  assert load_multilingual_config({},environ).enabled is multilingual
  assert load_direct_review_config({},environ).enabled is direct
 assert not load_hybrid_config({},{}).enabled
 assert not load_multilingual_config({},{}).enabled
 assert not load_direct_review_config({},{}).enabled

def test_direct_states_have_human_ui_labels_without_changing_csv_values():
 source=(Path(__file__).parents[1]/'app.py').read_text(encoding='utf-8')
 assert '"direct_multilingual_review": "Revisión multilingüe directa"' in source
 assert '"direct_review_failed": "Fallback local"' in source
