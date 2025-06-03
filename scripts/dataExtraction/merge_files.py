import pandas as pd

provision = ""
deprovision = ""

df_p = pd.read_csv(provision)
df_d = pd.read_csv(deprovision)

df_p["deprovision_start"] = df_d["deprovision_start"]
df_p["deprovision_end"] = df_d["deprovision_end"]

df_p.to_csv("test.csv", index=False)