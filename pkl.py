import pickle

# Assume you have trained YOLO models
model_polythene = "biogas.pt"  # Replace with actual model
model_biogas = "poly_non_poly.pt"  # Replace with actual model

models = {
    "polythene": model_polythene,
    "biogas": model_biogas
}

with open("Models_pickle.pkl", "wb") as f:
    pickle.dump(models, f)

print("✅ Models_pickle.pkl has been successfully recreated!")
