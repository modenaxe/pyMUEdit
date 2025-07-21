import scipy.io as sio
import numpy as np
from pprint import pprint

matfile = "D:\PyCharm\Programs\9900\capstone-project-25t2-9900-t09a-almond\data\matlab_output_trial1_40MVC.otb+_decomp_edited.mat"
data = sio.loadmat(matfile)

print("===== .mat 文件顶层结构 =====")
for key in data:
    if not key.startswith("__"):
        print(f"{key}: type={type(data[key])}, shape={data[key].shape if isinstance(data[key], np.ndarray) else ''}")

print("\n===== 深入查看每个主要字段 =====")
for key in data:
    if key != "edition":
        continue
    if not key.startswith("__"):
        print(f"\n==== {key} ====")
        value = data[key]
        # 如果是结构化数组（比如 edition/signal/parameters）
        if isinstance(value, np.ndarray) and value.dtype.names:
            for name in value.dtype.names:
                print(f"  {name}: type={type(value[name][0,0])}, shape={value[name][0,0].shape if hasattr(value[name][0,0], 'shape') else ''}")
                # 打印部分内容
                print(f"    内容样例: {value[name][0,0]}")
        else:
            pprint(value)
