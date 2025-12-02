import platform

# Check the operating system to use the appropriate embedding library.
if platform.system() == "Darwin":
    import mlx.core as mx
    from mlx_embeddings.utils import load


    # MODEL_NAME = "mlx-community/all-MiniLM-L6-v2-4bit"
    MODEL_NAME = "mlx-community/Qwen3-Embedding-0.6B-4bit-DWQ"
    model, tokenizer = load(MODEL_NAME)

    def embed_text(text: str):
        """Generate a normalized embedding vector for a given text."""
        try:
            # Encode text
            inputs = tokenizer.encode(text, return_tensors="mlx")
            
            # Forward pass to get embeddings
            outputs = model(inputs)
            emb = outputs.text_embeds[0].tolist()
            return emb

        except Exception as e:
            print("Embedding error:", e)
            return []

else:
    from sentence_transformers import SentenceTransformer

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    model = SentenceTransformer(MODEL_NAME)

    def embed_text(text: str):
        """Generate a normalized embedding vector for a given text."""
        try:
            # Generate embedding and normalize.
            emb = model.encode(text, normalize_embeddings=True)
            return emb.tolist()

        except Exception as e:
            print("Embedding error:", e)
            return []