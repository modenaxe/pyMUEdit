# Write .pkl files in output decomposition to .txt files
import pickle
import os

output_dir = os.path.abspath("../data/io/output_decomposition")

for file in os.listdir(output_dir):
    if file.endswith(".pkl"):
        with open(os.path.join(output_dir, file), 'rb') as f:
            data = pickle.load(f)
            # write the data to a new .txt file with the same name - remove .pkl
            file = file[:-4]

            with open(os.path.join(output_dir, f"{file}.txt"), 'w') as f:
                f.write(str(data))
