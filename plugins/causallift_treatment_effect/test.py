import pickle

with open('./data/plugins/models/0jwqwilt.pkl', 'rb') as f:
    data = pickle.load(f)

from causallift import CausalLift
from pandas import DataFrame


prefix = ['A_SUBMITTED', 'A_PARTLYSUBMITTED', 'W_Valideren aanvraag']
features = [data["mapping"][x] for x in prefix]
length = 3
test_df = DataFrame([features], columns=[f"Activity_{i}" for i in range(length)])
training_df = data["training_dfs"].get(length)

cl = CausalLift(train_df=training_df, test_df=test_df, enable_ipw=True)
train_df, test_df = cl.estimate_cate_by_2_models()
