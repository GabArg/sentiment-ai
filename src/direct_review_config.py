"""Independent opt-in configuration for direct multilingual sentiment review."""
from __future__ import annotations
from dataclasses import dataclass
import os
from typing import Any,Mapping

def _value(name,secrets,environ):
 if secrets is not None:
  try: value=secrets.get(name)
  except Exception: value=None
  if value is not None:return value
 return environ.get(name)
def _boolean(value):
 if value is None:return False
 if isinstance(value,bool):return value
 normalized=str(value).strip().casefold()
 if normalized in {'1','true','yes','on'}:return True
 if normalized in {'0','false','no','off',''}:return False
 raise ValueError('ENABLE_DIRECT_MULTILINGUAL_REVIEW must be true or false.')
@dataclass(frozen=True)
class DirectReviewConfig:
 enabled:bool=False
def load_direct_review_config(secrets:Mapping[str,Any]|None=None,environ:Mapping[str,str]|None=None)->DirectReviewConfig:
 return DirectReviewConfig(_boolean(_value('ENABLE_DIRECT_MULTILINGUAL_REVIEW',secrets,os.environ if environ is None else environ)))
