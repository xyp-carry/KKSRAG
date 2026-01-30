import pickle
import pandas as pd

async def get_file(filename=None):
    with open(f'./Tool/{filename}', 'rb') as f:
        data = pickle.load(f)
    # print(data)
    Output = []
    for index, item  in enumerate(data):
        Output.append({"index":index, "text":str(item).replace(r"\n","")})
    res = pd.DataFrame(Output[:10])
    return res 


# print(get_file('insert_data.pkl').to_dict(orient="records"))