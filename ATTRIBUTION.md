# Attribution and provenance

## Original team project

This repository is a recovered and modified version of software originally developed collaboratively by the **H12-25-L-Equipo-72** team:

- Original repository: https://github.com/S4mma3l/H12-25-L-Equipo-72
- Source branch: [`feature/mejora-dataset-v6`](https://github.com/S4mma3l/H12-25-L-Equipo-72/tree/feature/mejora-dataset-v6)
- Source commit inspected: `a3a4014fb0d03b3a1ff205d0784d710344967b75` (2025-12-25)
- Original license: GNU General Public License v3.0

The original code, training pipeline, datasets, trained classifier, TF-IDF vectorizer, FastAPI service and Streamlit frontend were team work. They are not represented here as having been created exclusively by the maintainer of this portfolio repository.

## Portfolio recovery and modifications

This version was recovered and prepared for portfolio presentation by **GabArg**. The recovery work includes:

- replacing the two-service `Streamlit → FastAPI` runtime with direct inference in Streamlit;
- removing the `localhost` HTTP dependency and all runtime downloads;
- packaging the original `sentiment_model.joblib` and `tfidf_vectorizer.joblib` locally;
- adding one-time artifact loading with Streamlit resource caching;
- correcting input validation, class/probability association and user-facing error handling;
- redesigning the interface for a restrained, responsive portfolio presentation;
- reducing runtime dependencies to Streamlit, scikit-learn and joblib;
- documenting artifact compatibility, architecture, limitations, deployment and provenance.

The trained artifacts remain unmodified copies of those stored in the source branch. The model was not retrained for this recovery.

## License notice

This modified version remains licensed under the **GNU General Public License v3.0**. The complete license text is included in `LICENSE`. Redistribution or further modification must comply with GPL-3.0 and preserve the applicable notices of origin and modification.
