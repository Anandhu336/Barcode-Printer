{
 "cells": [
  {
   "cell_type": "code",
   "execution_count": null,
   "id": "136c0480-214b-431b-ae4b-8012591a37a6",
   "metadata": {},
   "outputs": [],
   "source": [
    "# stock_update.py\n",
    "import streamlit as st\n",
    "import pandas as pd\n",
    "import os\n",
    "from utils.file_handler import read_po_file\n",
    "\n",
    "DATA_PATH = \"data/warehouse_stock.csv\"\n",
    "os.makedirs(\"data\", exist_ok=True)\n",
    "\n",
    "def run():\n",
    "    st.title(\"🚀 Stock Update & Sync\")\n",
    "    st.caption(\"Upload new PO sheets or manually adjust stock levels in real-time.\")\n",
    "\n",
    "    uploaded_file = st.file_uploader(\"📤 Upload PO File (CSV, Excel, PDF)\", type=[\"csv\", \"xlsx\", \"pdf\"])\n",
    "\n",
    "    if uploaded_file:\n",
    "        df, _ = read_po_file(uploaded_file)\n",
    "        if not df.empty:\n",
    "            st.success(f\"✅ Loaded {len(df)} items from PO sheet.\")\n",
    "            st.dataframe(df.head(10))\n",
    "            if st.button(\"📥 Sync to Main Database\"):\n",
    "                sync_stock(df)\n",
    "                st.success(\"Database successfully updated.\")\n",
    "        else:\n",
    "            st.warning(\"⚠️ Could not extract data. Please check file format.\")\n",
    "\n",
    "    st.markdown(\"### ✏️ Manual Adjustments\")\n",
    "    if os.path.exists(DATA_PATH):\n",
    "        stock_df = pd.read_csv(DATA_PATH)\n",
    "        edited_df = st.data_editor(stock_df, num_rows=\"dynamic\", use_container_width=True)\n",
    "        if st.button(\"💾 Save Manual Changes\"):\n",
    "            edited_df.to_csv(DATA_PATH, index=False)\n",
    "            st.success(\"✅ Stock data saved successfully!\")\n",
    "    else:\n",
    "        st.warning(\"No stock data found to edit. Please upload one first.\")\n",
    "\n",
    "def sync_stock(new_data):\n",
    "    \"\"\"Merge new PO data with existing warehouse stock.\"\"\"\n",
    "    if os.path.exists(DATA_PATH):\n",
    "        current_df = pd.read_csv(DATA_PATH)\n",
    "        merged = pd.concat([current_df, new_data], ignore_index=True)\n",
    "        merged.drop_duplicates(subset=[\"Sku\", \"Location\"], keep=\"last\", inplace=True)\n",
    "    else:\n",
    "        merged = new_data\n",
    "    merged.to_csv(DATA_PATH, index=False)"
   ]
  }
 ],
 "metadata": {
  "kernelspec": {
   "display_name": "barcode_demo",
   "language": "python",
   "name": "barcode_demo"
  },
  "language_info": {
   "codemirror_mode": {
    "name": "ipython",
    "version": 3
   },
   "file_extension": ".py",
   "mimetype": "text/x-python",
   "name": "python",
   "nbconvert_exporter": "python",
   "pygments_lexer": "ipython3",
   "version": "3.12.12"
  }
 },
 "nbformat": 4,
 "nbformat_minor": 5
}
