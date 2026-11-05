"""Re-validate existing anonymized collector outputs; do not rewrite raw source prose."""
from real_dataset.validation import write_quality
if __name__=='__main__':
 result=write_quality();print('PII remaining:',result['recognized_pii_remaining']);raise SystemExit(1 if result['recognized_pii_remaining'] else 0)
