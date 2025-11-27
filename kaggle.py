import streamlit as st
import requests
import os
import zipfile
import pandas as pd

st.title("📦 Kaggle Dataset Downloader")

# --- Config ---
base_extract_path = r"C:\Users\GenAIHYDSYPUSR117\Desktop\BTTEAM\data"
file_path = r"C:\Users\GenAIHYDSYPUSR117\Desktop\BTTEAM\dataset.zip"
headers = {"Authorization": "Bearer KGAT_ce8c9aa9a0a38f13958d5a7afa243fe1"}  # <-- Replace with your Kaggle API token

# --- Tabs ---
tab1, tab2 = st.tabs(["🔍 Search & Download", "📂 CSV Preview"])

# --- Tab 1: Search & Download ---
with tab1:
    search_key = st.text_input("Enter keyword to search Kaggle datasets:")

    # Pagination controls
    page_size = st.selectbox("Results per page:", [5, 10, 20, 50], index=0)
    page_number = st.number_input("Page number:", min_value=1, value=1)

    if search_key:
        try:
            url = "https://www.kaggle.com/api/v1/datasets/list"
            params = {
                "page": page_number,
                "pageSize": page_size,
                "search": search_key,
                "fileType": "csv",
                "sortBy": "hottest"
            }

            response = requests.get(url, headers=headers, verify=False, params=params)
            response.raise_for_status()
            data = response.json()

            st.subheader(f"Showing {page_size} datasets (Page {page_number}):")
            for i, ds in enumerate(data[:page_size]):
                title = ds.get("title")
                ref = ds.get("ref")
                url = ds.get("url")

                st.write(f"**{i+1}. {title}**")
                st.write(f"Ref: {ref}")
                st.write(f"URL: {url}")
                st.write(f"Creator: {ds.get('creatorName')}")
                st.write(f"Size: {ds.get('totalBytes')/1024:.2f} KB")
                st.write(f"Last Updated: {ds.get('lastUpdated')}")

                if st.button(f"⬇️ Download {title}", key=f"download_{i}_page{page_number}"):
                    try:
                        download_url = f"https://www.kaggle.com/api/v1/datasets/download/{ref}"
                        resp = requests.get(download_url, headers=headers, verify=False, stream=True)
                        resp.raise_for_status()

                        # Save zip file
                        with open(file_path, "wb") as f:
                            for chunk in resp.iter_content(chunk_size=8192):
                                f.write(chunk)

                        st.success(f"✅ Downloaded {title} to: {file_path}")

                        # Create unique folder for dataset
                        dataset_folder = os.path.join(base_extract_path, ref.replace("/", "_"))
                        os.makedirs(dataset_folder, exist_ok=True)

                        # Unzip into dataset-specific folder
                        with zipfile.ZipFile(file_path, 'r') as zip_ref:
                            zip_ref.extractall(dataset_folder)

                        st.success(f"📂 Files extracted to: {dataset_folder}")

                        # Collect CSV files
                        csv_files = [os.path.join(dataset_folder, f) for f in os.listdir(dataset_folder) if f.endswith(".csv")]

                        if csv_files:
                            st.session_state["datasets"] = st.session_state.get("datasets", {})
                            st.session_state["datasets"][ref] = {
                                "title": title,
                                "folder": dataset_folder,
                                "csv_files": csv_files
                            }
                            st.success(f"✅ {len(csv_files)} CSV files loaded for {title}. Switch to the 'CSV Preview' tab to explore.")
                        else:
                            st.warning("No CSV files found in the dataset.")

                    except Exception as e:
                        st.error(f"❌ Error downloading {title}: {e}")

                st.write("---")

        except Exception as e:
            st.error(f"❌ Error while searching: {e}")

# --- Tab 2: CSV Preview ---
with tab2:
    # ✅ Auto-rescan folders if datasets missing or cleared
    if "datasets" not in st.session_state or not st.session_state["datasets"]:
        if os.path.exists(base_extract_path):
            datasets = {}
            for folder in os.listdir(base_extract_path):
                dataset_folder = os.path.join(base_extract_path, folder)
                if os.path.isdir(dataset_folder):
                    csv_files = [os.path.join(dataset_folder, f) for f in os.listdir(dataset_folder) if f.endswith(".csv")]
                    if csv_files:
                        datasets[folder] = {
                            "title": folder.replace("_", " "),  # fallback title
                            "folder": dataset_folder,
                            "csv_files": csv_files
                        }
            if datasets:
                st.session_state["datasets"] = datasets

    if "datasets" in st.session_state and st.session_state["datasets"]:
        dataset_options = {
            f"{v['title']} 📂 ({os.path.basename(v['folder'])})": k
            for k, v in st.session_state["datasets"].items()
        }

        selected_dataset_label = st.selectbox("Select a dataset to explore:", list(dataset_options.keys()))
        if selected_dataset_label:
            ref = dataset_options[selected_dataset_label]
            dataset_info = st.session_state["datasets"][ref]

            selected_file = st.selectbox(
                f"Select a CSV file from {dataset_info['title']}:",
                dataset_info["csv_files"],
                key=f"select_{ref}"
            )

            if selected_file:
                try:
                    df = pd.read_csv(selected_file)

                    # ✅ Row preview slider
                    preview_rows = st.slider(
                        "Number of rows to preview:",
                        min_value=5,
                        max_value=100,
                        value=5,
                        step=5
                    )

                    st.write(f"**Preview of {os.path.basename(selected_file)} (showing {preview_rows} rows):**")
                    st.dataframe(df.head(preview_rows))

                    # ✅ Download button
                    with open(selected_file, "rb") as f:
                        st.download_button(
                            label=f"💾 Download {os.path.basename(selected_file)}",
                            data=f,
                            file_name=os.path.basename(selected_file),
                            mime="text/csv",
                            key=f"download_csv_{ref}"
                        )

                except Exception as e:
                    st.error(f"Could not preview {selected_file}: {e}")

        # ✅ Clear All button
        if st.button("🗑️ Clear all datasets"):
            st.session_state.pop("datasets", None)
            st.success("All datasets cleared from memory. Rescan will reload any folders on next run.")

    else:
        st.info("No datasets downloaded yet. Go to the 'Search & Download' tab first.")
