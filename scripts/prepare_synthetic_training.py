import json
from synthetic_data.training_export import export
if __name__=='__main__':
    result=export()
    print(json.dumps({k:result[k] for k in ('status','source_threads','source_comments','training_rows','excluded_uncertain','labels','training_performed')},ensure_ascii=False))
